"""Core teaching service with intelligent model routing."""

import time
import hashlib
from datetime import datetime
from typing import Optional, List
from ...core.models import (
    TeachingRequest,
    TeachingResponse,
    UsageMetrics,
    ConversationMessage,
)
from ...core.ports import (
    AbstractCacheService,
    AbstractDatabaseService,
    AbstractRateLimiter,
    AbstractMonitoringService,
)
from ...adapters.llm.factory import LLMProviderFactory


class TeachingService:
    """
    Orchestrates teaching interactions with pluggable LLM providers.

    This service implements the core business logic for educational AI,
    including model selection, caching, rate limiting, and pedagogical
    optimization.
    """

    def __init__(
        self,
        llm_factory: LLMProviderFactory,
        cache_service: AbstractCacheService,
        database_service: AbstractDatabaseService,
        rate_limiter: AbstractRateLimiter,
        monitoring_service: Optional[AbstractMonitoringService] = None,
    ):
        """
        Initialize teaching service.

        Args:
            llm_factory: Factory for creating LLM providers
            cache_service: Cache service for responses
            database_service: Database for persistent storage
            rate_limiter: Rate limiting service
            monitoring_service: Monitoring and observability service
        """
        self.llm_factory = llm_factory
        self.cache = cache_service
        self.database = database_service
        self.rate_limiter = rate_limiter
        self.monitoring = monitoring_service

    async def ask_question(self, request: TeachingRequest) -> TeachingResponse:
        """
        Main teaching endpoint with intelligent model routing.

        This method orchestrates the entire teaching flow:
        1. Rate limiting
        2. Cache checking
        3. Model selection
        4. Prompt engineering
        5. LLM generation
        6. Post-processing
        7. Caching and storage
        8. Usage tracking

        Args:
            request: Teaching request with question and context

        Returns:
            Teaching response with answer and metadata

        Raises:
            RateLimitExceeded: If rate limit exceeded
            ProviderError: If LLM generation fails
        """
        start_time = time.time()

        # 1. Rate limiting
        await self.rate_limiter.check_limit(
            identifier=request.student_id,
            limit=10,  # TODO: Make configurable per tier
            window_seconds=60,
        )

        # 2. Check cache for similar questions
        cached = await self.cache.get_teaching_response(request)
        if cached:
            if self.monitoring:
                await self.monitoring.record_cache_hit(
                    f"teaching:{request.subject.value}"
                )

            return TeachingResponse(
                answer=cached.answer,
                model_used=cached.model_used,
                tokens_used=cached.tokens_used,
                estimated_cost=cached.estimated_cost,
                confidence=cached.confidence,
                source="cache",
                processing_time_ms=int((time.time() - start_time) * 1000),
                follow_up_suggestions=cached.follow_up_suggestions,
                learning_resources=cached.learning_resources,
            )

        if self.monitoring:
            await self.monitoring.record_cache_miss(f"teaching:{request.subject.value}")

        # 3. Select appropriate model based on request characteristics
        model_id = self._select_model(request)

        # 4. Get model configuration
        model_config = self.llm_factory.get_model_config(model_id)

        # 5. Build pedagogically optimized prompt
        prompt = self._build_teaching_prompt(request, model_config)

        # 6. Get LLM provider for this model
        provider = self.llm_factory.get_provider_for_model(model_id)

        # 7. Generate response
        try:
            llm_response = await provider.generate(prompt, model_config.to_dict())

            # Track LLM call
            if self.monitoring:
                await self.monitoring.track_llm_call(
                    model=model_id,
                    tokens_used=llm_response.tokens_used,
                    cost=llm_response.cost,
                    latency_ms=llm_response.processing_time_ms,
                    success=True,
                )

        except Exception as e:
            if self.monitoring:
                await self.monitoring.track_llm_call(
                    model=model_id,
                    tokens_used=0,
                    cost=0.0,
                    latency_ms=int((time.time() - start_time) * 1000),
                    success=False,
                    error=str(e),
                )
            raise

        # 8. Post-process for educational context
        processed_answer = self._post_process_response(llm_response.content, request)

        # 9. Generate follow-up suggestions
        follow_ups = self._generate_follow_up_suggestions(request, processed_answer)

        # 10. Calculate confidence score
        confidence = self._calculate_confidence(llm_response, request)

        # 11. Create teaching response
        teaching_response = TeachingResponse(
            answer=processed_answer,
            model_used=model_id,
            tokens_used=llm_response.tokens_used,
            estimated_cost=llm_response.cost,
            confidence=confidence,
            source="llm",
            processing_time_ms=int((time.time() - start_time) * 1000),
            follow_up_suggestions=follow_ups,
            learning_resources=self._suggest_learning_resources(request),
        )

        # 12. Cache result (async, don't wait)
        await self.cache.set_teaching_response(
            request, teaching_response, ttl_seconds=3600
        )

        # 13. Save conversation to database (async, don't wait)
        await self.database.save_conversation(
            student_id=request.student_id, request=request, response=teaching_response
        )

        # 14. Track usage for cost optimization
        await self._track_usage(
            student_id=request.student_id,
            model_id=model_id,
            tokens_used=llm_response.tokens_used,
            cost=llm_response.cost,
        )

        return teaching_response

    def _select_model(self, request: TeachingRequest) -> str:
        """
        Intelligent model selection based on request characteristics.

        Selection criteria:
        - User preference (if specified)
        - Question complexity
        - Subject matter
        - Grade level
        - Available budget
        - Current model availability

        Args:
            request: Teaching request

        Returns:
            Selected model ID
        """
        # If user specified a preference, use it (with validation)
        if request.model_preference:
            available_models = self.llm_factory.config.list_available_models()
            if request.model_preference in available_models:
                return request.model_preference

        # Analyze question complexity (simple heuristic)
        question_length = len(request.question)
        has_context = bool(request.additional_context)

        # Advanced subjects or complex questions might need better models
        advanced_subjects = {"physics", "chemistry", "computer_science"}
        is_advanced = request.subject.value in advanced_subjects

        # College level or complex questions
        is_college = request.grade_level.value == "college"
        is_complex = question_length > 500 or has_context or is_college

        # Model selection logic
        # TODO: Make this configurable via routing rules in models.yaml
        if is_complex and is_advanced:
            # Try to use advanced model if available
            if "llama3-8b-advanced" in self.llm_factory.config.list_available_models():
                return "llama3-8b-advanced"

        # Default to phi3-mini for educational use
        return self.llm_factory.config.default_model

    def _build_teaching_prompt(self, request: TeachingRequest, model_config) -> str:
        """
        Build pedagogically optimized prompt.

        Incorporates:
        - System prompt from model config
        - Grade-level appropriate language
        - Subject-specific context
        - Conversation history
        - Socratic questioning techniques

        Args:
            request: Teaching request
            model_config: Model configuration

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        # Add conversation history if available
        if request.conversation_history:
            prompt_parts.append("Previous conversation:")
            for msg in request.conversation_history[-5:]:  # Last 5 messages
                role = msg.role.capitalize()
                prompt_parts.append(f"{role}: {msg.content}")
            prompt_parts.append("")

        # Add subject and grade level context
        prompt_parts.append(
            f"Subject: {request.subject.value.replace('_', ' ').title()}"
        )
        prompt_parts.append(
            f"Grade Level: {request.grade_level.value.replace('_', ' ').title()}"
        )
        prompt_parts.append("")

        # Add additional context if provided
        if request.additional_context:
            prompt_parts.append("Additional Context:")
            for key, value in request.additional_context.items():
                prompt_parts.append(f"- {key}: {value}")
            prompt_parts.append("")

        # Add pedagogical instructions
        prompt_parts.append("Teaching Guidelines:")
        prompt_parts.append("- Use Socratic questioning to guide learning")
        prompt_parts.append("- Encourage critical thinking and problem-solving")
        prompt_parts.append("- Provide clear explanations with examples")
        prompt_parts.append("- Adapt language to the student's grade level")
        prompt_parts.append("- Be encouraging and supportive")
        prompt_parts.append("")

        # Add the actual question
        prompt_parts.append(f"Student Question: {request.question}")
        prompt_parts.append("")
        prompt_parts.append("Please provide a helpful, educational response:")

        return "\n".join(prompt_parts)

    def _post_process_response(
        self, raw_response: str, request: TeachingRequest
    ) -> str:
        """
        Post-process LLM response for educational context.

        - Format for readability
        - Add grade-appropriate language checks
        - Remove inappropriate content
        - Add markdown formatting

        Args:
            raw_response: Raw LLM response
            request: Original request for context

        Returns:
            Processed response
        """
        # For now, return as-is
        # TODO: Add content filtering, formatting, etc.
        processed = raw_response.strip()

        # Ensure response isn't too long
        max_length = 2000
        if len(processed) > max_length:
            processed = processed[:max_length] + "..."

        return processed

    def _generate_follow_up_suggestions(
        self, request: TeachingRequest, answer: str
    ) -> List[str]:
        """
        Generate follow-up question suggestions.

        Args:
            request: Original request
            answer: Generated answer

        Returns:
            List of follow-up suggestions
        """
        # Simple heuristic-based suggestions
        # TODO: Use LLM to generate better suggestions
        suggestions = []

        subject = request.subject.value

        if subject == "math":
            suggestions.append("Can you show me another example?")
            suggestions.append("How would this apply to a real-world problem?")
        elif subject in ["science", "physics", "chemistry", "biology"]:
            suggestions.append("Can you explain the underlying principle?")
            suggestions.append("What are some real-world applications?")
        elif subject in ["history", "literature"]:
            suggestions.append("What was the historical context?")
            suggestions.append("How does this relate to other events?")

        # Generic suggestions
        suggestions.append("Can you explain this in simpler terms?")

        return suggestions[:3]  # Return top 3

    def _suggest_learning_resources(self, request: TeachingRequest) -> List[str]:
        """
        Suggest additional learning resources.

        Args:
            request: Teaching request

        Returns:
            List of resource URLs/descriptions
        """
        # TODO: Integrate with learning resource database
        resources = []

        subject = request.subject.value

        if subject == "math":
            resources.append("Khan Academy - Math")
            resources.append("Brilliant.org - Interactive Math")
        elif subject in ["science", "physics"]:
            resources.append("PhET Interactive Simulations")
            resources.append("Khan Academy - Physics")

        return resources

    def _calculate_confidence(self, llm_response, request: TeachingRequest) -> float:
        """
        Calculate confidence score for the response.

        Based on:
        - Response length
        - Token usage vs expected
        - Model performance metrics

        Args:
            llm_response: LLM response object
            request: Original request

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Simple heuristic for now
        # TODO: Implement more sophisticated confidence estimation

        # Start with base confidence
        confidence = 0.7

        # Adjust based on response length
        response_length = len(llm_response.content)
        if response_length < 50:
            confidence -= 0.2  # Very short response
        elif response_length > 200:
            confidence += 0.1  # Detailed response

        # Ensure in valid range
        confidence = max(0.0, min(1.0, confidence))

        return confidence

    async def _track_usage(
        self, student_id: str, model_id: str, tokens_used: int, cost: float
    ) -> None:
        """
        Track token usage and cost for analytics.

        Args:
            student_id: Student identifier
            model_id: Model used
            tokens_used: Tokens consumed
            cost: Cost in USD
        """
        metrics = UsageMetrics(
            user_id=student_id,
            model=model_id,
            tokens_used=tokens_used,
            cost=cost,
            timestamp=datetime.utcnow(),
        )

        await self.database.save_usage_metrics(metrics)
