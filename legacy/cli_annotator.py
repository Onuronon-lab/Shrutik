import os
import subprocess
import sounddevice as sd
import soundfile as sf
import ffmpeg
import json

# === CONFIG ===
AUDIO_PATH = "input_audio.mp3"   # your main audio file
OUTPUT_DIR = "chunks"
CHUNK_DURATION = 5               # seconds per chunk
PROGRESS_FILE = "progress.json"  # stores your progress
ANNOTATION_FILE = "annotations.txt"


# === STEP 1: Split audio using ffmpeg ===
def split_audio_ffmpeg(input_path, output_dir, chunk_length):
    os.makedirs(output_dir, exist_ok=True)
    try:
        (
            ffmpeg
            .input(input_path)
            .output(f"{output_dir}/chunk_%03d.wav", f="segment", segment_time=chunk_length, reset_timestamps=1)
            .run(quiet=True, overwrite_output=True)
        )
        print(f"✅ Audio split into {chunk_length}-second chunks at '{output_dir}'")
    except ffmpeg.Error as e:
        print("❌ FFmpeg error:", e)
        raise


# === STEP 2: Load / Save Progress ===
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed": []}

def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# === STEP 3: Annotate chunks with replay + skip + resume ===
def annotate_chunks(directory):
    annotations = {}
    files = sorted([f for f in os.listdir(directory) if f.endswith(".wav")])

    progress = load_progress()
    completed = set(progress["completed"])

    print(f"\n🔁 Resuming progress... {len(completed)} chunks already done.\n")

    for f in files:
        if f in completed:
            continue  # skip already done chunks

        filepath = os.path.join(directory, f)
        print(f"\n🎧 Now playing: {f}")

        # Load and play chunk
        data, samplerate = sf.read(filepath)

        while True:
            sd.play(data, samplerate)
            sd.wait()

            text = input("✍️ Type what you hear ('r' = replay, 's' = skip, 'q' = quit): ").strip()

            if text.lower() == "r":
                print("🔁 Replaying...")
                continue
            elif text.lower() == "s":
                print("⏭️ Skipped this chunk.")
                progress["completed"].append(f)
                save_progress(progress)
                break
            elif text.lower() == "q":
                print("\n🛑 Quitting safely... your progress is saved.")
                save_progress(progress)
                return annotations  # exit cleanly
            elif text == "":
                print("⚠️ Please type something, or use 'r'/'s'/'q'.")
                continue
            else:
                annotations[f] = text

                # Save immediately after every transcription
                with open(ANNOTATION_FILE, "a", encoding="utf-8") as out:
                    out.write(f"{f}: {text}\n")

                progress["completed"].append(f)
                save_progress(progress)
                print("✅ Saved!")
                break
    
    print("\n🎉 Annotation complete! All transcripts saved in", ANNOTATION_FILE)
    return annotations


# === MAIN ===
if __name__ == "__main__":
    # Only split if chunks folder is empty
    if not os.path.exists(OUTPUT_DIR) or not os.listdir(OUTPUT_DIR):
        split_audio_ffmpeg(AUDIO_PATH, OUTPUT_DIR, CHUNK_DURATION)
    else:
        print(f"📂 Using existing chunks in '{OUTPUT_DIR}'")

    annotate_chunks(OUTPUT_DIR)

