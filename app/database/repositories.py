from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.database.models import (
    User,
    Document,
    DocumentChunk,
    Conversation,
    Message,
    AgentSession,
    Report,
    AnalysisResult,
    ForecastResult,
)
from app.utils.security import hash_password

class UserRepository:
    @staticmethod
    def normalize_full_name(email: str, full_name: Optional[str] = None) -> str:
        if full_name and full_name.strip():
            return full_name.strip()
        local_part = email.split("@", 1)[0].strip()
        cleaned = local_part.replace(".", " ").replace("_", " ").replace("-", " ").strip()
        return cleaned.title() if cleaned else "User"

    @staticmethod
    def create(db: Session, email: str, password: str, full_name: Optional[str] = None, is_admin: bool = False) -> User:
        user = User(
            email=email.lower().strip(),
            hashed_password=hash_password(password),
            full_name=UserRepository.normalize_full_name(email, full_name),
            is_admin=is_admin,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_full_name(db: Session, user_id: str, full_name: str) -> Optional[User]:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            return None
        user.full_name = UserRepository.normalize_full_name(user.email, full_name)
        db.commit()
        db.refresh(user)
        return user


class DocumentRepository:
    @staticmethod
    def create(
        db: Session,
        filename: str,
        file_path: str,
        file_type: str,
        file_size_bytes: int,
        total_pages: int = 1,
        metadata_info: Optional[Dict[str, Any]] = None,
        summary: Optional[str] = None,
    ) -> Document:
        doc = Document(
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            total_pages=total_pages,
            metadata_info=metadata_info or {},
            summary=summary,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def add_chunks(
        db: Session,
        document_id: str,
        chunks: List[Dict[str, Any]],
    ) -> List[DocumentChunk]:
        chunk_objs = []
        for i, chunk in enumerate(chunks):
            obj = DocumentChunk(
                document_id=document_id,
                chunk_index=chunk.get("chunk_index", i),
                content=chunk["content"],
                page_number=chunk.get("page_number", 1),
                section=chunk.get("section"),
                modality=chunk.get("modality", "text"),
                token_count=chunk.get("token_count", len(chunk["content"].split())),
                metadata_info=chunk.get("metadata", {}),
            )
            chunk_objs.append(obj)
            db.add(obj)
        
        # update document chunk count
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.chunk_count = len(chunks)
            doc.status = "processed"

        db.commit()
        return chunk_objs

    @staticmethod
    def get_all(db: Session, limit: int = 100, offset: int = 0) -> List[Document]:
        return db.query(Document).order_by(Document.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, doc_id: str) -> Optional[Document]:
        return db.query(Document).filter(Document.id == doc_id).first()

    @staticmethod
    def delete(db: Session, doc_id: str) -> bool:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            db.delete(doc)
            db.commit()
            return True
        return False


class ConversationRepository:
    @staticmethod
    def get_or_create(db: Session, session_id: str, user_id: Optional[str] = None, title: Optional[str] = None) -> Conversation:
        conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
        if not conv:
            conv = Conversation(
                session_id=session_id,
                user_id=user_id,
                title=title or "New Conversation",
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)
        return conv

    @staticmethod
    def add_message(
        db: Session,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        agent_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Message:
        conv = ConversationRepository.get_or_create(db, session_id)
        msg = Message(
            conversation_id=conv.id,
            role=role,
            content=content,
            sources=sources or [],
            agent_name=agent_name,
            model=model,
            tokens_used=len(content.split()),
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def get_history(db: Session, session_id: str, limit: int = 50) -> List[Message]:
        conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
        if not conv:
            return []
        return db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.asc()).limit(limit).all()


class AnalyticsRepository:
    @staticmethod
    def save_analysis(
        db: Session,
        filename: str,
        analysis_type: str,
        summary: str,
        raw_results: Dict[str, Any],
        insights: List[str],
    ) -> AnalysisResult:
        res = AnalysisResult(
            filename=filename,
            analysis_type=analysis_type,
            summary=summary,
            raw_results=raw_results,
            insights=insights,
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return res

    @staticmethod
    def save_forecast(
        db: Session,
        filename: str,
        date_column: str,
        target_column: str,
        model_name: str,
        horizon_periods: int,
        metrics: Dict[str, Any],
        historical_points: List[Dict[str, Any]],
        forecast_points: List[Dict[str, Any]],
    ) -> ForecastResult:
        res = ForecastResult(
            filename=filename,
            date_column=date_column,
            target_column=target_column,
            model_name=model_name,
            horizon_periods=horizon_periods,
            metrics=metrics,
            historical_points=historical_points,
            forecast_points=forecast_points,
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return res

    @staticmethod
    def save_report(
        db: Session,
        title: str,
        topic: str,
        summary: str,
        content: str,
        sources: List[Dict[str, Any]],
        format: str = "markdown",
    ) -> Report:
        rep = Report(
            title=title,
            topic=topic,
            summary=summary,
            content=content,
            sources=sources,
            format=format,
        )
        db.add(rep)
        db.commit()
        db.refresh(rep)
        return rep
