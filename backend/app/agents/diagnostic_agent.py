import json

from app.color_theory import retrieve_season
from app.llm import llm, parse_llm_json
from app.models import CountdownState
from app.youcam_client import youcam_client

INTERPRET_PROMPT = """You are a skincare analyst. Given raw skin analysis scores \
(0-100, higher = healthier) for a person, pick the 2-3 concerns most worth \
addressing.

Raw scores (ui_score, 0-100, higher=healthier): {scores}
Overall skin health score: {overall_score}
Estimated skin age: {skin_age}
Measured undertone: {undertone} (sampled from the actual photo, not a guess)
Measured depth: {depth} (sampled from the actual photo, not a guess)

Respond ONLY with JSON, no markdown fences:
{{
  "top_concerns": [{{"name": "...", "score": 0}}, ...],
  "summary": "one sentence, plain language, no jargon"
}}
"""

# Non-concern keys present in the real Skin Analysis result payload —
# confirmed via live testing. Everything else is a concern dict shaped
# like {"raw_score": ..., "ui_score": ..., "output_mask_name": ...}.
META_KEYS = {"all", "skin_age", "resize_image"}


async def diagnostic_agent(state: CountdownState) -> CountdownState:
    # Uses the dedicated face-focused crop, not the full chest-up selfie —
    # see image_utils.py / main.py for why Skin Analysis gets a different
    # crop than Apparel VTO.
    result = await youcam_client.run_skin_analysis(src_file_id=state["skin_selfie_file_id"])

    raw_scores = {
        key: value["ui_score"]
        for key, value in result.items()
        if key not in META_KEYS and isinstance(value, dict) and "ui_score" in value
    }
    overall_score = result.get("all", {}).get("score")
    skin_age = result.get("skin_age")

    if not raw_scores:
        # Shouldn't happen now that extraction matches the real response
        # shape, but keep this as a safety net in case YouCam changes the
        # payload again.
        print(f"[diagnostic] Couldn't find scores under expected keys. Full result: {result}")

    # Undertone/depth now come from real pixel sampling (main.py /
    # image_utils.py), not the LLM — Skin Analysis returns no tone data at
    # all, and asking the LLM to invent it with zero real signal was why
    # the color season kept coming back the same for every photo.
    undertone = state["measured_undertone"]
    depth = state["measured_depth"]

    response = await llm.ainvoke(
        INTERPRET_PROMPT.format(
            scores=json.dumps(raw_scores),
            overall_score=overall_score,
            skin_age=skin_age,
            undertone=undertone,
            depth=depth,
        )
    )
    parsed = parse_llm_json(response.content)

    # Ground the color palette in real color-season data (retrieval step)
    # rather than letting downstream agents freestyle colors.
    season = retrieve_season(undertone, depth)

    return {
        "skin_concerns": parsed["top_concerns"],
        "skin_tone": undertone,
        "skin_depth": depth,
        "skin_summary": parsed["summary"],
        "color_season": season["name"],
        "color_palette": season["palette"],
        "color_reasoning": season["reasoning"],
    }
