"""
    Human checkpoint node for LangGraph.
    Pauses the graph for human review of scored JDs using interrupt.
    Phase 1 used input() — Phase 2 uses interrupt() which persists state
    and resumes the graph after the human responds.
"""
from langgraph.types import interrupt
from state import LadderState

def human_checkpoint_node(state: LadderState) -> dict:
    """LangGraph node - pause for human approval of scored JDs before gap analysis. """
    scored_jds = state["scored_jds"]
    decision = interrupt({
        "scored_jds": scored_jds,
        "message": "Review scores and approve. Reply with indices e.g. '1, 3' or 'all'."
    })
    if decision == "all":
        approved = scored_jds
    else:
        indicies = [int(x.strip()) - 1 for x in decision.split(",")]
        approved = [scored_jds[i] for i in indicies]
    return {"approved_paths": [jd["path"] for jd in approved]}