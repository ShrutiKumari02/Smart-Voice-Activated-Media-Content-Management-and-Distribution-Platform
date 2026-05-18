"""
Database models and initialization using SQLAlchemy + SQLite
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "media_analytics.db")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


class MediaFile(Base):
    __tablename__ = "media_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255))
    file_type = Column(String(50))          # image / video / audio / document
    file_size = Column(Float)               # in KB
    category = Column(String(100), default="General")
    tags = Column(Text, default="")
    description = Column(Text, default="")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)
    downloads = Column(Integer, default=0)
    duration = Column(Float, default=0)     # seconds (for audio/video)
    status = Column(String(50), default="active")   # active / scheduled / archived


class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer)
    task_name = Column(String(255))
    scheduled_time = Column(DateTime)
    action = Column(String(100))            # publish / archive / delete / notify
    status = Column(String(50), default="pending")   # pending / done / failed
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, default="")


class VoiceCommand(Base):
    __tablename__ = "voice_commands"
    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text)
    detected_intent = Column(String(100))
    language = Column(String(50), default="en")
    confidence = Column(Float, default=0.0)
    executed_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    response_text = Column(Text, default="")


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100))        # upload / view / download / voice_command / schedule
    media_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, default="")
    user_agent = Column(String(500), default="")


def init_db():
    Base.metadata.create_all(bind=engine)
    _seed_demo_data()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _seed_demo_data():
    """Seed realistic demo data for presentation."""
    db = SessionLocal()
    try:
        if db.query(MediaFile).count() > 0:
            return  # already seeded

        from datetime import timedelta
        import random

        categories = ["Marketing", "Education", "Entertainment", "News", "Sports"]
        file_types = ["video", "image", "audio", "document"]
        media_names = [
            ("promo_video_q1.mp4", "video", 14200, "Marketing", 120),
            ("tutorial_python.mp4", "video", 8900, "Education", 1800),
            ("podcast_ep12.mp3", "audio", 3400, "Entertainment", 3600),
            ("brand_logo.png", "image", 120, "Marketing", 0),
            ("news_report_may.mp4", "video", 22000, "News", 600),
            ("sports_highlight.mp4", "video", 18500, "Sports", 300),
            ("infographic_ai.png", "image", 450, "Education", 0),
            ("webinar_recording.mp4", "video", 55000, "Education", 5400),
            ("jingle_30sec.mp3", "audio", 1200, "Marketing", 30),
            ("project_report.pdf", "document", 980, "Education", 0),
            ("interview_ceo.mp4", "video", 32000, "News", 2400),
            ("thumbnail_set.png", "image", 230, "Marketing", 0),
            ("documentary_clip.mp4", "video", 41000, "Entertainment", 1200),
            ("lecture_ml.mp4", "video", 71000, "Education", 7200),
            ("ambient_music.mp3", "audio", 2800, "Entertainment", 2400),
        ]

        now = datetime.utcnow()
        for name, ftype, size, cat, dur in media_names:
            days_ago = random.randint(1, 90)
            mf = MediaFile(
                filename=name, original_name=name, file_type=ftype,
                file_size=size, category=cat, duration=dur,
                views=random.randint(50, 5000),
                downloads=random.randint(5, 500),
                uploaded_at=now - timedelta(days=days_ago),
                tags=f"{cat.lower()},{ftype}",
                description=f"Demo {ftype} file for {cat} category.",
                status="active"
            )
            db.add(mf)

        # Scheduled tasks
        task_actions = ["publish", "archive", "notify"]
        for i in range(6):
            st = ScheduledTask(
                media_id=random.randint(1, 15),
                task_name=f"Scheduled Task {i+1}",
                scheduled_time=now + timedelta(days=random.randint(1, 14)),
                action=random.choice(task_actions),
                status=random.choice(["pending", "done"]),
                notes="Auto-generated demo task."
            )
            db.add(st)

        # Voice commands log
        sample_commands = [
            ("upload video", "upload", "en", 0.97),
            ("show analytics", "analytics", "en", 0.95),
            ("schedule task", "schedule", "en", 0.92),
            ("search videos", "search", "en", 0.88),
            ("download report", "download", "en", 0.91),
            ("सामग्री अपलोड करें", "upload", "hi", 0.85),
        ]
        for raw, intent, lang, conf in sample_commands:
            vc = VoiceCommand(
                raw_text=raw, detected_intent=intent,
                language=lang, confidence=conf, success=True,
                response_text=f"Executed: {intent}"
            )
            db.add(vc)

        # Analytics events
        event_types = ["upload", "view", "download", "voice_command", "schedule"]
        for i in range(60):
            ae = AnalyticsEvent(
                event_type=random.choice(event_types),
                media_id=random.randint(1, 15),
                timestamp=now - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23)
                ),
                details="demo event"
            )
            db.add(ae)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Seeding error: {e}")
    finally:
        db.close()
