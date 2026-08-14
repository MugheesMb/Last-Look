from app.llm import llm, parse_llm_json
from app.models import CountdownState

PRESENT_PROMPT = """Write the copy for a "Countdown" card shown to a user preparing \
for "{occasion}" in {days} day(s).

Skin summary: {skin_summary}
Color season: {season} ({color_reasoning})
Outfit picks (verified color match): {outfits}
{weather_line}
Respond ONLY with JSON, no markdown fences:
{{
  "headline": "punchy one-liner, under 12 words",
  "final_summary": "2-3 warm, encouraging sentences tying the skin plan, color season, and outfit pick together — weave in the forecast only if it's given and genuinely relevant"
}}
"""


async def presenter_agent(state: CountdownState) -> CountdownState:
    outfits = ", ".join(o["label"] for o in state["accepted_outfits"])
    weather_summary = state.get("weather_summary")
    weather_line = f"Forecast for the event day: {weather_summary}\n" if weather_summary else ""

    response = await llm.ainvoke(
        PRESENT_PROMPT.format(
            occasion=state["occasion"],
            days=state["days_until"],
            skin_summary=state["skin_summary"],
            season=state["color_season"],
            color_reasoning=state["color_reasoning"],
            outfits=outfits,
            weather_line=weather_line,
        )
    )
    parsed = parse_llm_json(response.content)
    return {"headline": parsed["headline"], "final_summary": parsed["final_summary"]}
