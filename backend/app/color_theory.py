"""
Lightweight retrieval-augmented grounding for color recommendations.

Instead of letting the LLM freely improvise "warm tones suit you" (which
sounds plausible but is frequently wrong), we retrieve a structured
color-season profile from real color-theory data and pass THAT into the
prompt as grounding context. The LLM's job becomes reasoning over verified
facts, not inventing them — this is the same retrieval-then-generate
pattern as document RAG, just over a small structured knowledge base
instead of a vector store (appropriate given the fixed, well-defined
domain — 4 seasons, not an open corpus).

Simplified 4-season color analysis model (undertone x depth):
"""

SEASON_PALETTES: dict[str, dict] = {
    "spring": {  # warm + light
        "undertone": "warm",
        "depth": "light",
        "palette": ["#FF6F61", "#FFD166", "#06D6A0", "#FFA69E", "#F4E285"],
        "avoid": ["#000000", "#4B0082", "#708090"],
        "reasoning": (
            "Warm, light undertones are flattered by clear, warm colors "
            "with a golden base. Heavy black or icy jewel tones tend to "
            "overpower rather than complement."
        ),
    },
    "summer": {  # cool + light
        "undertone": "cool",
        "depth": "light",
        "palette": ["#A8DADC", "#B2A4D4", "#F4A6A6", "#8ECAE6", "#D6C9E8"],
        "avoid": ["#FF8C00", "#B8860B", "#8B0000"],
        "reasoning": (
            "Cool, light undertones pair best with soft, muted colors with "
            "a blue base. Strong orange-based warm tones tend to clash."
        ),
    },
    "autumn": {  # warm + deep
        "undertone": "warm",
        "depth": "deep",
        "palette": ["#B5651D", "#6B4226", "#8A9A5B", "#C08552", "#7B3F00"],
        "avoid": ["#FF69B4", "#C0C0C0", "#000080"],
        "reasoning": (
            "Warm, deep undertones suit rich, earthy colors with a golden "
            "or red base. Cool pastels or silvery tones tend to wash out "
            "against this depth."
        ),
    },
    "winter": {  # cool + deep
        "undertone": "cool",
        "depth": "deep",
        "palette": ["#0B3D91", "#5C0029", "#0F4C3A", "#1B1B1B", "#7A0C2E"],
        "avoid": ["#F4E285", "#DEB887", "#FFDAB9"],
        "reasoning": (
            "Cool, deep undertones are flattered by bold, saturated colors "
            "with a blue base and high contrast. Muted earthy warm tones "
            "tend to look dull against this depth."
        ),
    },
}


def retrieve_season(undertone: str, depth: str) -> dict:
    """Retrieve the closest matching season profile for a given undertone/depth.
    Returns the season dict with a 'name' key added."""
    undertone = undertone.lower().strip()
    depth = depth.lower().strip()

    for name, season in SEASON_PALETTES.items():
        if season["undertone"] == undertone and season["depth"] == depth:
            return {**season, "name": name}

    # neutral undertone or unrecognized depth: fall back to the closest
    # depth match within a sensible default, rather than erroring out mid-demo
    fallback_undertone = "warm" if undertone not in ("warm", "cool") else undertone
    for name, season in SEASON_PALETTES.items():
        if season["undertone"] == fallback_undertone:
            return {**season, "name": name}

    return {**SEASON_PALETTES["autumn"], "name": "autumn"}
