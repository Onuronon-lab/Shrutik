"""
Export Metrics Collection Module

This module provides metrics collection for export operations, consensus calculations,
and R2 usage tracking. Metrics are stored in Redis for real-time monitoring and
can be queried for dashboards and alerting.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.core.config import settings
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics tracked."""

    EXPORT_BATCH_CREATED = "export_batch_created"
    EXPORT_BATCH_FAILED = "export_batch_failed"
    CONSENSUS_CALCULATED = "consensus_calculated"
    CONSENSUS_FAILED = "consensus_failed"
    R2_CLASS_A_OPERATION = "r2_class_a_operation"
    R2_CLASS_B_OPERATION = "r2_class_b_operation"
    CHUNK_READY_FOR_EXPORT = "chunk_ready_for_export"
    CLEANUP_COMPLETED = "cleanup_completed"


@dataclass
class ExportMetrics:
    """Export operation metrics."""

    total_batches_created: int
    total_batches_failed: int
    total_chunks_exported: int
    total_batches_today: int
    total_batches_this_week: int
    total_batches_this_month: int
    average_batch_size: float
    average_batch_creation_time: float
    last_batch_created_at: Optional[str]
    last_batch_failed_at: Optional[str]


@dataclass
class ConsensusMetrics:
    """Consensus calculation metrics."""

    total_calculations: int
    total_calculations_today: int
    total_calculations_this_hour: int
    total_failed: int
    total_ready_for_export: int
    success_rate: float
    average_quality_score: float
    average_calculation_time: float
    chunks_in_review_queue: int


@dataclass
class R2Metrics:
    """R2 usage metrics."""

    class_a_operations_today: int
    class_a_operations_this_month: int
    class_b_operations_today: int
    class_b_operations_this_month: int
    storage_used_gb: float
    class_a_limit: int
    class_b_limit: int
    storage_limit_gb: int
    class_a_usage_percent: float
    class_b_usage_percent: float
    storage_usage_percent: float


@dataclass
class ChunkBacklogMetrics:
    """Chunk backlog metrics."""

    total_chunks_ready: int
    total_chunks_pending: int
    average_transcript_count: float
    chunks_with_5_plus_transcripts: int
    chunks_below_quality_threshold: int


