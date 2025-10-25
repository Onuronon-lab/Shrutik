# Database Design & Field Rationale (for Annotator)

## 🧭 Overview — goals & assumptions

**Primary goal:** store voice contributions and transcriptions in a way that is:

- easy to query for training pipelines,
- supports multiple transcriptions per chunk (crowdsourced labels),
- allows validation/quality control,
- language-aware and extensible.

**DB choice recommendation:** PostgreSQL (good text support, JSONB, concurrency, reliability).

---

## 📦 Entities & Rationale (table-by-table)

### `users`

**Why:** track people who record or transcribe; minimal auth/profile info.
**Core use cases:** attribution, quality control, reviewer reputation, limiting tasks per user.

Fields:

- `id SERIAL PRIMARY KEY` — unique identifier.
- `name VARCHAR` — display name.
- `email VARCHAR UNIQUE` — contact & unique login identifier (optional if using OAuth).
- `role VARCHAR` — `recorder`, `transcriber`, `reviewer`, `admin`. Keep roles flexible.
- `metadata JSONB` — optional free-form info (region/accent, device info) — useful for analysis.
- `created_at TIMESTAMP DEFAULT now()` — registration time.

Notes:

- Index `email`.
- Consider a `reputation_score` or `trust_level` later for weighting transcriptions.

---

### `languages`

**Why:** multi-language support (Bangla, English, etc.). Keeps schema normalized and extensible.
Fields:

- `id SERIAL PRIMARY KEY`
- `name VARCHAR` — "Bengali", "English"
- `code VARCHAR` — "bn", "en"
- `created_at TIMESTAMP`

Notes:

- Populate early with languages you’ll support.
- Use `code` in user-facing forms and model pipelines.

---

### `scripts`

**Why:** text snippets you give voice contributors to read. Helps manage content, fairness, duration buckets.
**Core use cases:** give randomized scripts for balanced dataset, record provenance to script.

Fields:

- `id SERIAL PRIMARY KEY`
- `text TEXT` — the script content
- `duration_category VARCHAR` — e.g. `2min`, `5min`, `10min` (helps routing)
- `language_id INT REFERENCES languages(id)`
- `metadata JSONB` — license, author, reading difficulty, domain (news, fiction)
- `created_at TIMESTAMP`

Notes:

- Scripts can be reused across recordings; store them here for traceability and to avoid duplicates.

---

### `voice_recordings`

**Why:** a single uploaded recording (one user reading one script). This is the _unit of upload_.
**Core use cases:** trace chunks back to original recording and speaker; apply processing tasks (VAD, normalization).

Fields:

- `id SERIAL PRIMARY KEY`
- `user_id INT REFERENCES users(id)` — who uploaded / recorded
- `script_id INT REFERENCES scripts(id)` — which script was read (nullable if user reads free-form)
- `file_path TEXT` — storage pointer (S3 URL, GCS, or local path)
- `duration INT` — seconds (for quick queries)
- `language_id INT REFERENCES languages(id)` — helps route chunking & transcription
- `status VARCHAR` — `uploaded`, `processed`, `failed`, `chunked`
- `metadata JSONB` — device info, mic type, sample_rate, bit_depth, loudness stats
- `created_at TIMESTAMP`

Notes:

- Index on `status` for background workers.
- Store heavy blobs in object storage; keep only URIs here.

---

### `audio_chunks`

**Why:** smallest audio unit for transcription. Ideally sentence-level (or intelligible short segments). Each recording spawns many chunks.
**Core use cases:** training pairs (`chunk_file` <-> `transcription`), random sampling for annotators, QC pipeline.

Fields:

- `id SERIAL PRIMARY KEY`
- `recording_id INT REFERENCES voice_recordings(id)`
- `chunk_index INT` — ordering inside recording (0, 1, 2...)
- `file_path TEXT` — chunk file (S3/GCS/local path)
- `start_time REAL` — seconds offset in original recording
- `end_time REAL`
- `duration REAL` — redundant but convenient
- `sentence_hint TEXT` — optional auto-alignment output or ASR suggestion (used for intelligent chunking)
- `metadata JSONB` — VAD confidence, silence_ratio, energy, language_prob
- `created_at TIMESTAMP`

