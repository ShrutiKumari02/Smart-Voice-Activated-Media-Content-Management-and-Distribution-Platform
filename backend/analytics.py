"""
Analytics Engine
Computes all metrics and chart data from the SQLite database.
"""
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func
from database import SessionLocal, MediaFile, ScheduledTask, VoiceCommand, AnalyticsEvent


def get_dashboard_summary() -> dict:
    db = SessionLocal()
    try:
        total_files    = db.query(MediaFile).count()
        total_views    = db.query(func.sum(MediaFile.views)).scalar() or 0
        total_downloads = db.query(func.sum(MediaFile.downloads)).scalar() or 0
        total_size_kb  = db.query(func.sum(MediaFile.file_size)).scalar() or 0
        pending_tasks  = db.query(ScheduledTask).filter_by(status="pending").count()
        voice_cmds     = db.query(VoiceCommand).count()
        active_files   = db.query(MediaFile).filter_by(status="active").count()

        # Growth vs last 30 days
        cutoff = datetime.utcnow() - timedelta(days=30)
        new_files = db.query(MediaFile).filter(MediaFile.uploaded_at >= cutoff).count()

        return {
            "total_files":      total_files,
            "active_files":     active_files,
            "total_views":      int(total_views),
            "total_downloads":  int(total_downloads),
            "total_size_mb":    round(total_size_kb / 1024, 2),
            "pending_tasks":    pending_tasks,
            "voice_commands":   voice_cmds,
            "new_files_30d":    new_files,
        }
    finally:
        db.close()


def get_media_by_type() -> dict:
    """Pie/doughnut chart: count by file_type."""
    db = SessionLocal()
    try:
        rows = (db.query(MediaFile.file_type, func.count(MediaFile.id))
                .group_by(MediaFile.file_type).all())
        labels = [r[0].capitalize() for r in rows]
        values = [r[1] for r in rows]
        return {"labels": labels, "values": values}
    finally:
        db.close()


def get_media_by_category() -> dict:
    """Bar chart: count by category."""
    db = SessionLocal()
    try:
        rows = (db.query(MediaFile.category, func.count(MediaFile.id))
                .group_by(MediaFile.category).all())
        labels = [r[0] for r in rows]
        values = [r[1] for r in rows]
        return {"labels": labels, "values": values}
    finally:
        db.close()


def get_uploads_over_time(days: int = 30) -> dict:
    """Line chart: daily uploads over last N days."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        files  = (db.query(MediaFile)
                  .filter(MediaFile.uploaded_at >= cutoff)
                  .all())

        daily = defaultdict(int)
        for f in files:
            day = f.uploaded_at.strftime("%Y-%m-%d")
            daily[day] += 1

        # Fill gaps
        labels, values = [], []
        for i in range(days):
            day = (datetime.utcnow() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
            labels.append(day)
            values.append(daily.get(day, 0))

        return {"labels": labels, "values": values}
    finally:
        db.close()


def get_views_vs_downloads() -> dict:
    """Bar chart: top 10 files by views + downloads."""
    db = SessionLocal()
    try:
        files = (db.query(MediaFile)
                 .order_by(MediaFile.views.desc())
                 .limit(10).all())
        labels    = [f.original_name[:20] for f in files]
        views     = [f.views for f in files]
        downloads = [f.downloads for f in files]
        return {"labels": labels, "views": views, "downloads": downloads}
    finally:
        db.close()


def get_voice_command_stats() -> dict:
    """Voice intent distribution + language breakdown."""
    db = SessionLocal()
    try:
        intent_rows = (db.query(VoiceCommand.detected_intent, func.count(VoiceCommand.id))
                       .group_by(VoiceCommand.detected_intent).all())
        lang_rows   = (db.query(VoiceCommand.language, func.count(VoiceCommand.id))
                       .group_by(VoiceCommand.language).all())

        avg_conf = db.query(func.avg(VoiceCommand.confidence)).scalar() or 0

        return {
            "intents": {
                "labels": [r[0] for r in intent_rows],
                "values": [r[1] for r in intent_rows],
            },
            "languages": {
                "labels": [r[0].upper() for r in lang_rows],
                "values": [r[1] for r in lang_rows],
            },
            "avg_confidence": round(float(avg_conf) * 100, 1),
            "total_commands": db.query(VoiceCommand).count(),
            "success_rate":   _voice_success_rate(db),
        }
    finally:
        db.close()


def get_activity_heatmap(days: int = 30) -> dict:
    """Events per day for activity heatmap / area chart."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        events  = db.query(AnalyticsEvent).filter(AnalyticsEvent.timestamp >= cutoff).all()

        by_day = defaultdict(lambda: defaultdict(int))
        for e in events:
            day = e.timestamp.strftime("%Y-%m-%d")
            by_day[day][e.event_type] += 1

        labels      = []
        uploads_arr = []
        views_arr   = []
        voice_arr   = []

        for i in range(days):
            day = (datetime.utcnow() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
            labels.append(day)
            uploads_arr.append(by_day[day].get("upload", 0))
            views_arr.append(by_day[day].get("view", 0))
            voice_arr.append(by_day[day].get("voice_command", 0))

        return {
            "labels":   labels,
            "uploads":  uploads_arr,
            "views":    views_arr,
            "voice":    voice_arr,
        }
    finally:
        db.close()


def get_top_media(limit: int = 5) -> list:
    db = SessionLocal()
    try:
        files = (db.query(MediaFile)
                 .order_by((MediaFile.views + MediaFile.downloads).desc())
                 .limit(limit).all())
        return [
            {
                "id":         f.id,
                "name":       f.original_name,
                "type":       f.file_type,
                "category":   f.category,
                "views":      f.views,
                "downloads":  f.downloads,
                "size_kb":    f.file_size,
                "uploaded_at": f.uploaded_at.strftime("%Y-%m-%d"),
            }
            for f in files
        ]
    finally:
        db.close()


def get_scheduled_tasks_summary() -> dict:
    db = SessionLocal()
    try:
        total   = db.query(ScheduledTask).count()
        pending = db.query(ScheduledTask).filter_by(status="pending").count()
        done    = db.query(ScheduledTask).filter_by(status="done").count()
        upcoming = (db.query(ScheduledTask)
                    .filter(ScheduledTask.status == "pending",
                            ScheduledTask.scheduled_time >= datetime.utcnow())
                    .order_by(ScheduledTask.scheduled_time)
                    .limit(5).all())
        return {
            "total":   total,
            "pending": pending,
            "done":    done,
            "upcoming": [
                {
                    "id":             t.id,
                    "task_name":      t.task_name,
                    "action":         t.action,
                    "scheduled_time": t.scheduled_time.strftime("%Y-%m-%d %H:%M"),
                    "status":         t.status,
                }
                for t in upcoming
            ],
        }
    finally:
        db.close()


def get_storage_breakdown() -> dict:
    """Storage used per file type (MB)."""
    db = SessionLocal()
    try:
        rows = (db.query(MediaFile.file_type, func.sum(MediaFile.file_size))
                .group_by(MediaFile.file_type).all())
        labels = [r[0].capitalize() for r in rows]
        values = [round((r[1] or 0) / 1024, 2) for r in rows]
        return {"labels": labels, "values": values}
    finally:
        db.close()


# ── helpers ──────────────────────────────────
def _voice_success_rate(db) -> float:
    total   = db.query(VoiceCommand).count()
    success = db.query(VoiceCommand).filter_by(success=True).count()
    if total == 0:
        return 100.0
    return round(success / total * 100, 1)
