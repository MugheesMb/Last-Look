
import re
from urllib.parse import quote_plus

from app.color_utils import best_palette_match, fetch_image_bytes, garment_dominant_color, nearest_color_name
from app.models import CountdownState, VerifiedOutfit
from app.youcam_client import youcam_client

MATCH_THRESHOLD = 90.0  # redmean distance; lower = stricter. Tune after real demo runs.
MAX_ACCEPTED = 2
MAX_ATTEMPTS = 4  # hard stop so a bad palette/catalog combo can't loop forever

# Garment-type keywords to pull out of a label for the shopping query — a
# clean type word ("suit", "dress") is far more useful to a search engine
# than the full descriptive label, which can carry pose/staging notes.
_GARMENT_TYPES = [
    "suit", "blazer", "dress", "blouse", "t-shirt", "tank top", "shirt", "top", "jacket",
]


def _extract_garment_type(label: str) -> str:
    lower = label.lower()
    for word in _GARMENT_TYPES:
        if word in lower:
            return word
    return "outfit"


def build_shop_url(label: str, gender: str, dominant_hex: str | None) -> str:
    """Real shopping search link for the garment. Went through three fixes:
    (1) Google's tbm=shop parameter turned out unreliable — it silently
    dropped from the URL and fell back to plain search, surfacing local
    business listings instead of products, so this now targets Amazon
    search instead, which reliably returns real products for any query.
    (2) the full descriptive label ("Black suit, arms crossed, studio")
    was polluting the query with pose/staging words a shopping search
    doesn't understand. (3) most importantly — once we know the ACTUAL
    verified dominant color of the rendered outfit (from real pixel
    inspection, not the label's guess), the query is built from THAT
    plus a clean garment-type word, which is far more likely to surface
    genuinely similar-colored results than the messy label ever was.
    Falls back to the cleaned label if no verified color is available yet."""
    garment_type = _extract_garment_type(label)

    if dominant_hex:
        color_name = nearest_color_name(dominant_hex)
        query = f"{gender} {color_name} {garment_type}"
    else:
        query = f"{gender} {garment_type}"

    return f"https://www.amazon.com/s?k={quote_plus(query)}"


async def verifier_agent(state: CountdownState) -> CountdownState:
    ranked = state["ranked_candidates"]
    index = state["candidate_index"]
    accepted = list(state["accepted_outfits"])
    attempts = state["verification_attempts"] + 1

    candidate = ranked[index]

    outfit: VerifiedOutfit = {
        "label": candidate["label"],
        "ref_image_url": candidate["image_url"],
        "result_image_url": None,
        "reasoning": candidate["reasoning"],
        "dominant_color": None,
        "match_score": None,
        "verified": False,
        "shop_url": build_shop_url(candidate["label"], state["gender"], None),  # rebuilt below once color is known
    }

    try:
        vto_result = await youcam_client.run_cloth_tryon(
            src_file_id=state["selfie_file_id"],
            ref_file_url=candidate["image_url"],
            # let YouCam auto-detect the garment type — the explicit "top"
            # override here was fighting the client's "auto" default and
            # was itself the actual cause of the InvalidParameters error
        )
        # YouCam nests output under results.url (confirmed for Skin Analysis;
        # the earlier top-level result_url/url guess for the cloth task was
        # never actually verified against a real success — this was the
        # actual bug behind "Preview unavailable" with no error printed,
        # since the task itself was succeeding all along).
        result_url = (vto_result.get("results") or {}).get("url") or vto_result.get("result_url") or vto_result.get("url")
        outfit["result_image_url"] = result_url

        if not result_url:
            print(f"[verifier] cloth task succeeded but no result URL found. Full response: {vto_result}")
        else:
            # One-time investigation: does YouCam's response include a
            # garment mask/region we've been ignoring? Its own engine must
            # segment the garment internally to perform the swap — if that's
            # exposed here, sampling color from an actual mask would be far
            # more reliable than our crop+skin+background heuristics.
            # Remove this once we know either way.
            print(f"[verifier] Full cloth task response (checking for a mask/region field): {vto_result}")

        if result_url:
            image_bytes = await fetch_image_bytes(result_url)
            dom_color = garment_dominant_color(image_bytes)
            _, distance = best_palette_match(dom_color, state["color_palette"])
            outfit["dominant_color"] = dom_color
            outfit["match_score"] = round(distance, 1)
            outfit["verified"] = distance <= MATCH_THRESHOLD
            # Now that we know the actual verified color, rebuild the shop
            # link from that instead of the label guess.
            outfit["shop_url"] = build_shop_url(candidate["label"], state["gender"], dom_color)
    except Exception as e:
        # A failed render/verification just means this candidate doesn't
        # get accepted — the loop moves on rather than crashing the demo.
        # We still print the reason so it's visible in the backend terminal
        # instead of silently producing "Preview unavailable" with no clue why.
        print(f"[verifier] cloth tryon/verification failed for '{candidate['label']}': {e!r}")

    is_last_candidate = (index + 1) >= len(ranked)
    has_render = outfit["result_image_url"] is not None

    if outfit["verified"]:
        # Passed the color-match check outright.
        accepted.append(outfit)
    elif has_render and (attempts >= MAX_ATTEMPTS or is_last_candidate):
        # Didn't verify, but it DID actually render — fine to show as
        # "best available" filler once we're out of budget or candidates.
        accepted.append(outfit)
    elif not accepted and is_last_candidate:
        # Absolute last resort: every single candidate failed to render at
        # all across the whole loop. Show something rather than an empty
        # outfit-picks section, even without an image.
        accepted.append(outfit)
    # Otherwise: this candidate's render totally failed (no image) and we
    # already have at least one real accepted outfit — skip it silently
    # rather than padding the results with a "Preview unavailable" card
    # just because the attempt budget happened to run out on THIS one.

    return {
        "accepted_outfits": accepted,
        "candidate_index": index + 1,
        "verification_attempts": attempts,
    }


def should_continue_verifying(state: CountdownState) -> str:
    """Conditional edge: keep looping until we have 2 accepted outfits,
    run out of candidates, or hit the attempt ceiling."""
    if len(state["accepted_outfits"]) >= MAX_ACCEPTED:
        return "presenter"
    if state["candidate_index"] >= len(state["ranked_candidates"]):
        return "presenter"
    if state["verification_attempts"] >= MAX_ATTEMPTS:
        return "presenter"
    return "verifier"