class ExportMetricsCollector:
    """Collector for export operation metrics."""

    def __init__(self):
        self.redis = redis_client

    def record_export_batch_created(
        self,
        batch_id: str,
        chunk_count: int,
        user_id: Optional[int] = None,
        creation_time_seconds: Optional[float] = None,
    ):
        """
        Record export batch creation.

        Args:
            batch_id: Unique batch identifier
            chunk_count: Number of chunks in batch
            user_id: User who created the batch
            creation_time_seconds: Time taken to create batch
        """
        try:
            timestamp = datetime.now(timezone.utc)

            # Increment counters
            self.redis.incr("metrics:export:total_batches_created")
            self.redis.incr(
                f"metrics:export:batches_created:{timestamp.strftime('%Y-%m-%d')}"
            )
            self.redis.incr(
                f"metrics:export:batches_created:{timestamp.strftime('%Y-W%W')}"
            )
            self.redis.incr(
                f"metrics:export:batches_created:{timestamp.strftime('%Y-%m')}"
            )

            # Track chunk count
            self.redis.incrby("metrics:export:total_chunks_exported", chunk_count)

            # Track batch sizes for average calculation
            self.redis.lpush("metrics:export:batch_sizes", chunk_count)
            self.redis.ltrim("metrics:export:batch_sizes", 0, 999)  # Keep last 1000

            # Track creation times
            if creation_time_seconds:
                self.redis.lpush("metrics:export:creation_times", creation_time_seconds)
                self.redis.ltrim("metrics:export:creation_times", 0, 999)

            # Store last batch info
            self.redis.set(
                "metrics:export:last_batch_created_at", timestamp.isoformat()
            )
            self.redis.set("metrics:export:last_batch_id", batch_id)

            # Set expiry on daily/weekly/monthly keys
            self.redis.expire(
                f"metrics:export:batches_created:{timestamp.strftime('%Y-%m-%d')}",
                86400 * 90,
            )  # 90 days
            self.redis.expire(
                f"metrics:export:batches_created:{timestamp.strftime('%Y-W%W')}",
                86400 * 90,
            )
            self.redis.expire(
                f"metrics:export:batches_created:{timestamp.strftime('%Y-%m')}",
                86400 * 365,
            )  # 1 year

            logger.debug(
                f"Recorded export batch creation: {batch_id} with {chunk_count} chunks"
            )

        except Exception as e:
            logger.error(f"Failed to record export batch creation metric: {e}")

    def record_export_batch_failed(
        self, batch_id: str, error_message: str, user_id: Optional[int] = None
    ):
        """
        Record export batch failure.

        Args:
            batch_id: Unique batch identifier
            error_message: Error message
            user_id: User who created the batch
        """
        try:
            timestamp = datetime.now(timezone.utc)

            # Increment failure counter
            self.redis.incr("metrics:export:total_batches_failed")
            self.redis.incr(
                f"metrics:export:batches_failed:{timestamp.strftime('%Y-%m-%d')}"
            )

            # Store last failure info
            self.redis.set("metrics:export:last_batch_failed_at", timestamp.isoformat())
            self.redis.set("metrics:export:last_batch_failed_id", batch_id)
            self.redis.set(
                "metrics:export:last_failure_error", error_message[:500]
            )  # Truncate

            # Track consecutive failures for alerting
            self.redis.incr("metrics:export:consecutive_failures")

            # Set expiry
            self.redis.expire(
                f"metrics:export:batches_failed:{timestamp.strftime('%Y-%m-%d')}",
                86400 * 90,
            )

            logger.debug(f"Recorded export batch failure: {batch_id}")

        except Exception as e:
            logger.error(f"Failed to record export batch failure metric: {e}")

    def reset_consecutive_failures(self):
        """Reset consecutive failure counter (called on successful batch creation)."""
        try:
            self.redis.set("metrics:export:consecutive_failures", 0)
        except Exception as e:
            logger.error(f"Failed to reset consecutive failures: {e}")

    def get_export_metrics(self) -> ExportMetrics:
        """
        Get current export metrics.

        Returns:
            ExportMetrics object with current statistics
        """
        try:
            now = datetime.now(timezone.utc)

            # Get counters
            total_batches_created = int(
                self.redis.get("metrics:export:total_batches_created") or 0
            )
            total_batches_failed = int(
                self.redis.get("metrics:export:total_batches_failed") or 0
            )
            total_chunks_exported = int(
                self.redis.get("metrics:export:total_chunks_exported") or 0
            )

            # Get time-based counters
            total_batches_today = int(
                self.redis.get(
                    f"metrics:export:batches_created:{now.strftime('%Y-%m-%d')}"
                )
                or 0
            )
            total_batches_this_week = int(
                self.redis.get(
                    f"metrics:export:batches_created:{now.strftime('%Y-W%W')}"
                )
                or 0
            )
            total_batches_this_month = int(
                self.redis.get(
                    f"metrics:export:batches_created:{now.strftime('%Y-%m')}"
                )
                or 0
            )

            # Calculate averages
            batch_sizes = [
                float(s) for s in self.redis.lrange("metrics:export:batch_sizes", 0, -1)
            ]
            average_batch_size = (
                sum(batch_sizes) / len(batch_sizes) if batch_sizes else 0.0
            )

            creation_times = [
                float(t)
                for t in self.redis.lrange("metrics:export:creation_times", 0, -1)
            ]
            average_creation_time = (
                sum(creation_times) / len(creation_times) if creation_times else 0.0
            )

            # Get last batch info
            last_batch_created_at = self.redis.get(
                "metrics:export:last_batch_created_at"
            )
            last_batch_failed_at = self.redis.get("metrics:export:last_batch_failed_at")

            return ExportMetrics(
                total_batches_created=total_batches_created,
                total_batches_failed=total_batches_failed,
                total_chunks_exported=total_chunks_exported,
                total_batches_today=total_batches_today,
                total_batches_this_week=total_batches_this_week,
                total_batches_this_month=total_batches_this_month,
                average_batch_size=round(average_batch_size, 2),
                average_batch_creation_time=round(average_creation_time, 2),
                last_batch_created_at=(
                    last_batch_created_at.decode()
                    if isinstance(last_batch_created_at, bytes)
                    else last_batch_created_at
                ),
                last_batch_failed_at=(
                    last_batch_failed_at.decode()
                    if isinstance(last_batch_failed_at, bytes)
                    else last_batch_failed_at
                ),
            )

        except Exception as e:
            logger.error(f"Failed to get export metrics: {e}")
            return ExportMetrics(
                total_batches_created=0,
                total_batches_failed=0,
                total_chunks_exported=0,
                total_batches_today=0,
                total_batches_this_week=0,
                total_batches_this_month=0,
                average_batch_size=0.0,
                average_batch_creation_time=0.0,
                last_batch_created_at=None,
                last_batch_failed_at=None,
            )


