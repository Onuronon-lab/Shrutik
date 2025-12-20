#!/usr/bin/env python3
"""
generate_test_data.py - Enhanced version with user prompts and unique content generation

Features:
- Interactive prompts for script counts
- Dependency checking with installation instructions
- Automatic database setup (language, user)
- Unique, non-repetitive script generation using varied templates and content pools

Usage:
    DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
    python generate_test_data.py
"""

import asyncio
import json
import os
import random
import socket
import string
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

from tqdm import tqdm


# ----------------- DEPENDENCY CHECKING -----------------
def check_dependencies():
    """Check if required packages are installed and provide installation instructions."""
    required_packages = {
        "sqlalchemy": "sqlalchemy",
        "aiohttp": "aiohttp",
        "tqdm": "tqdm",
    }

    # Check for at least one TTS backend
    tts_available = False
    try:
        import edge_tts  # noqa: F401

        tts_available = True
    except ImportError:
        pass

    if not tts_available:
        try:
            import gtts  # noqa: F401

            tts_available = True
        except ImportError:
            pass

    if not tts_available:
        required_packages["gtts"] = "gtts"  # Add gtts as fallback

    missing = []
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)

    if missing:
        print("=" * 60)
        print("ERROR: Missing required dependencies!")
        print("=" * 60)
        print("\nPlease install the following packages:\n")
        print("1. Activate your virtual environment (if using one):")
        print("   source venv/bin/activate  # Linux/Mac")
        print("   venv\\Scripts\\activate     # Windows\n")
        print("2. Install missing packages:")
        print(f"   pip install {' '.join(missing)}\n")
        print("=" * 60)
        sys.exit(1)


check_dependencies()

import aiohttp
from aiohttp import TCPConnector

# Import TTS libraries - prefer Edge TTS, fallback to Google TTS
EDGE_TTS_AVAILABLE = False
GTTS_AVAILABLE = False

try:
    import edge_tts  # noqa: F401

    EDGE_TTS_AVAILABLE = True
    print("✓ Edge TTS available")
except ImportError:
    print("⚠️  Edge TTS not available")

try:
    from gtts import gTTS  # noqa: F401

    GTTS_AVAILABLE = True
    print("✓ Google TTS available")
except ImportError:
    print("⚠️  Google TTS not available")

if not EDGE_TTS_AVAILABLE and not GTTS_AVAILABLE:
    print("ERROR: No TTS backend available. Install at least one:")
    print("  pip install edge-tts")
    print("  pip install gtts")
    sys.exit(1)

# Now import after checking
from sqlalchemy import create_engine, text

# ----------------- CONFIG -----------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: Please set DATABASE_URL environment variable.")
    print(
        "Example: DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection"
    )
    sys.exit(1)

# Output directory - defaults to uploads/generated_audio relative to project root
# Can be overridden with AUDIO_OUTPUT_DIR environment variable
AUDIO_OUTPUT_DIR = os.getenv("AUDIO_OUTPUT_DIR")
if AUDIO_OUTPUT_DIR:
    OUT_DIR = Path(AUDIO_OUTPUT_DIR)
else:
    # Find project root (parent of mock-test-generator-scripts or current dir if not in that folder)
    script_dir = Path(__file__).parent
    if script_dir.name == "mock-test-generator-scripts":
        project_root = script_dir.parent
    else:
        project_root = Path.cwd()
    OUT_DIR = project_root / "uploads" / "generated_audio"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Duration mappings
DURATIONS = {
    "SHORT": 120,  # 2 minutes
    "MEDIUM": 300,  # 5 minutes
    "LONG": 600,  # 10 minutes
}

# Approximate words for durations (adjusted for TTS speed ~120 WPM)
TARGET_WORDS = {
    "SHORT": 240,  # 2 minutes at 120 WPM
    "MEDIUM": 600,  # 5 minutes at 120 WPM
    "LONG": 1200,  # 10 minutes at 120 WPM
}

