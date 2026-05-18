"""
AI Voice Analytics MCA — Flask REST API
Entry point for all backend operations.
"""
import os
import uuid
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Local modules
from database import init_db, SessionLocal, MediaFile, VoiceCommand, AnalyticsEvent
from voice_processor import process_voice_command, get_available_commands
from analytics import (
    get_dashboard_summary, get_media_by_type, get_media_by_category,
    get_uploads_over_time, get_views_vs_downloads, get_voice_command_stats,
    get_activity_heatmap, get_top_media, get_scheduled_tasks_summary,
    get_storage_breakdown,
)
from scheduler import start_scheduler, stop_scheduler, add_scheduled_task, get_all_tasks, cancel_task

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "mp4", "avi", "mov", "mkv",          # video
    "mp3", "wav", "ogg", "m4a",          # audio
    "png", "jpg", "jpeg", "gif", "webp", # image
    "pdf", "docx", "pptx", "xlsx",       # document
}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ── App Init ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024   # 500 MB

init_db()
start_scheduler()


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _file_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext in {"mp4", "avi", "mov", "mkv"}:          return "video"
    if ext in {"mp3", "wav", "ogg", "m4a"}:          return "audio"
    if ext in {"png", "jpg", "jpeg", "gif", "webp"}: return "image"
    return "document"