class ConsensusMetricsCollector:
    """Collector for consensus calculation metrics."""

    def __init__(self):
        self.redis = redis_client

    def record_consensus_calculated(
        self,
        chunk_id: int,
        quality_score: float,
        ready_for_export: bool,
        calculation_time_seconds: Optional[float] = None,
    ):
        """
        Record consensus calculation.

        Args:
            chunk_id: Chunk ID
            quality_score: Calculated quality score
            ready_for_export: Whether chunk is ready for export
            calculation_time_seconds: Time taken to calculate
        """
        try:
            timestamp = datetime.now(timezone.utc)

            # Increment counters
            self.redis.incr("metrics:consensus:total_calculations")
            self.redis.incr(
                f"metrics:consensus:calculations:{timestamp.strftime('%Y-%m-%d')}"
            )
            self.redis.incr(
                f"metrics:consensus:calculations:{timestamp.strftime('%Y-%m-%d-%H')}"
            )

            if ready_for_export:
                self.redis.incr("metrics:consensus:total_ready_for_export")

            # Track quality scores
            self.redis.lpush("metrics:consensus:quality_scores", quality_score)
            self.redis.ltrim("metrics:consensus:quality_scores", 0, 999)

            # Track calculation times
            if calculation_time_seconds:
                self.redis.lpush(
                    "metrics:consensus:calculation_times", calculation_time_seconds
                )
                self.redis.ltrim("metrics:consensus:calculation_times", 0, 999)

            # Set expiry
            self.redis.expire(
                f"metrics:consensus:calculations:{timestamp.strftime('%Y-%m-%d')}",
                86400 * 90,
            )
            self.redis.expire(
                f"metrics:consensus:calculations:{timestamp.strftime('%Y-%m-%d-%H')}",
                86400 * 7,
            )

            logger.debug(f"Recorded consensus calculation for chunk {chunk_id}")

        except Exception as e:
            logger.error(f"Failed to record consensus calculation metric: {e}")

    def record_consensus_failed(self, chunk_id: int, error_message: str):
        """
        Record consensus calculation failure.

        Args:
            chunk_id: Chunk ID
            error_message: Error message
        """
        try:
            timestamp = datetime.now(timezone.utc)

            # Increment failure counter
            self.redis.incr("metrics:consensus:total_failed")
            self.redis.incr(
                f"metrics:consensus:failed:{timestamp.strftime('%Y-%m-%d')}"
            )

            # Set expiry
            self.redis.expire(
                f"metrics:consensus:failed:{timestamp.strftime('%Y-%m-%d')}", 86400 * 90
            )

            logger.debug(f"Recorded consensus failure for chunk {chunk_id}")

        except Exception as e:
            logger.error(f"Failed to record consensus failure metric: {e}")

    def get_consensus_metrics(self) -> ConsensusMetrics:
        """
        Get current consensus metrics.

        Returns:
            ConsensusMetrics object with current statistics
        """
        try:
            now = datetime.now(timezone.utc)

            # Get counters
            total_calculations = int(
                self.redis.get("metrics:consensus:total_calculations") or 0
            )
            total_failed = int(self.redis.get("metrics:consensus:total_failed") or 0)
            total_ready_for_export = int(
                self.redis.get("metrics:consensus:total_ready_for_export") or 0
            )

            # Get time-based counters
            total_calculations_today = int(
                self.redis.get(
                    f"metrics:consensus:calculations:{now.strftime('%Y-%m-%d')}"
                )
                or 0
            )
            total_calculations_this_hour = int(
                self.redis.get(
                    f"metrics:consensus:calculations:{now.strftime('%Y-%m-%d-%H')}"
                )
                or 0
            )

            # Calculate success rate
            success_rate = (
                ((total_calculations - total_failed) / total_calculations * 100)
                if total_calculations > 0
                else 0.0
            )

            # Calculate averages
            quality_scores = [
                float(s)
                for s in self.redis.lrange("metrics:consensus:quality_scores", 0, -1)
            ]
            average_quality_score = (
                sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            )

            calculation_times = [
                float(t)
                for t in self.redis.lrange("metrics:consensus:calculation_times", 0, -1)
            ]
            average_calculation_time = (
                sum(calculation_times) / len(calculation_times)
                if calculation_times
                else 0.0
            )

            # Get review queue size (from database query - placeholder for now)
            chunks_in_review_queue = 0  # Will be populated by database query

            return ConsensusMetrics(
                total_calculations=total_calculations,
                total_calculations_today=total_calculations_today,
                total_calculations_this_hour=total_calculations_this_hour,
                total_failed=total_failed,
                total_ready_for_export=total_ready_for_export,
                success_rate=round(success_rate, 2),
                average_quality_score=round(average_quality_score, 3),
                average_calculation_time=round(average_calculation_time, 3),
                chunks_in_review_queue=chunks_in_review_queue,
            )

        except Exception as e:
            logger.error(f"Failed to get consensus metrics: {e}")
            return ConsensusMetrics(
                total_calculations=0,
                total_calculations_today=0,
                total_calculations_this_hour=0,
                total_failed=0,
                total_ready_for_export=0,
                success_rate=0.0,
                average_quality_score=0.0,
                average_calculation_time=0.0,
                chunks_in_review_queue=0,
            )