Notes:

- Index on `(recording_id, chunk_index)` for fast retrieval.
- `sentence_hint` can store the before/after text if you run forced-alignment later.

---

### `transcriptions`

**Why:** store human-written transcripts for chunks. We keep many per chunk for reliability & consensus.
**Core use cases:** generate training labels, measure inter-annotator agreement, feed validation models.

Fields:

- `id SERIAL PRIMARY KEY`
- `chunk_id INT REFERENCES audio_chunks(id)`
- `user_id INT REFERENCES users(id)` — who transcribed
- `text TEXT` — the transcript (utf-8)
- `language_id INT REFERENCES languages(id)` — in case transcribers specify dialect
- `quality VARCHAR` — `unverified`, `verified`, `flagged`
- `confidence REAL` — optional (if annotator or auto-ASR provides a confidence)
- `created_at TIMESTAMP`

Notes:

- Index `chunk_id` for aggregating all transcripts of a chunk.
- Keep transcripts immutable (create new rows for edits); use `quality` or `validations` for QA.

---

### `quality_reviews` (aka `validations`)

**Why:** peer-review / QA. Instead of trusting single transcriber, others can mark correctness, rate quality, or flag issues.
Fields:

- `id SERIAL PRIMARY KEY`
- `transcription_id INT REFERENCES transcriptions(id)`
- `reviewer_id INT REFERENCES users(id)`
- `decision VARCHAR` — `correct` / `incorrect` / `needs_edit`
- `rating INT` — optional 1–5
- `comment TEXT`
- `created_at TIMESTAMP`

Notes:

- Use votes to compute final `verified` status for a transcription (e.g., 2 consistent `correct` votes -> verified).
- Keep reviewer actions auditable.

---

## 🔁 Relationships (summary)

- `users` 1—∞ `voice_recordings`
- `scripts` 1—∞ `voice_recordings`
- `voice_recordings` 1—∞ `audio_chunks`
- `audio_chunks` 1—∞ `transcriptions`
- `transcriptions` 1—∞ `quality_reviews`
- `languages` referenced by several tables

---

## 🔧 Implementation Details & SQL (Postgres-ready)

Below is a concise example DDL for core tables. Tweak datatypes / names to match your style.

> **Tip:** keep `metadata JSONB` fields for experimental metrics (VAD confidence, ASR suggestions, mic info). Postgres `JSONB` indexes are great for later analytics.

```sql
-- users
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(200),
  email VARCHAR(200) UNIQUE,
  role VARCHAR(50),
  metadata JSONB,
  created_at TIMESTAMP DEFAULT now()
);

-- languages
CREATE TABLE languages (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  code VARCHAR(10),
  created_at TIMESTAMP DEFAULT now()
);

-- scripts
CREATE TABLE scripts (
  id SERIAL PRIMARY KEY,
  text TEXT NOT NULL,
  duration_category VARCHAR(20),
  language_id INT REFERENCES languages(id),
  metadata JSONB,
  created_at TIMESTAMP DEFAULT now()
);

-- voice_recordings
CREATE TABLE voice_recordings (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  script_id INT REFERENCES scripts(id),
  file_path TEXT NOT NULL,
  duration INT,
  language_id INT REFERENCES languages(id),
  status VARCHAR(50) DEFAULT 'uploaded',
  metadata JSONB,
  created_at TIMESTAMP DEFAULT now()
);

-- audio_chunks
CREATE TABLE audio_chunks (
  id SERIAL PRIMARY KEY,
  recording_id INT REFERENCES voice_recordings(id),
  chunk_index INT,
  file_path TEXT,
  start_time REAL,
  end_time REAL,
  duration REAL,
  sentence_hint TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT now()
);

-- transcriptions
CREATE TABLE transcriptions (
  id SERIAL PRIMARY KEY,
  chunk_id INT REFERENCES audio_chunks(id),
  user_id INT REFERENCES users(id),
  text TEXT NOT NULL,
  language_id INT REFERENCES languages(id),
  quality VARCHAR(50) DEFAULT 'unverified',
  confidence REAL,
  created_at TIMESTAMP DEFAULT now()
);

-- quality_reviews
CREATE TABLE quality_reviews (
  id SERIAL PRIMARY KEY,
  transcription_id INT REFERENCES transcriptions(id),
  reviewer_id INT REFERENCES users(id),
  decision VARCHAR(50),
  rating INT,
  comment TEXT,
  created_at TIMESTAMP DEFAULT now()
);
```

