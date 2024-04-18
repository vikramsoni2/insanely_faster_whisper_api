from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.engine import URL
from sqlalchemy import event, text
from config import Config

Base = declarative_base()

class LogEntry(Base):
    __tablename__ = 'logs_whisper'
    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, index=True)
    app_name = Column(String)
    datetime = Column(DateTime(timezone=True), server_default=func.now())
    transcribed_text = Column(String)

DATABASE_URL = URL.create(
                drivername="postgresql+asyncpg",
                username=Config.DB_USER,
                password=Config.DB_PASSWORD,
                host=Config.DB_HOST,
                database=Config.DB_DATABASE,
                port=5432
            )

async_engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession)

async def init_db():
    async with async_engine.begin() as conn:
        # await conn.execute(text(f"SET search_path TO {Config.DB_SCHEMA}")) # use public schema
        await conn.run_sync(Base.metadata.create_all)
        

async def async_log_transcription(user: str, app_name: str, transcribed_text: str):
    async with AsyncSessionLocal() as session:
        new_log = LogEntry(user=user, app_name=app_name, transcribed_text=transcribed_text)
        session.add(new_log)
        await session.commit()
