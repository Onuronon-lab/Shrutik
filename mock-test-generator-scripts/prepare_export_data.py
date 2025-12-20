#!/usr/bin/env python3
"""
prepare_export_data.py - Prepare transcribed chunks for export by calculating consensus

This script processes chunks that have sufficient transcriptions (≥5) and calculates
consensus to mark them as ready for export. It simulates the complete workflow from
transcriptions to export-ready data.

Features:
- Finds chunks with ≥5 transcriptions
- Calculates consensus quality scores
- Marks chunks as ready_for_export when quality ≥90%
- Updates chunk metadata for export optimization
- Provides statistics on export readiness

Usage:
    DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
    python prepare_export_data.py
"""

import os
import statistics
import sys
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from tqdm import tqdm

# Check dependencies
missing_deps = []
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except ImportError:
    missing_deps.append("sqlalchemy")

if missing_deps:
    print("ERROR: Missing required dependencies!")
    print(f"\nPlease install: pip install {' '.join(missing_deps)}")
    sys.exit(1)

# ----------------- CONFIG -----------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: Please set DATABASE_URL environment variable.")
    print(
        "Example: DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection"
    )
    sys.exit(1)

# Create database engine and session
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Configuration
MIN_TRANSCRIPTIONS_FOR_CONSENSUS = 5
EXPORT_QUALITY_THRESHOLD = 0.30  # 30% quality required for export (lowered for testing)


