# Phase 2 — Frameworks + Multi-Agent: Step-by-Step Guide
> Project: Ladder v2 — Rebuild the Job Hunting Agent in LangGraph
> Duration: 3 weeks | Goal: Replace all manual wiring from Phase 1 with LangGraph

---

## The Golden Rule

You already built this pipeline by hand. Phase 2 is not about building something new — it is about rebuilding the same thing with LangGraph so you feel exactly what the framework gives you.

Every time LangGraph makes something easier, ask yourself: *how did I do this manually in Phase 1?* That comparison is the learning.

---

## What You Are Rebuilding

The same 4-agent Ladder pipeline:

```
Orchestrator (main.py)
    ↓
Agent 1 — Job Scraper      (web_search → scrape_page → save_jd)
    ↓
Agent 2 — JD Analyst       (list_jds → read_jd → score → save_scored_jds)
    ↓
Human Checkpoint            (review scores, approve shortlist)
    ↓
Agent 3 — Gap Analyser     (read_jd → read_profile → write_gap_report)
    ↓
Agent 4 — Study Updater    (read_file → append_to_study_plan)
```

What changes is the wiring — not the agents or tools themselves.

---

## Phase 1 vs Phase 2 — Side by Side

| Phase 1 (raw API) | Phase 2 (LangGraph) |
|---|---|
| `state = {}` plain dict | `TypedDict` state schema |
| `while True` ReAct loop | LangGraph node |
| Manual message passing | LangGraph edges |
| `if response.stop_reason == "tool_use"` | `ToolNode` handles this |
| `human_checkpoint()` function | `interrupt` node |
| Manual agent chaining in `main.py` | Graph edges define the flow |

---

## Week 3 — LangGraph Fundamentals

### Day 1–2: Understand the Core Concepts

**Goal:** Know what a node, edge, and state graph are before writing any code.

Read these — 2 hours max total:
- LangGraph quickstart (official docs)
- "Why LangGraph" section — focus on state management and human-in-the-loop
- LangGraph `interrupt` and `Command` docs

Key concepts to understand:
- **State** — a `TypedDict` that flows through the graph. Every node reads from it and writes to it.
- **Node** — a Python function that takes state and returns updated state. Each agent becomes a node.
- **Edge** — defines which node runs next. Can be fixed (`add_edge`) or conditional (`add_conditional_edges`).
- **ToolNode** — a built-in LangGraph node that executes tool calls automatically. Replaces your `if tool_name == "web_search"` dispatch logic.

### Day 3: Define the State Schema

**Goal:** Replace the plain dict with a typed state schema.

Phase 1:
```python
state = {
    "search_query": "Senior AI Engineer UK",
    "scored_jds": [],
    "approved_paths": [],
    "gap_report_path": "",
}
```

Phase 2:
```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class LadderState(TypedDict):
    search_query: str
    messages: Annotated[list, add_messages]  # agent message history
    scored_jds: list[dict]
    approved_paths: list[str]
    gap_report_path: str
```

The `messages` field with `add_messages` is important — LangGraph uses it to accumulate the conversation history for each agent automatically.

### Day 4–5: Convert Agent 1 to a LangGraph Node

**Goal:** Replace the `while True` loop in `scraper.py` with a LangGraph node.

Phase 1 — `run_scraper_agent()` was a standalone function with a manual loop.

Phase 2 — it becomes a node:

```python
from langgraph.prebuilt import create_react_agent
from tools.web_tools import web_search, scrape_page
from tools.file_tools import save_jd

# create_react_agent replaces your entire while True loop
scraper_agent = create_react_agent(
    model="claude-haiku-4-5-20251001",
    tools=[web_search, scrape_page, save_jd],
    prompt=(
        "You are a job scraping agent. Search once, scrape each result, "
        "save each job using save_jd, then stop."
    )
)

def scraper_node(state: LadderState) -> LadderState:
    result = scraper_agent.invoke({"messages": [("user", state["search_query"])]})
    return {"messages": result["messages"]}
```

Notice: `create_react_agent` replaces your entire `while True` ReAct loop. That is the core value of LangGraph.

---

## Week 4 — Convert All Agents + Human Checkpoint

### Day 1–2: Convert Agents 2, 3, and 4

Repeat the same pattern for each agent — wrap it in `create_react_agent` and expose it as a node function.

Agent 2 node:
```python
from tools.file_tools import list_jds, read_jd, save_scored_jds

analyst_agent = create_react_agent(
    model="claude-haiku-4-5-20251001",
    tools=[list_jds, read_jd, save_scored_jds],
    prompt="You are a JD analyst. List all JDs, read each one, score against the profile, save results, then stop."
)

def analyst_node(state: LadderState) -> LadderState:
    result = analyst_agent.invoke({"messages": [("user", "Analyse and score all saved JDs.")]})
    # Parse scored_jds from result and update state
    return {"messages": result["messages"]}
```

Do the same for Agent 3 (`gap_analyser_node`) and Agent 4 (`study_updater_node`).

### Day 3: Replace human_checkpoint() with interrupt

