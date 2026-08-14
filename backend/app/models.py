from typing import Literal, TypedDict

Occasion = Literal["interview", "first_date", "wedding_guest"]
Gender = Literal["women", "men"]


class SkinConcern(TypedDict):
    name: str
    score: int  # 0-100, higher = healthier for ui_score


class RoutineDay(TypedDict):
    day: int
    focus: str
    actions: list[str]


class RankedCandidate(TypedDict):
    label: str
    image_url: str
    reasoning: str


class VerifiedOutfit(TypedDict):
    label: str
    ref_image_url: str
    result_image_url: str | None
    reasoning: str
    dominant_color: str | None
    match_score: float | None  # lower = better color match
    verified: bool
    shop_url: str  # retailer search link for this garment


class CountdownState(TypedDict, total=False):
    # inputs
    occasion: Occasion
    gender: Gender
    days_until: int
    location: str | None  # optional city, used for weather grounding
    selfie_file_id: str  # full chest-up photo, used for Apparel VTO
    skin_selfie_file_id: str  # tighter face-focused crop of the same photo, used for Skin Analysis

    # weather agent output (runs in parallel with diagnostic)
    weather_summary: str | None

    # real pixel-sampled undertone/depth from the face crop — grounds the
    # color season in the actual photo instead of an LLM guessing blind
    # (YouCam's Skin Analysis returns no tone data at all)
    measured_undertone: str  # warm | cool | neutral
    measured_depth: str  # light | medium | deep

    # diagnostic agent output
    skin_concerns: list[SkinConcern]
    skin_tone: str  # warm | cool | neutral
    skin_depth: str  # light | medium | deep
    skin_summary: str

    # color theory retrieval (grounding)
    color_season: str
    color_palette: list[str]
    color_reasoning: str

    # timeline agent output
    routine: list[RoutineDay]

    # stylist ranking + verifier loop state
    ranked_candidates: list[RankedCandidate]
    candidate_index: int
    accepted_outfits: list[VerifiedOutfit]
    verification_attempts: int

    # presenter agent output
    headline: str
    final_summary: str
