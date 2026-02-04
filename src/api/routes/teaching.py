"""Teaching API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.models import TeachingRequest, TeachingResponse
from ...domain.teaching.service import TeachingService
from ..dependencies.services import get_teaching_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/teach", response_model=TeachingResponse)
async def ask_question(
    request: TeachingRequest,
    teaching_service: TeachingService = Depends(get_teaching_service),
) -> TeachingResponse:
    """
    Ask a teaching question.

    This endpoint accepts a student's question and returns an educational response
    optimized for their grade level and subject.

    The service:
    - Checks rate limits
    - Uses caching for repeated questions
    - Selects appropriate LLM model
    - Generates pedagogically optimized responses
    - Tracks usage and costs

    Args:
        request: Teaching request with question and context
        teaching_service: Injected teaching service

    Returns:
        Teaching response with answer and metadata

    Raises:
        HTTPException: If request fails
    """
    try:
        logger.info(f"Received teaching request for student: {request.student_id}")
        response = await teaching_service.ask_question(request)
        logger.info(
            f"Successfully generated response for student: {request.student_id}"
        )
        return response
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to generate response: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}",
        )


@router.get("/history/{student_id}")
async def get_history(
    student_id: str,
    limit: int = 10,
    teaching_service: TeachingService = Depends(get_teaching_service),
):
    """
    Get conversation history for a student.

    Args:
        student_id: Student identifier
        limit: Maximum number of conversations to retrieve
        teaching_service: Injected teaching service

    Returns:
        List of conversation history
    """
    try:
        logger.info(f"Retrieving history for student: {student_id}, limit: {limit}")
        history = await teaching_service.database.get_conversation_history(
            student_id=student_id, limit=limit
        )
        return {
            "student_id": student_id,
            "conversations": history,
            "count": len(history),
        }
    except Exception as e:
        logger.error(f"Failed to retrieve history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve history: {str(e)}",
        )


@router.get("/usage/{student_id}")
async def get_usage(
    student_id: str, teaching_service: TeachingService = Depends(get_teaching_service)
):
    """
    Get usage metrics for a student.

    Args:
        student_id: Student identifier
        teaching_service: Injected teaching service

    Returns:
        Usage summary with costs and token counts
    """
    try:
        logger.info(f"Retrieving usage for student: {student_id}")
        usage = await teaching_service.database.get_usage_summary(student_id=student_id)
        return usage
    except Exception as e:
        logger.error(f"Failed to retrieve usage: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage: {str(e)}",
        )