# TTS settings
TTS_VOICE = "en-US-JennyNeural"
TTS_RATE = "+0%"  # Ensure proper format

# DB helper user/email
AUTO_USER = {
    "name": "auto_importer",
    "email": "auto_import@example.com",
    "password_hash": "auto",
}
LANG_NAME = "English"
LANG_CODE = "en"

# Concurrency settings
CONCURRENCY = 2
SESSION_RESTART_EVERY = 40
FFMPEG_CONCURRENCY = 1

# TTS retry settings
TTS_MAX_RETRIES = 3
TTS_RETRY_BASE_SECONDS = 1.0

# Compression/audio settings
OPUS_BITRATE = "48k"

# ----------------- UNIQUE CONTENT GENERATION -----------------


class UniqueContentGenerator:
    """Generates human-like, narrative-driven motivational content with natural flow."""

    def __init__(self):
        # Import content library
        import sys
        from pathlib import Path

        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))

        try:
            from content_library import (
                CHALLENGES,
                CLOSINGS,
                ENCOURAGEMENT,
                EXAMPLES,
                INSIGHTS,
                OBSERVATIONS,
                OPENINGS,
                QUESTIONS,
                REFLECTIONS,
                TRANSITIONS,
            )

            self.openings = OPENINGS.copy()
            self.insights = INSIGHTS.copy()
            self.examples = EXAMPLES.copy()
            self.transitions = TRANSITIONS.copy()
            self.challenges = CHALLENGES.copy()
            self.encouragement = ENCOURAGEMENT.copy()
            self.reflections = REFLECTIONS.copy()
            self.closings = CLOSINGS.copy()
            self.questions = QUESTIONS.copy()
            self.observations = OBSERVATIONS.copy()
        except ImportError:
            # Fallback if library not found
            self.openings = ["Let's talk about growth."]
            self.insights = ["Progress takes time."]
            self.examples = ["Consider learning anything new."]
            self.transitions = ["Here's why."]
            self.challenges = ["It's not easy."]
            self.encouragement = ["But you can do it."]
            self.reflections = ["Think about your journey."]
            self.closings = ["Keep going."]
            self.questions = ["What will you do next?"]
            self.observations = ["Everyone starts somewhere."]

        # Global tracking
        self.used_content: Set[str] = set()

    def _get_unique_from_pool(self, pool: List[str]) -> str:
        """Get unique item from pool, removing it to prevent reuse."""
        if not pool:
            return "The journey continues."
        item = random.choice(pool)
        pool.remove(item)
        return item

    def generate_unique_script(self, word_target: int) -> str:
        """Generate a narrative-driven script with natural flow."""
        if word_target < 50:
            raise ValueError(f"Word target too small: {word_target}")

        sections = []
        current_words = 0

        # 1. Opening (grab attention)
        opening = self._get_unique_from_pool(self.openings)
        if not opening:
            opening = "Let's talk about growth and improvement."
        sections.append(opening)
        current_words += len(opening.split())

        # 2. Initial insight
        insight1 = self._get_unique_from_pool(self.insights)
        sections.append(insight1)
        current_words += len(insight1.split())

        # 3. Build the body with varied rhythm
        max_iterations = 1000  # Safety limit to prevent infinite loops
        iterations = 0

        while current_words < word_target * 0.85 and iterations < max_iterations:
            iterations += 1

            # Check if all pools are exhausted
            all_pools_empty = not any(
                [
                    self.transitions,
                    self.examples,
                    self.insights,
                    self.observations,
                    self.challenges,
                    self.encouragement,
                    self.questions,
                    self.reflections,
                ]
            )

            if all_pools_empty:
                break

            # Vary the pattern
            pattern = random.choice(
                [
                    ["transition", "example", "insight"],
                    ["observation", "challenge", "encouragement"],
                    ["question", "reflection", "insight"],
                    ["insight", "example", "observation"],
                    ["challenge", "encouragement", "reflection"],
                ]
            )

            for content_type in pattern:
                if current_words >= word_target * 0.85:
                    break

                content = None
                if content_type == "transition" and self.transitions:
                    content = self._get_unique_from_pool(self.transitions)
                elif content_type == "example" and self.examples:
                    content = self._get_unique_from_pool(self.examples)
                elif content_type == "insight" and self.insights:
                    content = self._get_unique_from_pool(self.insights)
                elif content_type == "observation" and self.observations:
                    content = self._get_unique_from_pool(self.observations)
                elif content_type == "challenge" and self.challenges:
                    content = self._get_unique_from_pool(self.challenges)
                elif content_type == "encouragement" and self.encouragement:
                    content = self._get_unique_from_pool(self.encouragement)
                elif content_type == "question" and self.questions:
                    content = self._get_unique_from_pool(self.questions)
                elif content_type == "reflection" and self.reflections:
                    content = self._get_unique_from_pool(self.reflections)

                if content:
                    sections.append(content)
                    current_words += len(content.split())

        # 4. Closing (memorable ending)
        if self.closings:
            closing = self._get_unique_from_pool(self.closings)
            sections.append(closing)

        # Assemble with natural paragraph breaks
        # Group 2-3 sentences per paragraph for natural rhythm
        paragraphs = []
        i = 0
        while i < len(sections):
            para_size = random.randint(2, 3)
            paragraph = " ".join(sections[i : i + para_size])
            paragraphs.append(paragraph)
            i += para_size

        full_text = "\n\n".join(paragraphs)

        # Trim to word count if needed (keep complete sentences)
        words = full_text.split()
        if len(words) > word_target:
            trimmed = " ".join(words[:word_target])
            last_period = trimmed.rfind(".")
            if last_period > 0:
                full_text = trimmed[: last_period + 1]

        # Validate final output
        final_words = len(full_text.split())
        if final_words < 20:
            raise ValueError(f"Generated script too short: {final_words} words")

        if len(full_text.strip()) < 100:
            raise ValueError(f"Generated script too short: {len(full_text)} characters")

        return full_text


