This diagram shows the *entire pipeline*: from users contributing data to how it’s chunked, transcribed, validated, and stored for Sworik.

---

```mermaid
flowchart TD

subgraph A["Voice Collection"]
    A1["User chooses a script length (2/5/10 mins)"]
    A2["Random Bangla script assigned"]
    A3["User records audio in browser/app"]
    A4["Audio uploaded to server"]
    A1 --> A2 --> A3 --> A4
end

subgraph B["Smart Chunking Engine"]
    B1["Run silence & sentence boundary detection"]
    B2["Split into clean chunks (per sentence)"]
    B3["Store each chunk with metadata (duration, timestamps)"]
    A4 --> B1 --> B2 --> B3
end

subgraph C["Transcription Interface"]
    C1["User selects number of sentences to transcribe"]
    C2["Random unverified chunks served"]
    C3["User listens & types transcript"]
    C4["Submit transcription"]
    C1 --> C2 --> C3 --> C4
end

subgraph D["Verification System"]
    D1["Multiple transcriptions per chunk compared"]
    D2["Consensus algorithm decides accuracy"]
    D3["Flag inconsistent transcriptions for review"]
    C4 --> D1 --> D2 --> D3
end

subgraph E["Database & Storage"]
    E1["Users Table"]
    E2["Recordings Table (raw audio)"]
    E3["Chunks Table"]
    E4["Transcriptions Table"]
    E5["Scripts Table"]
    E6["Metadata + Flags Table"]
    B3 --> E3
    D2 --> E4
    A4 --> E2
end

subgraph F["Training Data Export"]
    F1["Validated Chunks + Transcripts"]
    F2["Export dataset for Sworik model training"]
    E4 --> F1 --> F2
end

subgraph G["Web Platform"]
    G1["Frontend: React/Svelte + Tailwind"]
    G2["Backend: Go (Fiber/Gin) + PostgreSQL"]
    G3["Storage: MinIO / S3 / GCS"]
    G4["Auth: OAuth + JWT + Roles"]
    G1 --> G2 --> G3 --> G4
end

subgraph H["Admin Dashboard"]
    H1["Monitor contribution progress"]
    H2["Approve / reject submissions"]
    H3["View stats (contributors, hours, accuracy)"]
    H1 --> H2 --> H3
end

%% Data Flow Arrows
A --> B --> C --> D --> E --> F
G --> A
G --> C
G --> H
```

---

### 💡 Explanation

* **A → B → C → D → E → F**
  This is your *data journey*:
  recording → smart chunking → transcription → verification → database → export for training.

* **G** (Web Platform) ties everything together - UI, backend, and storage.

* **H** (Admin Dashboard) ensures quality control and community contribution tracking.

