import json
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.agents.graph import countdown_graph
from app.config import settings
from app.image_utils import UnsupportedImageError, crop_for_face, estimate_skin_tone
from app.models import CountdownState, Gender, Occasion
from app.youcam_client import youcam_client

app = FastAPI(title="LastLook API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Human-readable labels for each node, shown live in the frontend's status
# log while the countdown is being built. This is what makes the multi-agent
# pipeline visible to the user instead of a black-box spinner.
NODE_LABELS = {
    "diagnostic": "Analyzing your skin and checking the forecast",
    "timeline": "Building your skincare routine",
    "stylist": "Ranking outfit candidates against your color palette",
    "verifier": "Rendering and color-checking an outfit",
    "presenter": "Writing your LastLook summary",
}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/countdown")
async def create_countdown(
    occasion: Occasion = Form(...),
    gender: Gender = Form(...),
    days_until: int = Form(...),
    location: str = Form(""),
    face_x: float | None = Form(None),
    face_y: float | None = Form(None),
    face_w: float | None = Form(None),
    face_h: float | None = Form(None),
    selfie: UploadFile = File(...),
):
    if days_until < 1 or days_until > 30:
        raise HTTPException(400, "days_until must be between 1 and 30")

    selfie_bytes = await selfie.read()
    suffix = Path(selfie.filename or "selfie.jpg").suffix or ".jpg"

    # Real detected face position from the browser (face-api.js, captured
    # at the moment of a camera photo) — used instead of the blind
    # top-of-frame heuristic when available. Upload flow has no live
    # detection, so this stays None and crop_for_face falls back.
    face_box = None
    if None not in (face_x, face_y, face_w, face_h):
        face_box = {"x": face_x, "y": face_y, "w": face_w, "h": face_h}

    async def event_stream():
        # Upload the full chest-up photo as-is — this is what Apparel VTO
        # uses, since it needs shoulders/chest visible to place a garment.
        yield json.dumps({"type": "progress", "label": "Uploading your photo"}) + "\n"
        selfie_file_id = await youcam_client.upload_bytes(
            "cloth", f"selfie{suffix}", "image/jpeg", selfie_bytes
        )

        # Derive a tighter, face-focused crop from the SAME photo for Skin
        # Analysis — see image_utils.py for why this exists.
        try:
            cropped_bytes = crop_for_face(selfie_bytes, face_box=face_box)
        except UnsupportedImageError as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"
            return
        skin_selfie_file_id = await youcam_client.upload_bytes(
            "skin-analysis", f"selfie-face{suffix}", "image/jpeg", cropped_bytes
        )

        # Real pixel-sampled undertone/depth from the crop — see
        # image_utils.py for why this replaced blind LLM guessing.
        skin_tone = estimate_skin_tone(cropped_bytes)

        initial_state: CountdownState = {
            "occasion": occasion,
            "gender": gender,
            "days_until": days_until,
            "location": location or None,
            "selfie_file_id": selfie_file_id,
            "skin_selfie_file_id": skin_selfie_file_id,
            "measured_undertone": skin_tone["undertone"],
            "measured_depth": skin_tone["depth"],
        }

        final_state: CountdownState = dict(initial_state)
        verifier_pass = 0

        try:
            # stream_mode="values" yields the FULL accumulated state after
            # every node completes (not just a diff), which is both simpler
            # to work with and gives us a ready-made "final_state" for free —
            # whatever was yielded last when the stream ends.
            async for state_snapshot in countdown_graph.astream(initial_state, stream_mode="values"):
                final_state = state_snapshot

                # Figure out which node most recently ran from what's newly
                # present in the state, so we can show a specific label.
                if "accepted_outfits" not in state_snapshot:
                    node = "diagnostic" if "skin_summary" not in state_snapshot else "timeline"
                elif "ranked_candidates" not in state_snapshot or not state_snapshot.get("ranked_candidates"):
                    node = "stylist"
                elif "headline" in state_snapshot:
                    node = "presenter"
                else:
                    node = "verifier"

                label = NODE_LABELS[node]
                if node == "verifier":
                    verifier_pass += 1
                    tried = state_snapshot.get("candidate_index", 0)
                    total = len(state_snapshot.get("ranked_candidates", []))
                    label = f"Rendering and color-checking outfit {tried} of {total}"

                yield json.dumps({"type": "progress", "label": label}) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"
            return

        yield json.dumps({"type": "done", "data": final_state}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
