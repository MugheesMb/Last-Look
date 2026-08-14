# Last_Look

An agentic event-prep stylist for the YouCam API Skin AI & Apparel VTO Hackathon.

Tell it an occasion and how many days you have — it runs YouCam Skin AI on a
selfie, plans a realistic skincare micro-routine for the timeframe, then
picks and verifies outfits (via YouCam Apparel VTO) that actually match a
color palette grounded in real color-season theory — not an LLM's guess.

## What makes this more than a wrapper

1. **Grounded color reasoning, not LLM improvisation.** `color_theory.py`
   holds a real 4-season color-analysis knowledge base (undertone x depth →
   palette). The Diagnostic agent's undertone/depth reading retrieves a
   season profile from this base; every downstream color decision is
   generated FROM that retrieved data, not invented — a lightweight RAG
   pattern grounding a domain where hallucination is easy and costly (bad
   color advice is immediately, visibly wrong to the user).

2. **A closed verification loop, not a fixed pipeline.** Most VTO demos
   generate an image and call it done. Here, after each candidate is
   rendered via Apparel VTO, the **Verifier agent** downloads the actual
   rendered pixels, extracts the dominant color, and computes its distance
   to the recommended palette (`color_utils.py`). If it doesn't match well
   enough, the graph conditionally loops back and tries the next ranked
   candidate — up to a capped number of attempts. This is a genuine
   LangGraph conditional loop (`agents/graph.py`), driven by evidence the
   Stylist agent's flat-product-photo ranking couldn't have known (VTO
   rendering can shift a garment's on-body appearance from its product
   shot).

## Architecture

- **Backend**: FastAPI + LangGraph, `backend/`
  - Graph (`backend/app/agents/graph.py`):
    `Diagnostic → Timeline → Stylist → Verifier ⟲ (loop) → Presenter`
  - `youcam_client.py` wraps the YouCam S2S REST API (file upload → task → poll)
  - `color_theory.py` — grounded color-season knowledge base (retrieval)
  - `color_utils.py` — pixel-level dominant color + color-distance (verification)
  - Reasoning steps use DeepSeek's chat API via `langchain-openai`'s
    OpenAI-compatible client (`llm.py`) — no AWS account needed
- **Frontend**: Next.js (App Router) + Tailwind, `frontend/`
  - Single page: occasion + days picker, selfie upload, result view showing
    the color palette and each outfit's verified match score

## Setup

### Backend
```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in YOUCAM_API_KEY and DEEPSEEK_API_KEY
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open http://localhost:3000.


