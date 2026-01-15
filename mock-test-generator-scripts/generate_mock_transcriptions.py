#!/usr/bin/env python3
"""
generate_mock_transcriptions.py - Generate mock transcriptions for processed audio chunks

This script creates realistic transcriptions for audio chunks that have been processed
but don't have transcriptions yet. It uses the original script text as a base and
creates variations to simulate multiple users transcribing the same audio.

Features:
- Generates 5-8 transcriptions per chunk (required for consensus)
- Creates realistic variations with typos, punctuation differences, etc.
- Assigns transcriptions to different mock users
- Calculates quality and confidence scores
- Triggers consensus calculation automatically

Usage:
    DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
    python generate_mock_transcriptions.py
"""

import json
import os
import random
import re
import string
import sys
from typing import Dict, List

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
MIN_TRANSCRIPTIONS_PER_CHUNK = 5
MAX_TRANSCRIPTIONS_PER_CHUNK = 8
TRANSCRIPTION_VARIATION_RATE = (
    0.05  # 5% of words may be varied (more similar transcriptions)
)


class TranscriptionVariator:
    """Creates realistic variations of transcription text."""

    def __init__(self):
        # Common transcription variations
        self.common_typos = {
            "the": ["teh", "the", "thee"],
            "and": ["and", "an", "nd"],
            "you": ["you", "u", "yu"],
            "your": ["your", "ur", "youre"],
            "there": ["there", "their", "thier"],
            "they": ["they", "thay", "thy"],
            "with": ["with", "wth", "wit"],
            "that": ["that", "tht", "taht"],
            "this": ["this", "ths", "dis"],
            "have": ["have", "hav", "hve"],
            "will": ["will", "wil", "wll"],
            "from": ["from", "frm", "form"],
            "been": ["been", "ben", "bean"],
            "were": ["were", "wer", "where"],
            "said": ["said", "sed", "sayed"],
        }

        # Punctuation variations
        self.punctuation_variations = [
            (".", ""),  # Remove period
            (".", "!"),  # Period to exclamation
            (",", ""),  # Remove comma
            ("?", "."),  # Question to period
            ("'", ""),  # Remove apostrophe
        ]

        # Capitalization variations
        self.capitalization_variations = [
            "lower",  # all lowercase
            "upper",  # ALL UPPERCASE
            "title",  # Title Case
            "sentence",  # Sentence case
        ]

    def create_variation(
        self, original_text: str, variation_level: float = 0.15
    ) -> str:
        """
        Create a realistic variation of the original text.

        Args:
            original_text: The original script text
            variation_level: Fraction of words to potentially modify (0.0-1.0)

        Returns:
            Varied transcription text
        """
        if not original_text.strip():
            return original_text

        words = original_text.split()
        varied_words = []

        for word in words:
            # Clean word (remove punctuation for processing)
            clean_word = re.sub(r"[^\w\s]", "", word.lower())

            # Decide if this word should be varied
            if random.random() < variation_level:
                # Apply variation
                if clean_word in self.common_typos:
                    # Use common typo
                    varied_clean = random.choice(self.common_typos[clean_word])
                else:
                    # Create random typo
                    varied_clean = self._create_random_typo(clean_word)

                # Restore original punctuation and capitalization pattern
                varied_word = self._restore_word_format(word, varied_clean)
                varied_words.append(varied_word)
            else:
                varied_words.append(word)

        # Join words back
        result = " ".join(varied_words)

        # Apply punctuation variations
        if random.random() < 0.3:  # 30% chance
            result = self._vary_punctuation(result)

        # Apply capitalization variations
        if random.random() < 0.2:  # 20% chance
            result = self._vary_capitalization(result)

        return result.strip()

    def _create_random_typo(self, word: str) -> str:
        """Create a random typo in a word."""
        if len(word) < 3:
            return word

        typo_type = random.choice(["swap", "drop", "add", "substitute"])

        if typo_type == "swap" and len(word) > 3:
            # Swap two adjacent characters
            pos = random.randint(0, len(word) - 2)
            chars = list(word)
            chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
            return "".join(chars)

        elif typo_type == "drop" and len(word) > 3:
            # Drop a character
            pos = random.randint(1, len(word) - 2)  # Don't drop first or last
            return word[:pos] + word[pos + 1 :]

        elif typo_type == "add":
            # Add a random character
            pos = random.randint(1, len(word) - 1)
            char = random.choice(string.ascii_lowercase)
            return word[:pos] + char + word[pos:]

        elif typo_type == "substitute":
            # Substitute a character
            pos = random.randint(1, len(word) - 2)  # Don't change first or last
            char = random.choice(string.ascii_lowercase)
            return word[:pos] + char + word[pos + 1 :]

        return word

    def _restore_word_format(self, original: str, varied_clean: str) -> str:
        """Restore punctuation and capitalization from original word."""
        # Extract punctuation
        leading_punct = ""
        trailing_punct = ""

        # Find leading punctuation
        for char in original:
            if char.isalpha():
                break
            leading_punct += char

        # Find trailing punctuation
        for char in reversed(original):
            if char.isalpha():
                break
            trailing_punct = char + trailing_punct

        # Determine capitalization pattern
        original_clean = re.sub(r"[^\w\s]", "", original)
        if original_clean.isupper():
            varied_clean = varied_clean.upper()
        elif original_clean.istitle():
            varied_clean = varied_clean.capitalize()
        elif original_clean and original_clean[0].isupper():
            varied_clean = varied_clean.capitalize()

        return leading_punct + varied_clean + trailing_punct

    def _vary_punctuation(self, text: str) -> str:
        """Apply punctuation variations."""
        for old_punct, new_punct in self.punctuation_variations:
            if random.random() < 0.3:  # 30% chance for each variation
                text = text.replace(old_punct, new_punct)
        return text

    def _vary_capitalization(self, text: str) -> str:
        """Apply capitalization variations."""
        variation = random.choice(self.capitalization_variations)

        if variation == "lower":
            return text.lower()
        elif variation == "upper":
            return text.upper()
        elif variation == "title":
            return text.title()
        elif variation == "sentence":
            # Capitalize first letter of each sentence
            sentences = re.split(r"([.!?]+)", text)
            result = []
            for i, part in enumerate(sentences):
                if i % 2 == 0 and part.strip():  # Text parts (not punctuation)
                    part = part.strip()
                    if part:
                        part = part[0].upper() + part[1:].lower()
                result.append(part)
            return "".join(result)

        return text