def _log_event(event_type: str, media_id=None, details=""):
    db = SessionLocal()
    try:
        db.add(AnalyticsEvent(
            event_type=event_type, media_id=media_id, details=details,
            user_agent=request.headers.get("User-Agent", "")[:500],
        ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _ok(data=None, message="OK"):
    return jsonify({"status": "success", "message": message, "data": data or {}}), 200


def _err(message="Error", code=400):
    return jsonify({"status": "error", "message": message, "data": {}}), code


# ─────────────────────────────────────────────────────────────────────────────
#  Health Check
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return _ok({"server": "running", "time": datetime.utcnow().isoformat()}, "Server healthy")


# ─────────────────────────────────────────────────────────────────────────────
#  Voice Command Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/voice/process", methods=["POST"])
def voice_process():
    body = request.get_json(silent=True) or {}
    text = body.get("text", "").strip()
    if not text:
        return _err("No text provided.", 400)

    result = process_voice_command(text)

    # Persist to DB
    db = SessionLocal()
    try:
        vc = VoiceCommand(
            raw_text=result["raw_text"],
            detected_intent=result["detected_intent"],
            language=result["language"],
            confidence=result["confidence"],
            success=result["success"],
            response_text=result["response_text"],
        )
        db.add(vc)
        db.commit()
        _log_event("voice_command", details=f"Intent: {result['detected_intent']}")
    except Exception:
        db.rollback()
    finally:
        db.close()

    return _ok(result, result["response_text"])


@app.route("/api/voice/commands", methods=["GET"])
def voice_commands_list():
    return _ok(get_available_commands(), "Available voice commands")


@app.route("/api/voice/history", methods=["GET"])
def voice_history():
    db = SessionLocal()
    try:
        limit = int(request.args.get("limit", 20))
        records = (db.query(VoiceCommand)
                   .order_by(VoiceCommand.executed_at.desc())
                   .limit(limit).all())
        data = [
            {
                "id":             r.id,
                "text":           r.raw_text,
                "intent":         r.detected_intent,
                "language":       r.language,
                "confidence":     r.confidence,
                "success":        r.success,
                "response":       r.response_text,
                "executed_at":    r.executed_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for r in records
        ]
        return _ok(data, "Voice command history")
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
#  Media Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/media/upload", methods=["POST"])
def media_upload():
    if "file" not in request.files:
        return _err("No file in request.", 400)

    file = request.files["file"]
    if file.filename == "":
        return _err("Empty filename.", 400)
    if not _allowed(file.filename):
        return _err(f"File type not allowed.", 415)

    original_name = secure_filename(file.filename)
    unique_name   = f"{uuid.uuid4().hex}_{original_name}"
    save_path     = os.path.join(UPLOAD_DIR, unique_name)
    file.save(save_path)

    size_kb   = os.path.getsize(save_path) / 1024
    ftype     = _file_type(original_name)
    category  = request.form.get("category", "General")
    tags      = request.form.get("tags", "")
    desc      = request.form.get("description", "")

    db = SessionLocal()
    try:
        mf = MediaFile(
            filename=unique_name, original_name=original_name,
            file_type=ftype, file_size=round(size_kb, 2),
            category=category, tags=tags, description=desc,
        )
        db.add(mf)
        db.commit()
        db.refresh(mf)
        _log_event("upload", media_id=mf.id, details=f"Uploaded {original_name}")
        return _ok({
            "id": mf.id, "filename": original_name,
            "type": ftype, "size_kb": round(size_kb, 2),
        }, "File uploaded successfully.")
    except Exception as e:
        db.rollback()
        return _err(str(e), 500)
    finally:
        db.close()


@app.route("/api/media/list", methods=["GET"])
def media_list():
    db = SessionLocal()
    try:
        q        = db.query(MediaFile)
        ftype    = request.args.get("type")
        category = request.args.get("category")
        search   = request.args.get("search")
        status   = request.args.get("status", "active")

        if ftype:    q = q.filter(MediaFile.file_type == ftype)
        if category: q = q.filter(MediaFile.category  == category)
        if status:   q = q.filter(MediaFile.status     == status)
        if search:   q = q.filter(MediaFile.original_name.ilike(f"%{search}%"))

        files = q.order_by(MediaFile.uploaded_at.desc()).all()
        data  = [
            {
                "id":           f.id,
                "name":         f.original_name,
                "type":         f.file_type,
                "category":     f.category,
                "size_kb":      f.file_size,
                "views":        f.views,
                "downloads":    f.downloads,
                "tags":         f.tags,
                "description":  f.description,
                "uploaded_at":  f.uploaded_at.strftime("%Y-%m-%d %H:%M"),
                "status":       f.status,
            }
            for f in files
        ]
        return _ok(data, f"{len(data)} files found.")
    finally:
        db.close()


@app.route("/api/media/<int:media_id>", methods=["GET"])
def media_detail(media_id):
    db = SessionLocal()
    try:
        mf = db.query(MediaFile).filter_by(id=media_id).first()
        if not mf:
            return _err("File not found.", 404)
        mf.views += 1
        db.commit()
        _log_event("view", media_id=media_id)
        return _ok({
            "id": mf.id, "name": mf.original_name, "type": mf.file_type,
            "category": mf.category, "size_kb": mf.file_size,
            "views": mf.views, "downloads": mf.downloads,
            "tags": mf.tags, "description": mf.description,
            "uploaded_at": mf.uploaded_at.strftime("%Y-%m-%d %H:%M"),
            "status": mf.status,
        })
    finally:
        db.close()


@app.route("/api/media/<int:media_id>", methods=["PUT"])
def media_update(media_id):
    db = SessionLocal()
    try:
        mf = db.query(MediaFile).filter_by(id=media_id).first()
        if not mf:
            return _err("File not found.", 404)
        body = request.get_json(silent=True) or {}
        for field in ["category", "tags", "description", "status"]:
            if field in body:
                setattr(mf, field, body[field])
        db.commit()
        return _ok({"id": mf.id}, "File updated.")
    except Exception as e:
        db.rollback()
        return _err(str(e), 500)
    finally:
        db.close()


@app.route("/api/media/<int:media_id>", methods=["DELETE"])
def media_delete(media_id):
    db = SessionLocal()
    try:
        mf = db.query(MediaFile).filter_by(id=media_id).first()
        if not mf:
            return _err("File not found.", 404)
        # Soft delete
        mf.status = "deleted"
        db.commit()
        _log_event("delete", media_id=media_id)
        return _ok({}, "File deleted.")
    except Exception as e:
        db.rollback()
        return _err(str(e), 500)
    finally:
        db.close()


@app.route("/api/media/file/<filename>")
def serve_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ─────────────────────────────────────────────────────────────────────────────
#  Analytics Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/analytics/summary", methods=["GET"])
def analytics_summary():
    return _ok(get_dashboard_summary(), "Dashboard summary")


@app.route("/api/analytics/media-by-type", methods=["GET"])
def analytics_media_type():
    return _ok(get_media_by_type(), "Media by type")


@app.route("/api/analytics/media-by-category", methods=["GET"])
def analytics_media_category():
    return _ok(get_media_by_category(), "Media by category")


@app.route("/api/analytics/uploads-over-time", methods=["GET"])
def analytics_uploads():
    days = int(request.args.get("days", 30))
    return _ok(get_uploads_over_time(days), f"Uploads over {days} days")


@app.route("/api/analytics/views-vs-downloads", methods=["GET"])
def analytics_views():
    return _ok(get_views_vs_downloads(), "Views vs Downloads")


@app.route("/api/analytics/voice-stats", methods=["GET"])
def analytics_voice():
    return _ok(get_voice_command_stats(), "Voice command stats")


@app.route("/api/analytics/activity", methods=["GET"])
def analytics_activity():
    days = int(request.args.get("days", 30))
    return _ok(get_activity_heatmap(days), "Activity data")


@app.route("/api/analytics/top-media", methods=["GET"])
def analytics_top():
    limit = int(request.args.get("limit", 5))
    return _ok(get_top_media(limit), "Top media")


@app.route("/api/analytics/storage", methods=["GET"])
def analytics_storage():
    return _ok(get_storage_breakdown(), "Storage breakdown")


# ─────────────────────────────────────────────────────────────────────────────
#  Scheduler Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/schedule/tasks", methods=["GET"])
def schedule_list():
    return _ok(get_all_tasks(), "Scheduled tasks")


@app.route("/api/schedule/add", methods=["POST"])
def schedule_add():
    body = request.get_json(silent=True) or {}
    required = ["task_name", "action", "scheduled_time"]
    for field in required:
        if field not in body:
            return _err(f"Missing field: {field}", 400)
    try:
        dt = datetime.strptime(body["scheduled_time"], "%Y-%m-%dT%H:%M")
    except ValueError:
        return _err("Invalid date format. Use YYYY-MM-DDTHH:MM", 400)

    result = add_scheduled_task(
        media_id=body.get("media_id", 0),
        task_name=body["task_name"],
        action=body["action"],
        scheduled_time=dt,
        notes=body.get("notes", ""),
    )
    if result["success"]:
        return _ok(result, result["message"])
    return _err(result["message"], 500)


@app.route("/api/schedule/cancel/<int:task_id>", methods=["DELETE"])
def schedule_cancel(task_id):
    result = cancel_task(task_id)
    if result["success"]:
        return _ok({}, result["message"])
    return _err(result["message"], 404)


# ─────────────────────────────────────────────────────────────────────────────
#  Serve Frontend (SPA fallback)
# ─────────────────────────────────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Starting AI Voice Analytics server on http://localhost:5000")
    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    finally:
        stop_scheduler()