Suggested indexes:

- `CREATE INDEX idx_chunks_recording ON audio_chunks(recording_id, chunk_index);`
- `CREATE INDEX idx_trans_chunk ON transcriptions(chunk_id);`
- `CREATE INDEX idx_recordings_status ON voice_recordings(status);`

---

## 🔬 Sample queries (real-world use)

- Fetch untranscribed chunks to assign to annotators:

```sql
SELECT ac.* FROM audio_chunks ac
LEFT JOIN (
  SELECT chunk_id, COUNT(*) AS tcount FROM transcriptions GROUP BY chunk_id
) t ON ac.id = t.chunk_id
WHERE COALESCE(t.tcount,0) = 0
LIMIT 200;
```

- Get consensus (simple): choose transcription with most `quality='verified'` votes:

```sql
SELECT t.*, COUNT(q.id) as votes
FROM transcriptions t
LEFT JOIN quality_reviews q ON q.transcription_id = t.id AND q.decision='correct'
WHERE t.chunk_id = $CHUNK_ID
GROUP BY t.id
ORDER BY votes DESC
LIMIT 1;
```

- Find recordings by language or status:

```sql
SELECT * FROM voice_recordings WHERE language_id = $LANG AND status = 'chunked';
```

---

## 🔁 Intelligent chunking & alignment (design note)

You mentioned "intelligent" chunks that avoid cutting mid-sentence. Implementation approaches:

1. **VAD + silence thresholds** (fast): detect silence to split near pauses. Use `silero-vad` or `webrtcvad`.
2. **ASR + forced alignment** (higher quality): run an ASR/light model to get timestamps for sentences, or use forced-aligners (Montreal Forced Aligner) to split at sentence boundaries. Store results in `sentence_hint`.
3. **Hybrid:** VAD → initial splits; for long sentences, run alignment to merge/split chunks intelligently.

Store churned chunk metadata (`metadata JSONB`) with `vad_confidence`, `sentence_prob`, `merged_from` etc., so later you can analyze chunk quality.

---

## 📈 Scaling & infra recommendations

- **Storage:** audio blobs in object storage (S3/GCS). Keep URIs in DB. Don’t store binary in DB.
- **Workers:** use background workers (Celery/RQ) to handle chunking, normalization, forced alignment.
- **Batching & QC:** keep multiple transcriptions per chunk; resolve via voting or weighted consensus (using `reviewer` trust levels).
- **Rate limits / quotas:** protect against spam: limit recordings per user per day, require audio validation (min SNR).

---

## 🔒 Privacy & compliance

- Keep personal data minimal. If storing emails, secure them and plan for delete requests.
- Consent: record agreement from contributors to use voice for training. Store consent in `users.metadata` or a `consents` table.
- Consider hashing user identifiers in exported datasets when used outside Onuronon infra.

---

## ✅ Next steps & checklist

- [ ] Create migrations (Flyway / Alembic) and seed `languages`.
- [ ] Implement chunking worker that writes `audio_chunks` rows and uploads chunk files to object storage.
- [ ] Build simple API endpoints to fetch random chunk for annotator, post transcription, and post review.
- [ ] Add telemetry (counts per language, average chunk duration) to `metadata` for analytics.

---
