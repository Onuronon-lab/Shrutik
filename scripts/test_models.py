#!/usr/bin/env python3
"""Test script to verify database models work correctly"""

import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models import (
    AudioChunk,
    DurationCategory,
    Language,
    QualityReview,
    RecordingStatus,
    ReviewDecision,
    Script,
    Transcription,
    User,
    UserRole,
    VoiceRecording,
)


def test_model_creation():
    """Test that all models can be instantiated"""
    print("Testing model creation...")

    # Test User model
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash="hashed_password",
        role=UserRole.CONTRIBUTOR,
    )
    print(f"✓ User model: {user.name} ({user.role})")

    # Test Language model
    language = Language(name="Bangla", code="bn")
    print(f"✓ Language model: {language.name} ({language.code})")

    # Test Script model
    script = Script(
        text="This is a test script",
        duration_category=DurationCategory.SHORT,
        language_id=1,
    )
    print(f"✓ Script model: {script.duration_category}")

    # Test VoiceRecording model
    recording = VoiceRecording(
        user_id=1,
        script_id=1,
        language_id=1,
        file_path="/path/to/audio.wav",
        duration=120.5,
        status=RecordingStatus.UPLOADED,
    )
    print(f"✓ VoiceRecording model: {recording.duration}s ({recording.status})")

    # Test AudioChunk model
    chunk = AudioChunk(
        recording_id=1,
        chunk_index=0,
        file_path="/path/to/chunk.wav",
        start_time=0.0,
        end_time=5.0,
        duration=5.0,
    )
    print(f"✓ AudioChunk model: {chunk.duration}s")

    # Test Transcription model
    transcription = Transcription(
        chunk_id=1,
        user_id=1,
        language_id=1,
        text="This is the transcribed text",
        quality=0.95,
        confidence=0.88,
    )
    print(f"✓ Transcription model: quality={transcription.quality}")

    # Test QualityReview model
    review = QualityReview(
        transcription_id=1, reviewer_id=1, decision=ReviewDecision.APPROVED, rating=4.5
    )
    print(f"✓ QualityReview model: {review.decision} (rating={review.rating})")

    print("\n✅ All models created successfully!")


def test_model_relationships():
    """Test that model relationships are properly defined"""
    print("\nTesting model relationships...")

    # Check that all relationship attributes exist
    user = User(
        name="Test",
        email="test@example.com",
        password_hash="hash",
        role=UserRole.CONTRIBUTOR,
    )

    # Test User relationships
    assert hasattr(
        user, "voice_recordings"
    ), "User should have voice_recordings relationship"
    assert hasattr(
        user, "transcriptions"
    ), "User should have transcriptions relationship"
    assert hasattr(
        user, "quality_reviews"
    ), "User should have quality_reviews relationship"

    print("✓ User relationships defined")

    # Test other model relationships
    language = Language(name="Test", code="test")
    assert hasattr(language, "scripts"), "Language should have scripts relationship"
    assert hasattr(
        language, "voice_recordings"
    ), "Language should have voice_recordings relationship"
    assert hasattr(
        language, "transcriptions"
    ), "Language should have transcriptions relationship"

    print("✓ Language relationships defined")

    script = Script(
        text="test", duration_category=DurationCategory.SHORT, language_id=1
    )
    assert hasattr(script, "language"), "Script should have language relationship"
    assert hasattr(
        script, "voice_recordings"
    ), "Script should have voice_recordings relationship"

    print("✓ Script relationships defined")

    print("✅ All relationships properly defined!")


def test_enum_values():
    """Test that all enum values are accessible"""
    print("\nTesting enum values...")

    # Test UserRole enum
    roles = [UserRole.CONTRIBUTOR, UserRole.ADMIN, UserRole.SWORIK_DEVELOPER]
    print(f"✓ UserRole values: {[role.value for role in roles]}")

    # Test DurationCategory enum
    durations = [DurationCategory.SHORT, DurationCategory.MEDIUM, DurationCategory.LONG]
    print(f"✓ DurationCategory values: {[dur.value for dur in durations]}")

    # Test RecordingStatus enum
    statuses = [
        RecordingStatus.UPLOADED,
        RecordingStatus.PROCESSING,
        RecordingStatus.CHUNKED,
        RecordingStatus.FAILED,
    ]
    print(f"✓ RecordingStatus values: {[status.value for status in statuses]}")

    # Test ReviewDecision enum
    decisions = [
        ReviewDecision.APPROVED,
        ReviewDecision.REJECTED,
        ReviewDecision.NEEDS_REVISION,
        ReviewDecision.FLAGGED,
    ]
    print(f"✓ ReviewDecision values: {[decision.value for decision in decisions]}")

    print("✅ All enum values accessible!")


if __name__ == "__main__":
    print("🧪 Testing Voice Data Collection Database Models\n")

    try:
        test_model_creation()
        test_model_relationships()
        test_enum_values()

        print("\n🎉 All tests passed! Database models are working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
