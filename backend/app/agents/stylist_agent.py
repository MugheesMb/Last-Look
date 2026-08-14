import json

from app.garment_catalog import GARMENT_CATALOG
from app.llm import llm, parse_llm_json
from app.models import CountdownState

RANK_PROMPT = """You are a color-theory-grounded stylist. Do not invent color \
advice — use ONLY the palette and reasoning given below, which comes from a \
verified color-season reference, not your own judgment.

Color season: {season}
Recommended palette (hex): {palette}
Why this palette: {color_reasoning}
Occasion: {occasion}
{weather_line}
Candidate garments: {candidates}

Rank ALL candidates from best to worst match for this palette and occasion. \
For each, cite which part of the reasoning applies (do not just restate the label). \
If a forecast is given and it genuinely affects practicality (e.g. a heavy structured \
piece in very hot weather, or a light layer in cold/rainy conditions), you may note \
that briefly — don't force a mention if the forecast doesn't actually change anything.

Respond ONLY with JSON, no markdown fences:
{{
  "ranked": [
    {{"label": "...", "reasoning": "one short sentence citing the color reasoning"}},
    ...
  ]
}}
"""


async def stylist_agent(state: CountdownState) -> CountdownState:
    """Ranks all candidates using color-theory grounding. Does NOT call the
    VTO API here — that happens per-candidate in the verifier loop, so we
    only spend API units on candidates we actually show."""
    candidates = GARMENT_CATALOG[state["occasion"]][state["gender"]]
    candidate_desc = json.dumps([{"label": c["label"], "tags": c["tags"]} for c in candidates])
    weather_summary = state.get("weather_summary")
    weather_line = f"Forecast for the event day: {weather_summary}\n" if weather_summary else ""

    response = await llm.ainvoke(
        RANK_PROMPT.format(
            season=state["color_season"],
            palette=state["color_palette"],
            color_reasoning=state["color_reasoning"],
            occasion=state["occasion"],
            weather_line=weather_line,
            candidates=candidate_desc,
        )
    )
    ranked = parse_llm_json(response.content)["ranked"]

    ranked_candidates = []
    for r in ranked:
        # Exact match first, then a forgiving case/whitespace-insensitive
        # match — the LLM occasionally paraphrases a label slightly even
        # when told not to. Skip entries that still don't match rather than
        # crashing the whole request over one bad label (next() with no
        # match raised an unhandled StopIteration here before this fix).
        garment = next((c for c in candidates if c["label"] == r["label"]), None)
        if garment is None:
            garment = next(
                (c for c in candidates if c["label"].strip().lower() == r["label"].strip().lower()),
                None,
            )
        if garment is None:
            print(f"[stylist] LLM returned a label with no catalog match, skipping: {r['label']!r}")
            continue

        ranked_candidates.append(
            {"label": garment["label"], "image_url": garment["image_url"], "reasoning": r["reasoning"]}
        )

    if not ranked_candidates:
        # Every ranked label failed to match — fall back to catalog order
        # rather than leaving the Verifier loop with nothing to try.
        print("[stylist] No ranked labels matched the catalog at all; falling back to catalog order.")
        ranked_candidates = [
            {"label": c["label"], "image_url": c["image_url"], "reasoning": "Selected from the catalog."}
            for c in candidates
        ]

    return {
        "ranked_candidates": ranked_candidates,
        "candidate_index": 0,
        "accepted_outfits": [],
        "verification_attempts": 0,
    }