class R2MetricsCollector:
    """Collector for R2 usage metrics."""

    def __init__(self):
        self.redis = redis_client

    def record_r2_operation(self, operation_class: str, operation_type: str = ""):
        """
        Record R2 operation.

        Args:
            operation_class: "Class A" or "Class B"
            operation_type: Type of operation (upload, download, etc.)
        """
        try:
            timestamp = datetime.now(timezone.utc)

            if operation_class == "Class A":
                # Increment Class A counters
                self.redis.incr("metrics:r2:class_a_operations_total")
                self.redis.incr(
                    f"metrics:r2:class_a_operations:{timestamp.strftime('%Y-%m-%d')}"
                )
                self.redis.incr(
                    f"metrics:r2:class_a_operations:{timestamp.strftime('%Y-%m')}"
                )

                # Set expiry
                self.redis.expire(
                    f"metrics:r2:class_a_operations:{timestamp.strftime('%Y-%m-%d')}",
                    86400 * 90,
                )
                self.redis.expire(
                    f"metrics:r2:class_a_operations:{timestamp.strftime('%Y-%m')}",
                    86400 * 365,
                )

            elif operation_class == "Class B":
                # Increment Class B counters
                self.redis.incr("metrics:r2:class_b_operations_total")
                self.redis.incr(
                    f"metrics:r2:class_b_operations:{timestamp.strftime('%Y-%m-%d')}"
                )
                self.redis.incr(
                    f"metrics:r2:class_b_operations:{timestamp.strftime('%Y-%m')}"
                )

                # Set expiry
                self.redis.expire(
                    f"metrics:r2:class_b_operations:{timestamp.strftime('%Y-%m-%d')}",
                    86400 * 90,
                )
                self.redis.expire(
                    f"metrics:r2:class_b_operations:{timestamp.strftime('%Y-%m')}",
                    86400 * 365,
                )

            logger.debug(f"Recorded R2 {operation_class} operation: {operation_type}")

        except Exception as e:
            logger.error(f"Failed to record R2 operation metric: {e}")

    def update_storage_used(self, storage_gb: float):
        """
        Update R2 storage used.

        Args:
            storage_gb: Storage used in GB
        """
        try:
            self.redis.set("metrics:r2:storage_used_gb", storage_gb)
            logger.debug(f"Updated R2 storage used: {storage_gb} GB")
        except Exception as e:
            logger.error(f"Failed to update R2 storage metric: {e}")

    def get_r2_metrics(self) -> R2Metrics:
        """
        Get current R2 usage metrics.

        Returns:
            R2Metrics object with current statistics
        """
        try:
            now = datetime.now(timezone.utc)

            # Get operation counters
            class_a_operations_today = int(
                self.redis.get(
                    f"metrics:r2:class_a_operations:{now.strftime('%Y-%m-%d')}"
                )
                or 0
            )
            class_a_operations_this_month = int(
                self.redis.get(f"metrics:r2:class_a_operations:{now.strftime('%Y-%m')}")
                or 0
            )
            class_b_operations_today = int(
                self.redis.get(
                    f"metrics:r2:class_b_operations:{now.strftime('%Y-%m-%d')}"
                )
                or 0
            )
            class_b_operations_this_month = int(
                self.redis.get(f"metrics:r2:class_b_operations:{now.strftime('%Y-%m')}")
                or 0
            )

            # Get storage used
            storage_used_gb = float(self.redis.get("metrics:r2:storage_used_gb") or 0.0)

            # Get limits from settings
            class_a_limit = settings.R2_FREE_TIER_CLASS_A_MONTHLY
            class_b_limit = settings.R2_FREE_TIER_CLASS_B_MONTHLY
            storage_limit_gb = settings.R2_FREE_TIER_STORAGE_GB

            # Calculate usage percentages
            class_a_usage_percent = (
                (class_a_operations_this_month / class_a_limit * 100)
                if class_a_limit > 0
                else 0.0
            )
            class_b_usage_percent = (
                (class_b_operations_this_month / class_b_limit * 100)
                if class_b_limit > 0
                else 0.0
            )
            storage_usage_percent = (
                (storage_used_gb / storage_limit_gb * 100)
                if storage_limit_gb > 0
                else 0.0
            )

            return R2Metrics(
                class_a_operations_today=class_a_operations_today,
                class_a_operations_this_month=class_a_operations_this_month,
                class_b_operations_today=class_b_operations_today,
                class_b_operations_this_month=class_b_operations_this_month,
                storage_used_gb=round(storage_used_gb, 2),
                class_a_limit=class_a_limit,
                class_b_limit=class_b_limit,
                storage_limit_gb=storage_limit_gb,
                class_a_usage_percent=round(class_a_usage_percent, 2),
                class_b_usage_percent=round(class_b_usage_percent, 2),
                storage_usage_percent=round(storage_usage_percent, 2),
            )

        except Exception as e:
            logger.error(f"Failed to get R2 metrics: {e}")
            return R2Metrics(
                class_a_operations_today=0,
                class_a_operations_this_month=0,
                class_b_operations_today=0,
                class_b_operations_this_month=0,
                storage_used_gb=0.0,
                class_a_limit=settings.R2_FREE_TIER_CLASS_A_MONTHLY,
                class_b_limit=settings.R2_FREE_TIER_CLASS_B_MONTHLY,
                storage_limit_gb=settings.R2_FREE_TIER_STORAGE_GB,
                class_a_usage_percent=0.0,
                class_b_usage_percent=0.0,
                storage_usage_percent=0.0,
            )


# Global metric collectors
export_metrics_collector = ExportMetricsCollector()
consensus_metrics_collector = ConsensusMetricsCollector()
r2_metrics_collector = R2MetricsCollector()
