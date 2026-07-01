from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.chat import Conversation, Message
from typing import List

class PostgresMemoryStore:
    """
    Manages long-term archival of conversations in the relational database.
    This provides persistence for the User Dashboard history.
    """
    
    @staticmethod
    async def create_conversation(db: AsyncSession, user_id: str, title: str = "New Conversation") -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        return conv

    @staticmethod
    async def add_message(db: AsyncSession, conversation_id: str, role: str, content: str, tool_calls: dict = None, token_count: int = 0) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            token_count=token_count
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def get_conversation_history(db: AsyncSession, conversation_id: str) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return result.scalars().all()
