"""
Phase 2 orchestrator — LangGraph StateGraph.

Replaces the manual agent chain from Phase 1 with a compiled graph:
  scraper → analyst → human_checkpoint → gap_analyser → study_updater

The human_checkpoint node uses interrupt() to pause the graph and wait for
human input. MemorySaver persists state across the interrupt so the graph
can resume exactly where it left off.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from state import LadderState
from nodes.scraper import scraper_node
from nodes.analyst import analyst_node
from nodes.human_checkpoint import human_checkpoint_node
from nodes.gap_analyser import gap_analyst_node
from nodes.study_updater import study_updater_node

# --- Build the graph ---
builder = StateGraph(LadderState)

builder.add_node("scraper", scraper_node)
builder.add_node("analyst", analyst_node)
builder.add_node("human_checkpoint", human_checkpoint_node)
builder.add_node("gap_analyser", gap_analyst_node)
builder.add_node("study_updater", study_updater_node)

builder.add_edge(START, "scraper")
builder.add_edge("scraper", "analyst")
builder.add_edge("analyst", "human_checkpoint")
builder.add_edge("human_checkpoint", "gap_analyser")
builder.add_edge("gap_analyser", "study_updater")
builder.add_edge("study_updater", END)

# MemorySaver is required for interrupt() to persist state between runs
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# --- Visualise the graph ---
graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
print("Graph saved to graph.png")
print("Graph mermaid code:\n")
print(graph.get_graph().draw_mermaid())

# --- Run the graph ---
if __name__ == "__main__":
    # thread_id lets MemorySaver identify this run — required for interrupt/resume
    config = {"configurable": {"thread_id": "ladder-run-1"}}

    initial_state = {
        "search_query": "Senior AI Engineer UK or Ireland remote",
        "messages": [],
        "scored_jds": [],
        "approved_paths": [],
        "gap_report_path": "",
    }

    print("\n=== LADDER — PHASE 2 ===\n")

    # Stream events until the graph hits interrupt() or finishes
    for event in graph.stream(initial_state, config=config, stream_mode="updates"):
        node_name = list(event.keys())[0]
        print(f"[{node_name}] done")

    # Check if the graph is paused at the human checkpoint
    snapshot = graph.get_state(config)
    if snapshot.next:
        # Graph is interrupted — show scored JDs to the human
        interrupted_state = snapshot.values
        scored_jds = interrupted_state.get("scored_jds", [])

        print("\n=== RANKED JDs — REVIEW AND APPROVE ===\n")
        for i, jd in enumerate(scored_jds):
            print(f"[{i+1}] {jd.get('score', '?'):>3}/100  {jd.get('title', '?')} @ {jd.get('company', '?')}")
            print(f"      {jd.get('reasoning', '')}\n")

        print("Type the numbers to approve, e.g: 1,3  or 'all'")
        user_input = input("Approve: ").strip().lower()

        # Resume the graph by passing the human's decision as the interrupt value
        # Command(resume=...) is how LangGraph resumes after an interrupt()
        for event in graph.stream(
            Command(resume=user_input),
            config=config,
            stream_mode="updates"
        ):
            node_name = list(event.keys())[0]
            print(f"[{node_name}] done")

    print("\n=== PIPELINE COMPLETE ===")
    print("gap_report.md and study_plan.md updated.")
