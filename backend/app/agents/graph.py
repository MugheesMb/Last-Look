from langgraph.graph import END, START, StateGraph

from app.agents.diagnostic_agent import diagnostic_agent
from app.agents.presenter_agent import presenter_agent
from app.agents.stylist_agent import stylist_agent
from app.agents.timeline_agent import timeline_agent
from app.agents.verifier_agent import should_continue_verifying, verifier_agent
from app.agents.weather_agent import weather_agent
from app.models import CountdownState


def build_countdown_graph():
    graph = StateGraph(CountdownState)

    graph.add_node("diagnostic", diagnostic_agent)
    graph.add_node("weather", weather_agent)
    graph.add_node("timeline", timeline_agent)
    graph.add_node("stylist", stylist_agent)
    graph.add_node("verifier", verifier_agent)
    graph.add_node("presenter", presenter_agent)

    # Genuine fan-out: diagnostic (YouCam Skin Analysis) and weather
    # (Open-Meteo) are independent of each other, so they run concurrently
    # from the start. "timeline" fans back in — LangGraph won't run it until
    # BOTH parent nodes have completed.
    graph.add_edge(START, "diagnostic")
    graph.add_edge(START, "weather")
    graph.add_edge("diagnostic", "timeline")
    graph.add_edge("weather", "timeline")

    graph.add_edge("timeline", "stylist")
    graph.add_edge("stylist", "verifier")

    # The other real agentic loop: after each verification attempt, decide
    # whether to try the next ranked candidate (loop back to "verifier") or
    # move on — a genuine conditional graph, not a fixed sequence.
    graph.add_conditional_edges(
        "verifier",
        should_continue_verifying,
        {"verifier": "verifier", "presenter": "presenter"},
    )
    graph.add_edge("presenter", END)

    return graph.compile()


countdown_graph = build_countdown_graph()
