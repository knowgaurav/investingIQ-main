"""Chat API endpoints for InvestingIQ."""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.database import get_db, ChatConversation, ChatMessage
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ChatMessageResponse,
)
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message",
    description="Send a message to the AI assistant and receive a response with RAG-enhanced context."
)
async def send_chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Send a chat message and get an AI response.
    
    The response is enhanced with RAG (Retrieval-Augmented Generation) context
    from relevant financial documents and analysis reports for the specified ticker.
    
    Args:
        request: ChatRequest with message, ticker, and optional conversation_id
        db: Database session
        
    Returns:
        ChatResponse with AI response, sources, and conversation_id
    """
    try:
        llm_service = get_llm_service()
        rag_service = get_rag_service()
        
        ticker = request.ticker.upper()
        
        # Get or create conversation
        if request.conversation_id:
            conversation = db.query(ChatConversation).filter(
                ChatConversation.id == request.conversation_id
            ).first()
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {request.conversation_id} not found"
                )
        else:
            # Create new conversation
            conversation = ChatConversation(ticker=ticker)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # Store user message
        user_message = ChatMessage(
            conversation_id=conversation.id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        db.commit()
        
        # Build context using RAG
        context, sources = rag_service.build_context_string(
            db=db,
            query=request.message,
            ticker=ticker
        )
        
        # Get conversation history for context
        history_messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation.id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        # Build conversation context (last 10 messages for context window)
        conversation_context = ""
        recent_messages = history_messages[-10:] if len(history_messages) > 10 else history_messages
        if len(recent_messages) > 1:  # More than just the current message
            conversation_context = "\n\n## Conversation History\n"
            for msg in recent_messages[:-1]:  # Exclude current message
                role_label = "User" if msg.role == "user" else "Assistant"
                conversation_context += f"{role_label}: {msg.content}\n"
        
        # Combine all context
        full_context = f"Stock Ticker: {ticker}\n"
        if context:
            full_context += f"\n{context}"
        if conversation_context:
            full_context += conversation_context
        
        # Generate AI response
        ai_response = llm_service.chat(
            query=request.message,
            context=full_context
        )
        
        # Store assistant message
        assistant_message = ChatMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_response,
            sources=sources if sources else None
        )
        db.add(assistant_message)
        db.commit()
        
        return ChatResponse(
            response=ai_response,
            sources=sources,
            conversation_id=conversation.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.get(
    "/chat/conversations/{conversation_id}",
    response_model=List[ChatMessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Get conversation history",
    description="Retrieve all messages in a conversation by its ID."
)
async def get_conversation_history(
    conversation_id: UUID,
    db: Session = Depends(get_db)
) -> List[ChatMessageResponse]:
    """
    Get the message history for a conversation.
    
    Args:
        conversation_id: UUID of the conversation
        db: Database session
        
    Returns:
        List of ChatMessageResponse objects ordered by timestamp
    """
    try:
        # Verify conversation exists
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Get all messages in the conversation
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return [
            ChatMessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                sources=msg.sources,
                timestamp=msg.created_at
            )
            for msg in messages
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching conversation history: {str(e)}"
        )