class MockTranscriptionGenerator:
    """Generates mock transcriptions for audio chunks."""

    def __init__(self):
        self.db = SessionLocal()
        self.variator = TranscriptionVariator()
        self.mock_users = []
        self._setup_mock_users()

    def _setup_mock_users(self):
        """Create or get mock users for transcriptions."""
        mock_user_data = [
            {"name": "Alice Transcriber", "email": "alice.transcriber@mock.com"},
            {"name": "Bob Listener", "email": "bob.listener@mock.com"},
            {"name": "Carol Typist", "email": "carol.typist@mock.com"},
            {"name": "David Scribe", "email": "david.scribe@mock.com"},
            {"name": "Eva Recorder", "email": "eva.recorder@mock.com"},
            {"name": "Frank Writer", "email": "frank.writer@mock.com"},
            {"name": "Grace Noter", "email": "grace.noter@mock.com"},
            {"name": "Henry Clerk", "email": "henry.clerk@mock.com"},
        ]

        for user_data in mock_user_data:
            # Check if user exists
            result = self.db.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": user_data["email"]},
            ).first()

            if result:
                user_id = result[0]
            else:
                # Create user
                result = self.db.execute(
                    text(
                        """
                        INSERT INTO users (name, email, password_hash, role, meta_data)
                        VALUES (:name, :email, :pwd, :role, :meta)
                        RETURNING id
                    """
                    ),
                    {
                        "name": user_data["name"],
                        "email": user_data["email"],
                        "pwd": "mock_transcriber",
                        "role": "CONTRIBUTOR",
                        "meta": json.dumps(
                            {"mock_user": True, "created_for": "transcription_testing"}
                        ),
                    },
                )
                user_id = result.scalar_one()
                self.db.commit()

            self.mock_users.append(user_id)

        print(f"✓ Set up {len(self.mock_users)} mock users for transcriptions")

    def get_chunks_needing_transcriptions(self) -> List[Dict]:
        """Get audio chunks that need transcriptions."""
        # Find chunks that are ready (from processed recordings) but have < 5 transcriptions
        query = text(
            """
            SELECT
                ac.id as chunk_id,
                ac.recording_id,
                ac.chunk_index,
                ac.duration,
                vr.script_id,
                vr.language_id,
                s.text as script_text,
                COALESCE(t.transcription_count, 0) as current_transcriptions
            FROM audio_chunks ac
            JOIN voice_recordings vr ON ac.recording_id = vr.id
            JOIN scripts s ON vr.script_id = s.id
            LEFT JOIN (
                SELECT chunk_id, COUNT(*) as transcription_count
                FROM transcriptions
                GROUP BY chunk_id
            ) t ON ac.id = t.chunk_id
            WHERE vr.status = 'CHUNKED'
            AND COALESCE(t.transcription_count, 0) < :min_transcriptions
            ORDER BY ac.id
        """
        )

        results = self.db.execute(
            query, {"min_transcriptions": MIN_TRANSCRIPTIONS_PER_CHUNK}
        ).fetchall()

        chunks = []
        for row in results:
            chunks.append(
                {
                    "chunk_id": row.chunk_id,
                    "recording_id": row.recording_id,
                    "chunk_index": row.chunk_index,
                    "duration": row.duration,
                    "script_id": row.script_id,
                    "language_id": row.language_id,
                    "script_text": row.script_text,
                    "current_transcriptions": row.current_transcriptions,
                }
            )

        return chunks

    def generate_transcriptions_for_chunk(self, chunk_info: Dict) -> int:
        """Generate transcriptions for a single chunk."""
        chunk_id = chunk_info["chunk_id"]
        script_text = chunk_info["script_text"]
        language_id = chunk_info["language_id"]
        current_count = chunk_info["current_transcriptions"]

        # Determine how many transcriptions to create
        target_count = random.randint(
            MIN_TRANSCRIPTIONS_PER_CHUNK, MAX_TRANSCRIPTIONS_PER_CHUNK
        )
        needed_count = max(0, target_count - current_count)

        if needed_count == 0:
            return 0

        # Select random users (no duplicates)
        selected_users = random.sample(
            self.mock_users, min(needed_count, len(self.mock_users))
        )

        created_count = 0

        for user_id in selected_users:
            # Create variation of the script text
            variation_level = random.uniform(0.05, 0.25)  # 5-25% variation
            transcription_text = self.variator.create_variation(
                script_text, variation_level
            )

            # Calculate quality and confidence scores
            # Higher similarity to original = higher scores
            similarity = self._calculate_similarity(script_text, transcription_text)
            quality = max(0.3, min(0.95, similarity + random.uniform(-0.1, 0.1)))
            confidence = max(0.4, min(0.9, similarity + random.uniform(-0.05, 0.15)))

            # Insert transcription
            try:
                self.db.execute(
                    text(
                        """
                        INSERT INTO transcriptions (
                            chunk_id, user_id, language_id, text, quality, confidence, meta_data
                        ) VALUES (
                            :chunk_id, :user_id, :language_id, :text, :quality, :confidence, :meta
                        )
                    """
                    ),
                    {
                        "chunk_id": chunk_id,
                        "user_id": user_id,
                        "language_id": language_id,
                        "text": transcription_text,
                        "quality": quality,
                        "confidence": confidence,
                        "meta": json.dumps(
                            {
                                "generated_by": "mock_transcription_generator",
                                "original_similarity": similarity,
                                "variation_level": variation_level,
                                "created_at": "auto",
                            }
                        ),
                    },
                )
                created_count += 1

            except Exception as e:
                print(f"  ⚠️  Failed to create transcription for chunk {chunk_id}: {e}")

        self.db.commit()
        return created_count

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        from difflib import SequenceMatcher

        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def trigger_consensus_calculation(self, chunk_ids: List[int]):
        """Trigger consensus calculation for chunks with new transcriptions."""
        try:
            # Import here to avoid circular imports
            import sys
            from pathlib import Path

            # Add app directory to path
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            app_dir = project_root / "app"
            sys.path.insert(0, str(project_root))

            from app.tasks.audio_processing import calculate_consensus_for_chunks

            # Queue consensus calculation task
            task = calculate_consensus_for_chunks.delay(chunk_ids)
            print(
                f"  🔄 Triggered consensus calculation for {len(chunk_ids)} chunks (task: {task.id})"
            )

        except Exception as e:
            print(f"  ⚠️  Failed to trigger consensus calculation: {e}")
            print(
                "  💡 You can manually run consensus calculation later or use prepare_export_data.py"
            )

    def run_generation(self):
        """Main generation workflow."""
        print("=" * 60)
        print("MOCK TRANSCRIPTION GENERATOR")
        print("=" * 60)

        # Get chunks needing transcriptions
        print("\n🔍 Finding chunks that need transcriptions...")
        chunks = self.get_chunks_needing_transcriptions()

        if not chunks:
            print(
                "✓ No chunks need transcriptions. All chunks have sufficient transcriptions!"
            )
            return

        print(f"Found {len(chunks)} chunks needing transcriptions")

        # Show summary
        total_needed = sum(
            max(0, MIN_TRANSCRIPTIONS_PER_CHUNK - chunk["current_transcriptions"])
            for chunk in chunks
        )
        print(f"Total transcriptions to create: ~{total_needed}")

        # Confirm
        confirm = (
            input(f"\nProceed with generating transcriptions? [Y/n]: ").strip().lower()
        )
        if confirm and confirm not in ["y", "yes"]:
            print("Cancelled.")
            return

        # Generate transcriptions
        print(f"\n📝 Generating transcriptions...")
        total_created = 0
        processed_chunks = []

        progress = tqdm(chunks, desc="Processing chunks", unit="chunk")

        for chunk_info in progress:
            chunk_id = chunk_info["chunk_id"]
            progress.set_description(f"Processing chunk {chunk_id}")

            created_count = self.generate_transcriptions_for_chunk(chunk_info)
            total_created += created_count

            if created_count > 0:
                processed_chunks.append(chunk_id)

            progress.set_postfix({"created": created_count, "total": total_created})

        progress.close()

        print(
            f"\n✅ Successfully created {total_created} transcriptions for {len(processed_chunks)} chunks"
        )

        # Trigger consensus calculation
        if processed_chunks:
            print(f"\n🔄 Triggering consensus calculation...")
            self.trigger_consensus_calculation(processed_chunks)

        print(f"\n{'=' * 60}")
        print("TRANSCRIPTION GENERATION COMPLETE")
        print(f"{'=' * 60}")
        print(f"Chunks processed: {len(processed_chunks)}")
        print(f"Transcriptions created: {total_created}")
        print(f"{'=' * 60}")

    def close(self):
        """Clean up database connection."""
        self.db.close()


def main():
    generator = None
    try:
        generator = MockTranscriptionGenerator()
        generator.run_generation()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
    finally:
        if generator:
            generator.close()


if __name__ == "__main__":
    main()