**Goal:** Replace your manual `input()` checkpoint with LangGraph's built-in `interrupt`.

Phase 1:
```python
def human_checkpoint(scored_jds):
    user_input = input("Approve: ").strip()
    ...
```

Phase 2:
```python
from langgraph.types import interrupt, Command

def human_checkpoint_node(state: LadderState) -> LadderState:
    # Pause the graph and surface the scored JDs to the human
    decision = interrupt({
        "scored_jds": state["scored_jds"],
        "message": "Review scores and approve. Reply with indices e.g. '1,3' or 'all'."
    })
    # Resume here after human responds
    if decision == "all":
        approved = state["scored_jds"]
    else:
        indices = [int(x.strip()) - 1 for x in decision.split(",")]
        approved = [state["scored_jds"][i] for i in indices]

    return {"approved_paths": [jd["path"] for jd in approved]}
```

The key difference: `interrupt` pauses the entire graph execution and persists state to a checkpointer. When the human responds, the graph resumes exactly where it left off. Your Phase 1 version had no persistence — if the process crashed, you lost all progress.

### Day 4–5: Wire the Graph in main.py

**Goal:** Replace the manual agent chain in `main.py` with a LangGraph graph.

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Build the graph
builder = StateGraph(LadderState)

# Add nodes
builder.add_node("scraper", scraper_node)
builder.add_node("analyst", analyst_node)
builder.add_node("human_checkpoint", human_checkpoint_node)
builder.add_node("gap_analyser", gap_analyser_node)
builder.add_node("study_updater", study_updater_node)

# Add edges — defines the flow
builder.set_entry_point("scraper")
builder.add_edge("scraper", "analyst")
builder.add_edge("analyst", "human_checkpoint")
builder.add_edge("human_checkpoint", "gap_analyser")
builder.add_edge("gap_analyser", "study_updater")
builder.add_edge("study_updater", END)

# Compile with a checkpointer (enables interrupt to work)
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# Run it
config = {"configurable": {"thread_id": "run-1"}}
graph.invoke({"search_query": "Senior AI Engineer UK"}, config=config)
```

Compare this to Phase 1's `main.py` — the graph replaces all the manual chaining.

---

## Week 5 — MCP Server + Graph Visualisation

### Day 1–3: Visualise the Graph

LangGraph can render your pipeline as a diagram:

```python
print(graph.get_graph().draw_mermaid())
```

This outputs a Mermaid diagram you can paste into any Mermaid renderer. Add this to your README — it is a strong portfolio piece that makes the architecture immediately understandable to interviewers.

### Day 4–5: Build an MCP Server for the Scraper Tools

**Goal:** Expose `web_search` and `scrape_page` as an MCP server. Connect it to the LangGraph agent as MCP tools instead of importing them directly.

This replaces:
```python
from tools.web_tools import web_search, scrape_page
```

With a proper MCP protocol where tools are served over a standard interface.

Steps:
1. Read the Anthropic MCP quickstart docs
2. Create `mcp_server.py` — expose `web_search` and `scrape_page` as MCP tools
3. Update Agent 1 to connect to the MCP server and call tools via the protocol
4. Confirm the behaviour is identical to Phase 1

**Why this matters:** MCP is the emerging standard for agent tool protocols. Building a server (not just using one) is a strong signal to interviewers that you understand the full stack.

---

## Key Concepts Learned in Phase 2

| Concept | Where you encounter it |
|---|---|
| Typed state graphs | `LadderState` TypedDict |
| Node/edge architecture | Graph definition in `main.py` |
| `create_react_agent` | Each agent node |
| `ToolNode` | Auto tool dispatch |
| `interrupt` + `Command` | Human checkpoint node |
| Checkpointing + persistence | `MemorySaver` |
| Graph visualisation | `draw_mermaid()` |
| MCP protocol | `mcp_server.py` |

---

## Folder Structure

```
ladder-v2/
├── main.py                  # graph definition + entry point
├── state.py                 # LadderState TypedDict
├── nodes/
│   ├── scraper.py           # scraper_node
│   ├── analyst.py           # analyst_node
│   ├── human_checkpoint.py  # human_checkpoint_node
│   ├── gap_analyser.py      # gap_analyser_node
│   └── study_updater.py     # study_updater_node
├── tools/
│   ├── web_tools.py         # unchanged from Phase 1
│   └── file_tools.py        # unchanged from Phase 1
├── mcp_server.py            # MCP server exposing web_search + scrape_page
└── requirements.txt
```

Note: `tools/` is unchanged. You are reusing everything you built in Phase 1 — only the wiring changes.

---

## Definition of Done

- [ ] All 4 agents converted to LangGraph nodes
- [ ] Human checkpoint uses `interrupt` instead of `input()`
- [ ] Graph runs end-to-end: search → scrape → score → approve → gap report → study plan updated
- [ ] Graph diagram rendered with `draw_mermaid()` and added to README
- [ ] MCP server created for `web_search` and `scrape_page`
- [ ] Agent 1 connects to MCP server instead of importing tools directly
