"""
Scheduler Module
Uses APScheduler to handle deferred media operations.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from database import SessionLocal, ScheduledTask, MediaFile, AnalyticsEvent
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


def start_scheduler():
    """Start the background scheduler and restore pending jobs."""
    if not scheduler.running:
        scheduler.start()
        _restore_pending_jobs()
        logger.info("APScheduler started.")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)


def add_scheduled_task(media_id: int, task_name: str,
                        action: str, scheduled_time: datetime,
                        notes: str = "") -> dict:
    db = SessionLocal()
    try:
        task = ScheduledTask(
            media_id=media_id,
            task_name=task_name,
            action=action,
            scheduled_time=scheduled_time,
            status="pending",
            notes=notes,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Register with APScheduler (only future tasks)
        if scheduled_time > datetime.utcnow():
            scheduler.add_job(
                _execute_task,
                trigger=DateTrigger(run_date=scheduled_time),
                args=[task.id],
                id=f"task_{task.id}",
                replace_existing=True,
            )

        return {"success": True, "task_id": task.id, "message": f"Task '{task_name}' scheduled."}
    except Exception as e:
        db.rollback()
        logger.error(f"Schedule error: {e}")
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def get_all_tasks() -> list:
    db = SessionLocal()
    try:
        tasks = db.query(ScheduledTask).order_by(ScheduledTask.scheduled_time.desc()).all()
        return [
            {
                "id":             t.id,
                "media_id":       t.media_id,
                "task_name":      t.task_name,
                "action":         t.action,
                "scheduled_time": t.scheduled_time.strftime("%Y-%m-%d %H:%M"),
                "status":         t.status,
                "created_at":     t.created_at.strftime("%Y-%m-%d %H:%M"),
                "notes":          t.notes,
            }
            for t in tasks
        ]
    finally:
        db.close()


def cancel_task(task_id: int) -> dict:
    db = SessionLocal()
    try:
        task = db.query(ScheduledTask).filter_by(id=task_id).first()
        if not task:
            return {"success": False, "message": "Task not found."}
        task.status = "cancelled"
        db.commit()

        job_id = f"task_{task_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        return {"success": True, "message": f"Task {task_id} cancelled."}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


# ── Internal ──────────────────────────────────────
def _execute_task(task_id: int):
    """Runs when scheduled time arrives."""
    db = SessionLocal()
    try:
        task = db.query(ScheduledTask).filter_by(id=task_id).first()
        if not task or task.status != "pending":
            return

        media = db.query(MediaFile).filter_by(id=task.media_id).first()
        if media:
            if task.action == "archive":
                media.status = "archived"
            elif task.action == "delete":
                media.status = "deleted"
            elif task.action == "publish":
                media.status = "active"

        task.status = "done"

        event = AnalyticsEvent(
            event_type="schedule",
            media_id=task.media_id,
            details=f"Task '{task.task_name}' ({task.action}) executed automatically.",
        )
        db.add(event)
        db.commit()
        logger.info(f"Task {task_id} executed: {task.action}")
    except Exception as e:
        db.rollback()
        logger.error(f"Task execution error: {e}")
    finally:
        db.close()


def _restore_pending_jobs():
    """Re-queue any pending tasks that survived a server restart."""
    db = SessionLocal()
    try:
        now   = datetime.utcnow()
        tasks = (db.query(ScheduledTask)
                 .filter(ScheduledTask.status == "pending",
                         ScheduledTask.scheduled_time > now)
                 .all())
        for t in tasks:
            scheduler.add_job(
                _execute_task,
                trigger=DateTrigger(run_date=t.scheduled_time),
                args=[t.id],
                id=f"task_{t.id}",
                replace_existing=True,
            )
        logger.info(f"Restored {len(tasks)} pending scheduled jobs.")
    finally:
        db.close()
