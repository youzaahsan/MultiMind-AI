import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from app.database.connection import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False, index=True)
    file_size_bytes = Column(Integer, nullable=False)
    total_pages = Column(Integer, default=1)
    chunk_count = Column(Integer, default=0)
    status = Column(String(50), default="processed", index=True)  # uploaded, processing, processed, error
    metadata_info = Column(JSON, default=dict)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, default=1)
    section = Column(String(255), nullable=True)
    modality = Column(String(50), default="text")  # text, table, chart, image_caption
    token_count = Column(Integer, default=0)
    metadata_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("idx_doc_chunk_order", "document_id", "chunk_index"),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=list)  # list of {document_id, filename, page, text_snippet}
    agent_name = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    conversation = relationship("Conversation", back_populates="messages")


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    status = Column(String(50), default="active")  # active, completed, failed
    plan = Column(JSON, default=list)
    execution_trace = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    topic = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=list)
    format = Column(String(50), default="markdown")
    created_at = Column(DateTime, default=utc_now)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    analysis_type = Column(String(100), nullable=False)  # statistical, correlation, cluster, anomaly
    summary = Column(Text, nullable=False)
    raw_results = Column(JSON, default=dict)
    insights = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    date_column = Column(String(100), nullable=False)
    target_column = Column(String(100), nullable=False)
    model_name = Column(String(100), nullable=False)
    horizon_periods = Column(Integer, nullable=False)
    metrics = Column(JSON, default=dict)  # MAE, RMSE, MAPE
    historical_points = Column(JSON, default=list)
    forecast_points = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)
