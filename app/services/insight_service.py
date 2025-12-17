import json
import time
from typing import Dict, Any
from pydantic import ValidationError
from app.models.schemas import (
    InsightRequest, InsightResponse, FeatureSet,
    InsightOutput, InputSummary, ResponseMetadata
)
from app.clients.llm_base import LLMClient
from app.services.feature_extractor import FeatureExtractor
from app.services.prompt_builder import PromptBuilder
from app.config import Settings
from app.services.anomaly_detector import AnomalyDetector, AnomalyResult
import logging

logger = logging.getLogger(__name__)


class InsightService:
    def __init__(self, llm_client: LLMClient, settings: Settings):
        self.llm_client = llm_client
        self.settings = settings
        self.feature_extractor = FeatureExtractor(settings)
        self.prompt_builder = PromptBuilder()
        self.anomaly_detector = AnomalyDetector()

    async def generate_insight(self, request: InsightRequest) -> InsightResponse:
        """
        Main orchestration method for insight generation.
        Implements retry logic and fallback strategy.
        """
        start_time = time.time()
        fallback_used = False

        logger.info(f"Request data: {request.data}")
        logger.info(f"Request input_type: {request.input_type}")
        try:
            # Step 1: Extract features
            features = self._extract_features(request)
            logger.info(f"Features extracted: {features.dict()}")

            # Step 1.1: Run anomaly detection
            anomaly_result = None
            if request.input_type == "metrics":
                values = request.data.get('values', [])
                if len(values) >= 3:
                    anomaly_result = self.anomaly_detector.z_score_detection(values)
                    logger.info(f"Anomaly detection: {anomaly_result.is_anomaly} "
                                f"(z-score: {anomaly_result.z_score:.2f})")

            # Step 2: Build prompt
            metric_name = self._get_metric_name(request)
            prompt = self.prompt_builder.build_insight_prompt(
                metric_name=metric_name,
                features=features,
                input_data=request.data,
                anomaly_result=anomaly_result  # ← ADD THIS
            )

            # Step 3: Call LLM with retry logic
            llm_output = await self._call_llm_with_retry(prompt)

            # Step 4: Validate and parse LLM output
            try:
                insight = InsightOutput(**json.loads(llm_output))
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"LLM output validation failed: {e}")
                # Use rule-based fallback
                insight = self._generate_fallback_insight(features, metric_name)
                fallback_used = True

        except Exception as e:
            logger.error(f"Insight generation failed: {e}", exc_info=True)

            # Try to preserve extracted features if they exist
            try:
                # Features already extracted before error
                if 'features' not in locals():
                    features = FeatureSet(
                        previous_value=0.0,
                        current_value=0.0,
                        change_absolute=0.0,
                        change_percent=0.0,
                        severity="low"
                    )
                if 'metric_name' not in locals():
                    metric_name = self._get_metric_name(request) if hasattr(request, 'data') else "unknown"
            except:
                features = FeatureSet(
                    previous_value=0.0,
                    current_value=0.0,
                    change_absolute=0.0,
                    change_percent=0.0,
                    severity="low"
                )
                metric_name = "unknown"


            insight = self._generate_fallback_insight(features, metric_name)
            fallback_used = True

        # Step 5: Build response
        processing_time = int((time.time() - start_time) * 1000)

        return InsightResponse(
            user_id=request.user_id,
            tenant_id=request.tenant_id,
            input_summary=InputSummary(
                metric_name=metric_name,
                data_points_count=len(request.data.get('values', [1, 2])),
                time_range=None  # TODO: Parse from timestamps
            ),
            features=features,
            insight=insight,
            metadata=ResponseMetadata(
                processing_time_ms=processing_time,
                llm_provider=self.settings.llm_provider,
                model_version=self.llm_client.get_model_name(),
                fallback_used=fallback_used
            )
        )

    def _extract_features(self, request: InsightRequest) -> FeatureSet:
        """Route to appropriate feature extractor"""
        if request.input_type == "metrics":
            values = request.data.get('values', [])  # ← CHANGE 1: Use .get()

            # CHANGE 2: Add validation
            if not values or len(values) < 2:
                logger.warning(f"Invalid values in request: {request.data}")
                raise ValueError("Need at least 2 values in data.values")

            context = request.context.dict() if request.context else None
            return self.feature_extractor.extract_from_metrics(values, context)

    def _get_metric_name(self, request: InsightRequest) -> str:
        """Extract metric name from request data"""
        if request.input_type == "metrics":
            metric_name = request.data.get('metric_name')
            if not metric_name:
                logger.warning(f"Missing metric_name in request data: {request.data}")
                return "Unknown Metric"
            return metric_name
        elif request.input_type == "text":
            return "Text Analysis"
        else:
            return request.data.get('series_name', 'Time Series')

    async def _call_llm_with_retry(self, prompt: str) -> str:
        """
        Call LLM with retry logic and progressive prompt refinement.
        """
        schema = self.prompt_builder.get_response_schema()
        last_error = None

        for attempt in range(self.settings.llm_max_retries):
            try:
                logger.info(f"LLM call attempt {attempt + 1}/{self.settings.llm_max_retries}")

                # Refine prompt after first failure
                if attempt > 0 and last_error:
                    prompt += f"\n\nPREVIOUS ATTEMPT FAILED: {last_error}\nEnsure output is valid JSON."

                response = await self.llm_client.generate(
                    prompt=prompt,
                    response_schema=schema,
                    temperature=0.7
                )

                # Validate it's parseable JSON
                json.loads(response)
                return response

            except Exception as e:
                last_error = str(e)
                logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}")

                if attempt == self.settings.llm_max_retries - 1:
                    raise

        raise Exception("LLM retry limit exceeded")

    def _generate_fallback_insight(self, features: FeatureSet, metric_name: str) -> InsightOutput:
        """
        Rule-based fallback when LLM fails.
        Ensures the system always returns a valid response.
        """
        if features.change_percent > 0:
            direction = "increase"
            action_verb = "investigate the cause of this growth"
        else:
            direction = "decrease"
            action_verb = "identify factors driving this decline"

        summary = (
            f"{metric_name} experienced a {abs(features.change_percent):.1f}% {direction} "
            f"from {features.previous_value} to {features.current_value}. "
            f"This change has been classified as {features.severity} severity based on "
            f"historical thresholds."
        )

        return InsightOutput(
            summary=summary,
            severity=features.severity,
            confidence=0.60,  # Lower confidence for rule-based
            recommended_actions=[
                f"Review {metric_name} data for the past 7 days to identify patterns",
                f"Verify data quality and check for any anomalies in data collection",
                f"Consult with relevant teams to {action_verb}"
            ],
            key_findings=[
                f"{abs(features.change_percent):.1f}% change detected",
                f"Current value: {features.current_value}",
                "Analysis based on rule-based thresholds (LLM unavailable)"
            ]
        )