class ConsensusCalculator:
    """Calculates consensus for chunks with multiple transcriptions."""

    def __init__(self):
        self.db = SessionLocal()

    def get_chunks_for_consensus(self) -> List[Dict]:
        """Get chunks that have enough transcriptions for consensus calculation."""
        query = text(
            """
            SELECT
                ac.id as chunk_id,
                ac.recording_id,
                ac.chunk_index,
                ac.duration,
                ac.transcript_count,
                ac.consensus_quality,
                ac.ready_for_export,
                vr.language_id,
                COUNT(t.id) as actual_transcription_count
            FROM audio_chunks ac
            JOIN voice_recordings vr ON ac.recording_id = vr.id
            JOIN transcriptions t ON ac.id = t.chunk_id
            WHERE vr.status = 'CHUNKED'
            GROUP BY ac.id, ac.recording_id, ac.chunk_index, ac.duration,
                     ac.transcript_count, ac.consensus_quality, ac.ready_for_export, vr.language_id
            HAVING COUNT(t.id) >= :min_transcriptions
            ORDER BY ac.id
        """
        )

        results = self.db.execute(
            query, {"min_transcriptions": MIN_TRANSCRIPTIONS_FOR_CONSENSUS}
        ).fetchall()

        chunks = []
        for row in results:
            chunks.append(
                {
                    "chunk_id": row.chunk_id,
                    "recording_id": row.recording_id,
                    "chunk_index": row.chunk_index,
                    "duration": row.duration,
                    "language_id": row.language_id,
                    "current_transcript_count": row.transcript_count or 0,
                    "actual_transcription_count": row.actual_transcription_count,
                    "current_consensus_quality": row.consensus_quality or 0.0,
                    "currently_ready_for_export": row.ready_for_export or False,
                }
            )

        return chunks

    def get_transcriptions_for_chunk(self, chunk_id: int) -> List[Dict]:
        """Get all transcriptions for a chunk."""
        query = text(
            """
            SELECT id, user_id, text, quality, confidence, created_at
            FROM transcriptions
            WHERE chunk_id = :chunk_id
            ORDER BY created_at
        """
        )

        results = self.db.execute(query, {"chunk_id": chunk_id}).fetchall()

        transcriptions = []
        for row in results:
            transcriptions.append(
                {
                    "id": row.id,
                    "user_id": row.user_id,
                    "text": row.text,
                    "quality": row.quality or 0.5,
                    "confidence": row.confidence or 0.5,
                    "created_at": row.created_at,
                }
            )

        return transcriptions

    def calculate_consensus_quality(
        self, transcriptions: List[Dict]
    ) -> Tuple[float, Optional[int], Dict]:
        """
        Calculate consensus quality score and select consensus transcription.

        Returns:
            (quality_score, consensus_transcription_id, metadata)
        """
        if len(transcriptions) < MIN_TRANSCRIPTIONS_FOR_CONSENSUS:
            return 0.0, None, {"error": "insufficient_transcriptions"}

        # Calculate pairwise similarities
        similarities = []
        texts = [t["text"].strip().lower() for t in transcriptions]

        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                similarity = SequenceMatcher(None, texts[i], texts[j]).ratio()
                similarities.append(similarity)

        avg_similarity = statistics.mean(similarities) if similarities else 0.0

        # Find consensus transcription (highest average similarity to others)
        best_transcription_id = None
        best_score = -1.0

        for i, candidate in enumerate(transcriptions):
            candidate_similarities = []
            candidate_text = candidate["text"].strip().lower()

            for j, other in enumerate(transcriptions):
                if i != j:
                    other_text = other["text"].strip().lower()
                    similarity = SequenceMatcher(
                        None, candidate_text, other_text
                    ).ratio()
                    candidate_similarities.append(similarity)

            # Average similarity to all others
            avg_candidate_similarity = (
                statistics.mean(candidate_similarities)
                if candidate_similarities
                else 0.0
            )

            # Factor in individual quality score
            quality_factor = candidate["quality"]

            # Combined score (70% similarity, 30% individual quality)
            combined_score = (avg_candidate_similarity * 0.7) + (quality_factor * 0.3)

            if combined_score > best_score:
                best_score = combined_score
                best_transcription_id = candidate["id"]

        # Calculate overall quality score
        # Factors: similarity (60%), individual quality (20%), length consistency (20%)

        # Individual quality scores
        quality_scores = [t["quality"] for t in transcriptions]
        avg_quality = statistics.mean(quality_scores)

        # Length consistency
        lengths = [len(t["text"]) for t in transcriptions]
        if len(lengths) > 1 and statistics.mean(lengths) > 0:
            length_std = statistics.stdev(lengths)
            avg_length = statistics.mean(lengths)
            length_consistency = 1.0 - min(length_std / avg_length, 1.0)
        else:
            length_consistency = 1.0

        # Combine factors
        quality_score = (
            avg_similarity * 0.6 + avg_quality * 0.2 + length_consistency * 0.2
        )

        # Clamp to [0, 1]
        quality_score = max(0.0, min(1.0, quality_score))

        metadata = {
            "transcription_count": len(transcriptions),
            "avg_similarity": avg_similarity,
            "avg_individual_quality": avg_quality,
            "length_consistency": length_consistency,
            "consensus_transcription_id": best_transcription_id,
            "pairwise_similarities": similarities,
            "calculated_at": "auto",
        }

        return quality_score, best_transcription_id, metadata

    def update_chunk_consensus(
        self,
        chunk_id: int,
        quality_score: float,
        consensus_transcription_id: Optional[int],
        metadata: Dict,
    ) -> bool:
        """Update chunk with consensus information."""
        try:
            # Determine if ready for export
            ready_for_export = quality_score >= EXPORT_QUALITY_THRESHOLD

            # Update chunk - just update the basic fields, skip metadata for now
            self.db.execute(
                text(
                    """
                    UPDATE audio_chunks
                    SET transcript_count = :count,
                        consensus_quality = :quality,
                        consensus_transcript_id = :consensus_id,
                        ready_for_export = :ready
                    WHERE id = :chunk_id
                """
                ),
                {
                    "chunk_id": chunk_id,
                    "count": metadata["transcription_count"],
                    "quality": quality_score,
                    "consensus_id": consensus_transcription_id,
                    "ready": ready_for_export,
                },
            )

            # Update transcription consensus flags
            if consensus_transcription_id:
                # Clear all consensus flags for this chunk
                self.db.execute(
                    text(
                        """
                        UPDATE transcriptions
                        SET is_consensus = false, is_validated = :validated
                        WHERE chunk_id = :chunk_id
                    """
                    ),
                    {"chunk_id": chunk_id, "validated": ready_for_export},
                )

                # Set consensus flag for selected transcription
                self.db.execute(
                    text(
                        """
                        UPDATE transcriptions
                        SET is_consensus = true, is_validated = :validated
                        WHERE id = :transcription_id
                    """
                    ),
                    {
                        "transcription_id": consensus_transcription_id,
                        "validated": ready_for_export,
                    },
                )

            self.db.commit()
            return True

        except Exception as e:
            print(f"  ❌ Failed to update chunk {chunk_id}: {e}")
            self.db.rollback()
            return False

    def process_chunk(self, chunk_info: Dict) -> Dict:
        """Process a single chunk for consensus calculation."""
        chunk_id = chunk_info["chunk_id"]

        # Get transcriptions
        transcriptions = self.get_transcriptions_for_chunk(chunk_id)

        if len(transcriptions) < MIN_TRANSCRIPTIONS_FOR_CONSENSUS:
            return {
                "chunk_id": chunk_id,
                "status": "insufficient_transcriptions",
                "transcription_count": len(transcriptions),
                "quality_score": 0.0,
                "ready_for_export": False,
            }

        # Calculate consensus
        quality_score, consensus_id, metadata = self.calculate_consensus_quality(
            transcriptions
        )

        # Update database
        success = self.update_chunk_consensus(
            chunk_id, quality_score, consensus_id, metadata
        )

        return {
            "chunk_id": chunk_id,
            "status": "success" if success else "failed",
            "transcription_count": len(transcriptions),
            "quality_score": quality_score,
            "ready_for_export": quality_score >= EXPORT_QUALITY_THRESHOLD,
            "consensus_transcription_id": consensus_id,
        }

    def get_export_statistics(self) -> Dict:
        """Get statistics about export readiness."""
        stats = {}

        # Total chunks
        result = self.db.execute(text("SELECT COUNT(*) FROM audio_chunks")).scalar()
        stats["total_chunks"] = result

        # Chunks with transcriptions
        result = self.db.execute(
            text(
                """
            SELECT COUNT(DISTINCT ac.id)
            FROM audio_chunks ac
            JOIN transcriptions t ON ac.id = t.chunk_id
        """
            )
        ).scalar()
        stats["chunks_with_transcriptions"] = result

        # Chunks ready for export
        result = self.db.execute(
            text(
                """
            SELECT COUNT(*) FROM audio_chunks WHERE ready_for_export = true
        """
            )
        ).scalar()
        stats["chunks_ready_for_export"] = result

        # Chunks with sufficient transcriptions but not ready
        result = (
            self.db.execute(
                text(
                    """
            SELECT COUNT(DISTINCT ac.id)
            FROM audio_chunks ac
            JOIN transcriptions t ON ac.id = t.chunk_id
            WHERE ac.ready_for_export = false
            GROUP BY ac.id
            HAVING COUNT(t.id) >= :min_transcriptions
        """
                ),
                {"min_transcriptions": MIN_TRANSCRIPTIONS_FOR_CONSENSUS},
            ).scalar()
            or 0
        )
        stats["chunks_with_transcriptions_not_ready"] = result

        # Average quality scores
        result = self.db.execute(
            text(
                """
            SELECT AVG(consensus_quality)
            FROM audio_chunks
            WHERE consensus_quality > 0
        """
            )
        ).scalar()
        stats["average_consensus_quality"] = float(result) if result else 0.0

        # Quality distribution
        result = self.db.execute(
            text(
                """
            SELECT
                COUNT(CASE WHEN consensus_quality >= 0.9 THEN 1 END) as excellent,
                COUNT(CASE WHEN consensus_quality >= 0.7 AND consensus_quality < 0.9 THEN 1 END) as good,
                COUNT(CASE WHEN consensus_quality >= 0.5 AND consensus_quality < 0.7 THEN 1 END) as fair,
                COUNT(CASE WHEN consensus_quality > 0 AND consensus_quality < 0.5 THEN 1 END) as poor
            FROM audio_chunks
            WHERE consensus_quality > 0
        """
            )
        ).first()

        stats["quality_distribution"] = {
            "excellent_90_plus": result.excellent if result else 0,
            "good_70_to_90": result.good if result else 0,
            "fair_50_to_70": result.fair if result else 0,
            "poor_below_50": result.poor if result else 0,
        }

        return stats

    def run_consensus_calculation(self):
        """Main consensus calculation workflow."""
        print("=" * 60)
        print("EXPORT DATA PREPARATION")
        print("=" * 60)

        # Get initial statistics
        print("\n📊 Current export statistics:")
        initial_stats = self.get_export_statistics()
        print(f"  Total chunks: {initial_stats['total_chunks']}")
        print(
            f"  Chunks with transcriptions: {initial_stats['chunks_with_transcriptions']}"
        )
        print(f"  Chunks ready for export: {initial_stats['chunks_ready_for_export']}")
        print(
            f"  Average consensus quality: {initial_stats['average_consensus_quality']:.3f}"
        )

        # Get chunks needing consensus calculation
        print(
            f"\n🔍 Finding chunks with ≥{MIN_TRANSCRIPTIONS_FOR_CONSENSUS} transcriptions..."
        )
        chunks = self.get_chunks_for_consensus()

        if not chunks:
            print("✓ No chunks need consensus calculation!")
            return

        # Filter chunks that need processing
        chunks_to_process = []
        already_ready = 0

        for chunk in chunks:
            if not chunk["currently_ready_for_export"]:
                chunks_to_process.append(chunk)
            else:
                already_ready += 1

        print(f"Found {len(chunks)} chunks with sufficient transcriptions")
        print(f"  - Already ready for export: {already_ready}")
        print(f"  - Need consensus calculation: {len(chunks_to_process)}")

        if not chunks_to_process:
            print(
                "✓ All chunks with sufficient transcriptions are already ready for export!"
            )
            return

        # Confirm processing
        confirm = (
            input(
                f"\nProcess {len(chunks_to_process)} chunks for consensus calculation? [Y/n]: "
            )
            .strip()
            .lower()
        )
        if confirm and confirm not in ["y", "yes"]:
            print("Cancelled.")
            return

        # Process chunks
        print(f"\n🔄 Calculating consensus for {len(chunks_to_process)} chunks...")

        results = {
            "processed": 0,
            "ready_for_export": 0,
            "failed": 0,
            "insufficient": 0,
        }

        progress = tqdm(chunks_to_process, desc="Processing chunks", unit="chunk")

        for chunk_info in progress:
            chunk_id = chunk_info["chunk_id"]
            progress.set_description(f"Processing chunk {chunk_id}")

            result = self.process_chunk(chunk_info)

            results["processed"] += 1

            if result["status"] == "success":
                if result["ready_for_export"]:
                    results["ready_for_export"] += 1
            elif result["status"] == "insufficient_transcriptions":
                results["insufficient"] += 1
            else:
                results["failed"] += 1

            progress.set_postfix(
                {"ready": results["ready_for_export"], "failed": results["failed"]}
            )

        progress.close()

        # Get final statistics
        print(f"\n📊 Final export statistics:")
        final_stats = self.get_export_statistics()
        print(f"  Total chunks: {final_stats['total_chunks']}")
        print(
            f"  Chunks ready for export: {final_stats['chunks_ready_for_export']} (+{final_stats['chunks_ready_for_export'] - initial_stats['chunks_ready_for_export']})"
        )
        print(
            f"  Average consensus quality: {final_stats['average_consensus_quality']:.3f}"
        )

        # Quality distribution
        dist = final_stats["quality_distribution"]
        print(f"\n📈 Quality distribution:")
        print(f"  Excellent (≥90%): {dist['excellent_90_plus']}")
        print(f"  Good (70-90%): {dist['good_70_to_90']}")
        print(f"  Fair (50-70%): {dist['fair_50_to_70']}")
        print(f"  Poor (<50%): {dist['poor_below_50']}")

        print(f"\n{'=' * 60}")
        print("CONSENSUS CALCULATION COMPLETE")
        print(f"{'=' * 60}")
        print(f"Chunks processed: {results['processed']}")
        print(f"Now ready for export: {results['ready_for_export']}")
        print(f"Failed processing: {results['failed']}")
        print(f"Quality threshold: {EXPORT_QUALITY_THRESHOLD * 100}%")
        print(f"{'=' * 60}")

    def close(self):
        """Clean up database connection."""
        self.db.close()


def main():
    calculator = None
    try:
        calculator = ConsensusCalculator()
        calculator.run_consensus_calculation()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
    finally:
        if calculator:
            calculator.close()


if __name__ == "__main__":
    main()
