# Urdu Story GenAI System — Mermaid Diagrams

Use these diagrams in any Mermaid-compatible viewer (e.g., GitHub, VS Code Mermaid extension, mermaid.live).

---

## 1. System Architecture (Component Diagram)

```mermaid
flowchart TB
    subgraph User["👤 User"]
        Browser[Browser]
    end

    subgraph Frontend["Frontend (Vercel)"]
        NextJS[Next.js App]
        UI[ChatGPT-like UI]
        SSE[SSE Client]
    end

    subgraph Backend["Backend (Render/Railway)"]
        FastAPI[FastAPI Service]
        Tokenizer[Word Tokenizer]
        Trigram[Trigram Model]
    end

    subgraph Models["Trained Models"]
        TokenizerJSON[tokenizer.json]
        TrigramJSON[trigram.json]
    end

    subgraph Data["Data Pipeline"]
        Scraper[Web Scraper]
        Preprocess[Preprocessor]
        Corpus[corpus.txt]
    end

    Browser --> NextJS
    NextJS --> UI
    UI --> SSE
    SSE -->|GET /generate/stream| FastAPI
    FastAPI --> Tokenizer
    FastAPI --> Trigram
    Tokenizer --> TokenizerJSON
    Trigram --> TrigramJSON
    Scraper --> Preprocess
    Preprocess --> Corpus
    Corpus --> Tokenizer
    Corpus --> Trigram
```

---

## 2. End-to-End Request Flow (Sequence Diagram)

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant T as Tokenizer
    participant M as Trigram Model

    U->>F: Enter prefix "ایک بار ایک بادشاہ تھا"
    U->>F: Click "کہانی بنائیں"
    F->>B: GET /generate/stream?prefix=...
    B->>T: encode(prefix)
    T-->>B: [token_ids]
    loop Until <EOT> or max_length
        B->>M: generate_next_token(w1, w2, temp)
        M-->>B: next_token
        B->>T: decode(generated_tokens)
        B->>F: SSE: {"text": "..."}
        F->>U: Display streaming text
    end
    B->>F: SSE: {"done": true}
```

---

## 3. Training Pipeline Flow

```mermaid
flowchart LR
    subgraph Phase1["Phase I: Data"]
        A1[Raw HTML] --> A2[Scraper]
        A2 --> A3[stories.json]
        A3 --> A4[Preprocessor]
        A4 --> A5[corpus.txt]
    end

    subgraph Phase2["Phase II: Tokenizer"]
        B1[corpus.txt] --> B2[WordTokenizer.train]
        B2 --> B3[tokenizer.json]
    end

    subgraph Phase3["Phase III: Model"]
        C1[corpus.txt] --> C2[Tokenizer.encode]
        C2 --> C3[Tokenized Corpus]
        C3 --> C4[TrigramModel.train]
        C4 --> C5[trigram.json]
    end

    A5 --> B1
    A5 --> C1
    B3 --> C2
```

---

## 4. Trigram Generation Loop

```mermaid
flowchart TD
    Start([Prefix: "ایک بار"]) --> Encode[Tokenizer.encode]
    Encode --> Tokens[prefix_tokens: w1, w2]
    Tokens --> Loop{len < max_length?}
    Loop -->|Yes| Context[Get context: w1=last-2, w2=last-1]
    Context --> Prob[Compute P(w3|w1,w2) for all candidates]
    Prob --> Temp[Apply temperature sampling]
    Temp --> Sample[Sample next_token]
    Sample --> Append[Append to generated]
    Append --> Check{next_token == EOT?}
    Check -->|Yes| Decode[Tokenizer.decode]
    Check -->|No| Loop
    Loop -->|No| Decode
    Decode --> Output([Story text])
```

---

## 5. Preprocessing Pipeline

```mermaid
flowchart TD
    Raw[Raw Story HTML] --> HTML[Remove HTML tags]
    HTML --> Zero[Remove zero-width chars]
    Zero --> Eng[Remove English blocks]
    Eng --> NonUrdu[Remove non-Urdu chars]
    NonUrdu --> Unicode[Normalize Unicode NFC]
    Unicode --> Punct[Standardize punctuation]
    Punct --> WS[Normalize whitespace]
    WS --> Special[Insert EOS, EOP tokens]
    Special --> Filter{Quality filters}
    Filter -->|Pass| EOT[Append EOT token]
    Filter -->|Fail| Skip[Skip story]
    EOT --> Corpus[Write to corpus.txt]
```

---

## 6. High-Level Phase Overview

```mermaid
flowchart TB
    P1[Phase I: Data Collection & Preprocessing]
    P2[Phase II: Tokenizer Training]
    P3[Phase III: Trigram Model Training]
    P4[Phase IV: Backend Microservice]
    P5[Phase V: Frontend UI]
    P6[Phase VI: Cloud Deployment]

    P1 --> P2
    P2 --> P3
    P3 --> P4
    P4 --> P5
    P5 --> P6
```