# Global content generator
content_generator = UniqueContentGenerator()

# ----------------- UTILITY FUNCTIONS -----------------


def has_binary(name: str) -> bool:
    """Check if a binary is available in PATH."""
    try:
        subprocess.run(
            [name, "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception:
        return False


FFMPEG_AVAILABLE = has_binary("ffmpeg") and has_binary("ffprobe")


def random_suffix(n=6):
    """Generate random suffix for filenames."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def get_user_input() -> Dict[str, int]:
    """Prompt user for how many scripts to generate for each duration."""
    print("\n" + "=" * 60)
    print("VOICE DATA GENERATION SCRIPT")
    print("=" * 60)
    print("\nThis script will generate motivational scripts and synthesize audio.")
    print("Each script will be unique with no repetitive content.\n")

    counts = {}
    for duration_key, seconds in DURATIONS.items():
        minutes = seconds // 60
        while True:
            try:
                prompt = f"How many {minutes}-minute ({duration_key}) scripts? [default: 0]: "
                user_input = input(prompt).strip()
                count = int(user_input) if user_input else 0
                if count < 0:
                    print("Please enter a non-negative number.")
                    continue
                counts[duration_key] = count
                break
            except ValueError:
                print("Invalid input. Please enter a number.")

    total = sum(counts.values())
    if total == 0:
        print("\nNo scripts to generate. Exiting.")
        sys.exit(0)

    print(f"\n{'=' * 60}")
    print(f"Total scripts to generate: {total}")
    for duration_key, count in counts.items():
        if count > 0:
            print(f"  - {duration_key}: {count}")
    print(f"{'=' * 60}\n")

    confirm = input("Proceed? [Y/n]: ").strip().lower()
    if confirm and confirm not in ["y", "yes"]:
        print("Cancelled.")
        sys.exit(0)

    return counts


# ----------------- DATABASE FUNCTIONS -----------------

engine = create_engine(DATABASE_URL, future=True)


async def run_subprocess(cmd: list, check: bool = True, capture_output: bool = False):
    """Run blocking subprocess in threadpool."""

    def _run():
        return subprocess.run(
            cmd,
            check=check,
            stdout=(subprocess.PIPE if capture_output else None),
            stderr=(subprocess.PIPE if capture_output else None),
        )

    return await asyncio.to_thread(_run)


async def convert_to_webm(
    tmp_mp3: Path, out_webm: Path, ffmpeg_semaphore: asyncio.Semaphore
) -> Path:
    """Convert mp3 -> webm/opus using ffmpeg."""
    if not FFMPEG_AVAILABLE:
        return tmp_mp3
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(tmp_mp3),
        "-c:a",
        "libopus",
        "-b:a",
        OPUS_BITRATE,
        "-vbr",
        "on",
        str(out_webm),
    ]
    async with ffmpeg_semaphore:
        try:
            await run_subprocess(cmd, check=True)
            tmp_mp3.unlink(missing_ok=True)
            return out_webm
        except Exception:
            return tmp_mp3


def measure_duration_seconds_sync(path: Path) -> Optional[float]:
    """Measure audio duration using ffprobe."""
    if not FFMPEG_AVAILABLE:
        return None
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        s = proc.stdout.strip()
        return float(s) if s else None
    except Exception:
        return None


async def measure_duration_seconds(path: Path) -> Optional[float]:
    """Async wrapper for duration measurement."""
    return await asyncio.to_thread(measure_duration_seconds_sync, path)


def db_ensure_language_and_user_sync(connection, lang_code, lang_name, auto_user):
    """Ensure language and user exist in database."""
    # Ensure language
    r = connection.execute(
        text("SELECT id FROM languages WHERE code = :code LIMIT 1"), {"code": lang_code}
    ).first()
    if r:
        language_id = r[0]
        print(f"✓ Language '{lang_name}' already exists (id={language_id})")
    else:
        res = connection.execute(
            text(
                "INSERT INTO languages (name, code) VALUES (:name, :code) RETURNING id"
            ),
            {"name": lang_name, "code": lang_code},
        )
        language_id = res.scalar_one()
        print(f"✓ Created language '{lang_name}' (id={language_id})")

    # Ensure user
    r2 = connection.execute(
        text("SELECT id FROM users WHERE email = :email LIMIT 1"),
        {"email": auto_user["email"]},
    ).first()
    if r2:
        user_id = r2[0]
        print(f"✓ User '{auto_user['name']}' already exists (id={user_id})")
    else:
        res = connection.execute(
            text(
                "INSERT INTO users (name, email, password_hash, role, meta_data) "
                "VALUES (:name, :email, :pwd, :role, :meta) RETURNING id"
            ),
            {
                "name": auto_user["name"],
                "email": auto_user["email"],
                "pwd": auto_user["password_hash"],
                "role": "SWORIK_DEVELOPER",
                "meta": json.dumps({"auto_created": True}),
            },
        )
        user_id = res.scalar_one()
        print(f"✓ Created user '{auto_user['name']}' (id={user_id})")

    return language_id, user_id


async def ensure_language_and_user():
    """Async wrapper for database setup."""

    def _work():
        with engine.begin() as conn:
            return db_ensure_language_and_user_sync(
                conn, LANG_CODE, LANG_NAME, AUTO_USER
            )

    return await asyncio.to_thread(_work)


async def db_insert_script(
    text_body: str, duration_key: str, language_id: int, meta: dict
) -> int:
    """Insert script into database."""

    def _work():
        with engine.begin() as conn:
            res = conn.execute(
                text(
                    "INSERT INTO scripts (text, duration_category, language_id, meta_data) "
                    "VALUES (:text, :dur, :lang, :meta) RETURNING id"
                ),
                {
                    "text": text_body,
                    "dur": duration_key,
                    "lang": language_id,
                    "meta": json.dumps(meta),
                },
            )
            return res.scalar_one()

    return await asyncio.to_thread(_work)


async def db_insert_recording(
    user_id: int,
    script_id: int,
    language_id: int,
    file_path: str,
    duration_seconds: float,
    meta: dict,
) -> int:
    """Insert voice recording into database."""

    def _work():
        with engine.begin() as conn:
            res = conn.execute(
                text(
                    "INSERT INTO voice_recordings (user_id, script_id, language_id, file_path, duration, status, meta_data) "
                    "VALUES (:uid, :sid, :lid, :fp, :dur, :status, :meta) RETURNING id"
                ),
                {
                    "uid": user_id,
                    "sid": script_id,
                    "lid": language_id,
                    "fp": file_path,
                    "dur": duration_seconds,
                    "status": "UPLOADED",
                    "meta": json.dumps(meta),
                },
            )
            return res.scalar_one()

    return await asyncio.to_thread(_work)


# ----------------- TTS SYNTHESIS -----------------


async def synthesize_tts_with_retries(
    text: str,
    out_path: Path,
    session: aiohttp.ClientSession,
    retries: int = TTS_MAX_RETRIES,
) -> Path:
    """Synthesize speech with retry logic. Try Edge TTS first, fallback to Google TTS."""
    tmp_mp3 = out_path.with_suffix(".mp3")

    # Validate text length
    if len(text.strip()) < 10:
        raise ValueError(f"Text too short for TTS: {len(text)} characters")

    # Try Edge TTS first if available
    if EDGE_TTS_AVAILABLE:
        print(f"  🎤 Trying Edge TTS for {out_path.name}...")
        for attempt in range(1, retries + 1):
            try:
                print(f"    Edge TTS attempt {attempt}/{retries}...")
                comm = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE)
                await comm.save(str(tmp_mp3))

                # Verify the file was created and has content
                if tmp_mp3.exists() and tmp_mp3.stat().st_size > 1000:  # At least 1KB
                    print(f"    ✅ Edge TTS successful: {tmp_mp3.stat().st_size} bytes")
                    return tmp_mp3
                else:
                    raise RuntimeError(
                        f"Edge TTS output file too small: {tmp_mp3.stat().st_size if tmp_mp3.exists() else 0} bytes"
                    )

            except Exception as exc:
                print(f"    ⚠️  Edge TTS error (attempt {attempt}): {exc}")
                if attempt < retries:
                    sleep_for = TTS_RETRY_BASE_SECONDS * (2 ** (attempt - 1))
                    print(f"    Retrying in {sleep_for}s...")
                    await asyncio.sleep(sleep_for)
                continue

        print(f"  ❌ Edge TTS failed after {retries} attempts, trying Google TTS...")

    # Fallback to Google TTS if Edge TTS failed or not available
    if GTTS_AVAILABLE:
        print(f"  🎤 Trying Google TTS for {out_path.name}...")
        for attempt in range(1, retries + 1):
            try:
                print(f"    Google TTS attempt {attempt}/{retries}...")

                # Google TTS is synchronous, run in thread pool
                def _gtts_sync():
                    tts = gTTS(text=text, lang="en", slow=False)
                    tts.save(str(tmp_mp3))

                await asyncio.to_thread(_gtts_sync)

                # Verify the file was created and has content
                if tmp_mp3.exists() and tmp_mp3.stat().st_size > 1000:  # At least 1KB
                    print(
                        f"    ✅ Google TTS successful: {tmp_mp3.stat().st_size} bytes"
                    )
                    return tmp_mp3
                else:
                    raise RuntimeError(
                        f"Google TTS output file too small: {tmp_mp3.stat().st_size if tmp_mp3.exists() else 0} bytes"
                    )

            except Exception as exc:
                print(f"    ⚠️  Google TTS error (attempt {attempt}): {exc}")
                if attempt < retries:
                    sleep_for = TTS_RETRY_BASE_SECONDS * (2 ** (attempt - 1))
                    print(f"    Retrying in {sleep_for}s...")
                    await asyncio.sleep(sleep_for)
                continue

    # If we get here, both TTS backends failed
    error_msg = f"All TTS backends failed after {retries} attempts each"
    print(f"  ❌ {error_msg}")
    raise RuntimeError(error_msg)


# ----------------- MAIN GENERATION -----------------


async def test_tts_connectivity():
    """Test TTS services before starting generation. Try Edge TTS first, fallback to Google TTS."""
    print("🔍 Testing TTS connectivity...")
    test_text = "This is a test of the text to speech service."
    test_file = OUT_DIR / "tts_test.mp3"

    # Try Edge TTS first if available
    if EDGE_TTS_AVAILABLE:
        print("  Testing Edge TTS...")
        try:
            comm = edge_tts.Communicate(test_text, TTS_VOICE, rate=TTS_RATE)
            await comm.save(str(test_file))

            if test_file.exists() and test_file.stat().st_size > 1000:
                print(f"  ✅ Edge TTS working: {test_file.stat().st_size} bytes")
                test_file.unlink()  # Clean up
                return True
            else:
                print(
                    f"  ❌ Edge TTS failed: file too small ({test_file.stat().st_size if test_file.exists() else 0} bytes)"
                )
        except Exception as e:
            print(f"  ❌ Edge TTS failed: {e}")

    # Try Google TTS if Edge TTS failed or not available
    if GTTS_AVAILABLE:
        print("  Testing Google TTS...")
        try:

            def _gtts_sync():
                tts = gTTS(text=test_text, lang="en", slow=False)
                tts.save(str(test_file))

            await asyncio.to_thread(_gtts_sync)

            if test_file.exists() and test_file.stat().st_size > 1000:
                print(f"  ✅ Google TTS working: {test_file.stat().st_size} bytes")
                test_file.unlink()  # Clean up
                return True
            else:
                print(
                    f"  ❌ Google TTS failed: file too small ({test_file.stat().st_size if test_file.exists() else 0} bytes)"
                )
        except Exception as e:
            print(f"  ❌ Google TTS failed: {e}")

    print("❌ All TTS services failed")
    return False


async def run_generation():
    """Main generation workflow."""
    # Test TTS first
    if not await test_tts_connectivity():
        print("\n❌ TTS service is not working. Please check your internet connection.")
        print("   Edge TTS requires internet access to Microsoft's speech service.")
        return []

    # Get user input
    counts = get_user_input()

    # Setup aiohttp session
    connector = TCPConnector(family=socket.AF_INET, limit_per_host=CONCURRENCY + 2)
    session = aiohttp.ClientSession(connector=connector)
    ffmpeg_semaphore = asyncio.Semaphore(FFMPEG_CONCURRENCY)

    # Ensure database setup
    print("\nSetting up database...")
    language_id, user_id = await ensure_language_and_user()
    print(f"\nUsing language_id={language_id}, user_id={user_id}\n")

    semaphore = asyncio.Semaphore(CONCURRENCY)
    total_jobs = sum(counts.values())

    async def process_single(duration_key: str, idx: int, task_i: int):
        async with semaphore:
            title = f"{duration_key.lower()}_motivation_{idx}_{random_suffix(5)}"
            target_words = TARGET_WORDS[duration_key]

            # Generate unique script
            text_body = content_generator.generate_unique_script(target_words)
            actual_words = len(text_body.split())
            print(
                f"  📄 Generated script: {actual_words} words (target: {target_words})"
            )
            print(f"  📄 Preview: {text_body[:150]}...")

            # Insert script
            try:
                script_meta = {"generated_by": "generate_test_data_v2", "title": title}
                script_id = await db_insert_script(
                    text_body, duration_key, language_id, script_meta
                )
            except Exception as e:
                print(f"[ERROR] Failed to insert script (title={title}): {e}")
                raise

            # Synthesize TTS
            outname = OUT_DIR / f"script_{script_id}_{duration_key}_{idx}"
            print(
                f"  📝 Generating audio for script {script_id} ({len(text_body.split())} words)..."
            )

            try:
                tmp_mp3 = await synthesize_tts_with_retries(text_body, outname, session)
            except Exception as e:
                print(f"[ERROR] TTS completely failed for script_id={script_id}: {e}")
                print(f"[ERROR] Script text preview: {text_body[:200]}...")
                # Don't create fallback - let the error propagate so we can fix the issue
                raise

            # Convert to webm
            final_audio_path = tmp_mp3
            if FFMPEG_AVAILABLE:
                target_webm = outname.with_suffix(".webm")
                final_audio_path = await convert_to_webm(
                    tmp_mp3, target_webm, ffmpeg_semaphore
                )

            # Measure duration
            measured = await measure_duration_seconds(final_audio_path)
            duration_seconds = measured if measured else float(DURATIONS[duration_key])

            # Insert recording with Docker-compatible path
            # Convert host path to Docker container path
            # Host: /home/user/project/uploads/generated_audio/file.webm
            # Docker: /app/uploads/generated_audio/file.webm
            try:
                # Get relative path from project root
                relative_path = final_audio_path.relative_to(OUT_DIR.parent.parent)
                docker_path = f"/app/{relative_path}"

                meta = {
                    "generated_by": "generate_test_data_v2",
                    "path_type": final_audio_path.suffix.replace(".", ""),
                }
                recording_id = await db_insert_recording(
                    user_id, script_id, language_id, docker_path, duration_seconds, meta
                )
            except Exception as e:
                print(
                    f"[ERROR] Failed to insert recording for script_id={script_id}: {e}"
                )
                raise

            return {
                "script_id": script_id,
                "recording_id": recording_id,
                "file": str(final_audio_path),
                "duration": duration_seconds,
            }

    # Execute tasks
    results = []
    progress = tqdm(total=total_jobs, desc="Generating", unit="script")

    task_counter = 0
    batch_size = 8
    todo_coros = []

    for duration_key, count in counts.items():
        if count == 0:
            continue
        for i in range(1, count + 1):
            task_counter += 1
            todo_coros.append(process_single(duration_key, i, task_counter))

            if len(todo_coros) >= batch_size:
                done = await asyncio.gather(*todo_coros, return_exceptions=True)
                for d in done:
                    if isinstance(d, Exception):
                        print(f"[WARN] Task failed: {d}")
                    else:
                        results.append(d)
                    progress.update(1)
                todo_coros = []

            # Periodic session restart
            if task_counter % SESSION_RESTART_EVERY == 0:
                try:
                    await session.close()
                except Exception:
                    pass
                connector = TCPConnector(
                    family=socket.AF_INET, limit_per_host=CONCURRENCY + 2
                )
                session = aiohttp.ClientSession(connector=connector)

    # Process remaining
    if todo_coros:
        done = await asyncio.gather(*todo_coros, return_exceptions=True)
        for d in done:
            if isinstance(d, Exception):
                print(f"[WARN] Task failed: {d}")
            else:
                results.append(d)
            progress.update(1)

    progress.close()

    try:
        await session.close()
    except Exception:
        pass

    print(f"\n{'=' * 60}")
    print(f"✓ Successfully created {len(results)} recordings (requested {total_jobs})")
    print(f"✓ Audio files saved to: {OUT_DIR.absolute()}")
    print(f"{'=' * 60}\n")

    return results


if __name__ == "__main__":
    try:
        asyncio.run(run_generation())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nERROR: {e}")
        raise
