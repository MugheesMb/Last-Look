from app.llm import llm, parse_llm_json
from app.models import CountdownState

TIMELINE_PROMPT = """You are a realistic skincare coach. The user has {days} day(s) \
before "{occasion}". Their top skin concerns are: {concerns}.
{weather_line}
Build a short day-by-day micro-routine that is achievable in this exact timeframe. \
Be honest about what's NOT achievable (e.g. don't promise a cleared breakout in 2 \
days) and focus on what visibly helps by the deadline (redness, dullness, puffiness, \
hydration are all fast-moving; deep wrinkles or acne scarring are not). If a forecast \
is given, factor it in where it genuinely matters (heat/humidity → oil control and \
SPF emphasis; cold/dry air → richer moisturizer; rain → lighter, less humidity-prone \
products) — don't force a mention if it doesn't change the advice.

Respond ONLY with JSON, no markdown fences, one entry per day:
{{
  "routine": [
    {{"day": 1, "focus": "...", "actions": ["...", "..."]}},
    ...
  ]
}}
"""


async def timeline_agent(state: CountdownState) -> CountdownState:
    concerns = ", ".join(f"{c['name']} ({c['score']})" for c in state["skin_concerns"])
    weather_summary = state.get("weather_summary")
    weather_line = f"\nForecast for the event day: {weather_summary}\n" if weather_summary else ""

    response = await llm.ainvoke(
        TIMELINE_PROMPT.format(
            days=state["days_until"], occasion=state["occasion"], concerns=concerns, weather_line=weather_line
        )
    )
    parsed = parse_llm_json(response.content)
    return {"routine": parsed["routine"]}
