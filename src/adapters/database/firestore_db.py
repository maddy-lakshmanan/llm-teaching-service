"""Firestore database implementation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from google.cloud import firestore
from ...core.ports import AbstractDatabaseService
from ...core.models import TeachingRequest, TeachingResponse, UsageMetrics


class FirestoreService(AbstractDatabaseService):
    """Firestore-based database service for persistent storage."""

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Firestore service.

        Args:
            project_id: GCP project ID (uses default if None)
        """
        self.db = firestore.AsyncClient(project=project_id)
        self.conversations_collection = "conversations"
        self.usage_metrics_collection = "usage_metrics"

    async def save_conversation(
        self, student_id: str, request: TeachingRequest, response: TeachingResponse
    ) -> str:
        """
        Save conversation to Firestore.

        Args:
            student_id: Student identifier
            request: Teaching request
            response: Teaching response

        Returns:
            Conversation document ID
        """
        conversation_data = {
            "student_id": student_id,
            "question": request.question,
            "answer": response.answer,
            "subject": request.subject.value,
            "grade_level": request.grade_level.value,
            "model_used": response.model_used,
            "tokens_used": response.tokens_used,
            "cost": response.estimated_cost,
            "confidence": response.confidence,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Add optional fields
        if request.conversation_history:
            conversation_data["conversation_history"] = [
                msg.model_dump() for msg in request.conversation_history
            ]

        if response.follow_up_suggestions:
            conversation_data["follow_up_suggestions"] = response.follow_up_suggestions

        # Save to Firestore
        doc_ref = self.db.collection(self.conversations_collection).document()
        await doc_ref.set(conversation_data)

        return doc_ref.id

    async def get_conversation_history(
        self, student_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve student's conversation history.

        Args:
            student_id: Student identifier
            limit: Maximum number of conversations to retrieve

        Returns:
            List of conversation documents
        """
        query = (
            self.db.collection(self.conversations_collection)
            .where("student_id", "==", student_id)
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )

        conversations = []
        async for doc in query.stream():
            conversation = doc.to_dict()
            conversation["id"] = doc.id
            conversations.append(conversation)

        return conversations

    async def save_usage_metrics(self, metrics: UsageMetrics) -> None:
        """
        Save token usage and cost metrics.

        Args:
            metrics: Usage metrics to save
        """
        metrics_data = {
            "user_id": metrics.user_id,
            "model": metrics.model,
            "tokens_used": metrics.tokens_used,
            "cost": metrics.cost,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "created_at": metrics.timestamp.isoformat(),
        }

        if metrics.request_id:
            metrics_data["request_id"] = metrics.request_id

        # Save to Firestore
        await self.db.collection(self.usage_metrics_collection).add(metrics_data)

    async def get_usage_summary(
        self,
        student_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get usage summary with aggregated metrics.

        Args:
            student_id: Filter by student (optional)
            start_date: Start date for range (optional)
            end_date: End date for range (optional)

        Returns:
            Usage summary with totals and breakdowns
        """
        # Build query
        query = self.db.collection(self.usage_metrics_collection)

        if student_id:
            query = query.where("user_id", "==", student_id)

        # Note: For production, consider using BigQuery for complex aggregations
        # This is a simplified version that fetches and aggregates in memory

        total_tokens = 0
        total_cost = 0.0
        request_count = 0
        model_breakdown = {}

        async for doc in query.stream():
            metrics = doc.to_dict()

            # Apply date filters
            if start_date or end_date:
                created_at = metrics.get("created_at", "")
                if start_date and created_at < start_date:
                    continue
                if end_date and created_at > end_date:
                    continue

            # Aggregate
            total_tokens += metrics.get("tokens_used", 0)
            total_cost += metrics.get("cost", 0.0)
            request_count += 1

            # Model breakdown
            model = metrics.get("model", "unknown")
            if model not in model_breakdown:
                model_breakdown[model] = {"tokens": 0, "cost": 0.0, "requests": 0}
            model_breakdown[model]["tokens"] += metrics.get("tokens_used", 0)
            model_breakdown[model]["cost"] += metrics.get("cost", 0.0)
            model_breakdown[model]["requests"] += 1

        return {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "request_count": request_count,
            "average_tokens_per_request": total_tokens / request_count
            if request_count > 0
            else 0,
            "average_cost_per_request": total_cost / request_count
            if request_count > 0
            else 0.0,
            "model_breakdown": model_breakdown,
            "filters": {
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        }

    async def close(self):
        """Close Firestore client."""
        # AsyncClient doesn't require explicit closing in recent versions
        pass


class InMemoryDatabaseService(AbstractDatabaseService):
    """In-memory database for testing/development."""

    def __init__(self):
        """Initialize in-memory storage."""
        self.conversations: List[Dict[str, Any]] = []
        self.usage_metrics: List[Dict[str, Any]] = []

    async def save_conversation(
        self, student_id: str, request: TeachingRequest, response: TeachingResponse
    ) -> str:
        """Save conversation to memory."""
        conversation_id = f"conv_{len(self.conversations)}"
        conversation = {
            "id": conversation_id,
            "student_id": student_id,
            "question": request.question,
            "answer": response.answer,
            "subject": request.subject.value,
            "grade_level": request.grade_level.value,
            "model_used": response.model_used,
            "tokens_used": response.tokens_used,
            "cost": response.estimated_cost,
            "timestamp": datetime.utcnow(),
        }
        self.conversations.append(conversation)
        return conversation_id

    async def get_conversation_history(
        self, student_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation history."""
        student_conversations = [
            c for c in self.conversations if c["student_id"] == student_id
        ]
        # Sort by timestamp descending
        student_conversations.sort(key=lambda x: x["timestamp"], reverse=True)
        return student_conversations[:limit]

    async def save_usage_metrics(self, metrics: UsageMetrics) -> None:
        """Save usage metrics."""
        self.usage_metrics.append(
            {
                "user_id": metrics.user_id,
                "model": metrics.model,
                "tokens_used": metrics.tokens_used,
                "cost": metrics.cost,
                "timestamp": metrics.timestamp,
            }
        )

    async def get_usage_summary(
        self,
        student_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get usage summary."""
        filtered_metrics = self.usage_metrics

        if student_id:
            filtered_metrics = [
                m for m in filtered_metrics if m["user_id"] == student_id
            ]

        total_tokens = sum(m["tokens_used"] for m in filtered_metrics)
        total_cost = sum(m["cost"] for m in filtered_metrics)
        request_count = len(filtered_metrics)

        return {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "request_count": request_count,
            "average_tokens_per_request": total_tokens / request_count
            if request_count > 0
            else 0,
            "average_cost_per_request": total_cost / request_count
            if request_count > 0
            else 0.0,
        }
