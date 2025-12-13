#!/usr/bin/env python3
"""
Create sample data for testing analytics dashboard
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.audio_chunk import AudioChunk
from app.models.script import DurationCategory, Script
from app.models.transcription import Transcription
from app.models.user import User, UserRole
from app.models.voice_recording import RecordingStatus, VoiceRecording


def create_sample_users(db: Session) -> list[User]:
    """Create sample users if they don't exist."""
    print("Creating sample users...")

    users = []
    sample_users = [
        {"name": "Admin", "email": "admin@example.com", "role": UserRole.ADMIN},
        {
            "name": "auto_importer",
            "email": "auto_importer@example.com",
            "role": UserRole.SWORIK_DEVELOPER,
        },
        {
            "name": "pop",
            "email": "popcycle@gmail.com",
            "role": UserRole.SWORIK_DEVELOPER,
        },
        {"name": "φφ", "email": "chunkster@gmail.com", "role": UserRole.CONTRIBUTOR},
        {
            "name": "lamia",
            "email": "lamiaostan@gmail.com",
            "role": UserRole.CONTRIBUTOR,
        },
        {"name": "pookie", "email": "pookie@gmail.com", "role": UserRole.ADMIN},
    ]

    for user_data in sample_users:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing_user:
            user = User(
                name=user_data["name"],
                email=user_data["email"],
                role=user_data["role"],
                password_hash="dummy_hash",  # Not used for sample data
            )
            db.add(user)
            users.append(user)
        else:
            users.append(existing_user)

    db.commit()
    print(f"✓ Created/found {len(users)} users")
    return users


def create_sample_scripts(db: Session) -> list[Script]:
    """Create sample scripts if they don't exist."""
    print("Creating sample scripts...")

    scripts = []
    sample_scripts = [
        {
            "text": "Hello, this is a short test script for voice recording.",
            "duration_category": DurationCategory.SHORT,
            "language_id": 1,
        },
        {
            "text": "This is a medium length script that should take about five minutes to read aloud. It contains more content and complexity.",
            "duration_category": DurationCategory.MEDIUM,
            "language_id": 1,
        },
        {
            "text": "This is a longer script designed to take approximately ten minutes to read. It includes multiple sentences, various topics, and provides a comprehensive test for voice recording capabilities. The script covers different aspects of speech patterns and pronunciation challenges.",
            "duration_category": DurationCategory.LONG,
            "language_id": 1,
        },
    ]

    for script_data in sample_scripts:
        existing_script = (
            db.query(Script).filter(Script.text == script_data["text"]).first()
        )
        if not existing_script:
            script = Script(**script_data)
            db.add(script)
            scripts.append(script)
        else:
            scripts.append(existing_script)

    db.commit()
    print(f"✓ Created/found {len(scripts)} scripts")
    return scripts


def create_sample_recordings(
    db: Session, users: list[User], scripts: list[Script]
) -> list[VoiceRecording]:
    """Create sample voice recordings with dates spread over the last 30 days."""
    print("Creating sample voice recordings...")

    recordings = []
    from datetime import timezone

    end_date = datetime.now(timezone.utc)

    # Create recordings for the last 30 days
    for days_ago in range(30):
        date = end_date - timedelta(days=days_ago)

        # Create 1-5 recordings per day (random distribution)
        import random

        num_recordings = random.randint(0, 5)

        for i in range(num_recordings):
            user = random.choice(users)
            script = random.choice(scripts)

            # Create recording with the specific date
            recording = VoiceRecording(
                user_id=user.id,
                script_id=script.id,
                language_id=1,
                file_path=f"/fake/path/recording_{date.strftime('%Y%m%d')}_{i}.wav",
                duration=random.randint(60, 600),  # 1-10 minutes
                status=random.choice(
                    [
                        RecordingStatus.CHUNKED,
                        RecordingStatus.PROCESSING,
                        RecordingStatus.FAILED,
                    ]
                ),
                created_at=date,
                updated_at=date,
            )
            db.add(recording)
            recordings.append(recording)

    db.commit()
    print(f"✓ Created {len(recordings)} sample recordings")
    return recordings


def create_sample_chunks_and_transcriptions(
    db: Session, recordings: list[VoiceRecording], users: list[User]
):
    """Create sample audio chunks and transcriptions."""
    print("Creating sample chunks and transcriptions...")

    chunks_created = 0
    transcriptions_created = 0

    for recording in recordings:
        if recording.status != RecordingStatus.CHUNKED:
            continue

        # Create 1-3 chunks per recording
        import random

        num_chunks = random.randint(1, 3)

        for chunk_idx in range(num_chunks):
            chunk = AudioChunk(
                recording_id=recording.id,
                chunk_index=chunk_idx,
                file_path=f"/fake/path/chunk_{recording.id}_{chunk_idx}.wav",
                start_time=chunk_idx * 30.0,
                end_time=(chunk_idx + 1) * 30.0,
                duration=30.0,
                created_at=recording.created_at,
            )
            db.add(chunk)
            db.flush()  # Get the chunk ID
            chunks_created += 1

            # Create transcription for this chunk (80% chance)
            if random.random() < 0.8:
                transcriber = random.choice(users)
                transcription = Transcription(
                    chunk_id=chunk.id,
                    user_id=transcriber.id,
                    text=f"Sample transcription text for chunk {chunk_idx} of recording {recording.id}",
                    language_id=1,
                    quality=random.uniform(0.6, 1.0),
                    confidence=random.uniform(0.7, 1.0),
                    created_at=recording.created_at
                    + timedelta(hours=random.randint(1, 24)),
                )
                db.add(transcription)
                transcriptions_created += 1

    db.commit()
    print(
        f"✓ Created {chunks_created} chunks and {transcriptions_created} transcriptions"
    )


def main():
    """Main function to create all sample data."""
    print("🎯 Creating sample analytics data...\n")

    try:
        # Get database session
        db = next(get_db())

        # Create sample data
        users = create_sample_users(db)
        scripts = create_sample_scripts(db)
        recordings = create_sample_recordings(db, users, scripts)
        create_sample_chunks_and_transcriptions(db, recordings, users)

        print("\n🎉 Sample analytics data created successfully!")
        print("You can now view the analytics dashboard with data.")

    except Exception as e:
        print(f"\n❌ Failed to create sample data: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
