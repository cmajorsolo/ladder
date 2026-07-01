# Notes

---

## Q: Do I have to use a name that Claude already knows, like "web_search"?

**Short answer: No. You make up the name yourself.**

Claude has no built-in tools. When you call the Anthropic API, you send a list of tools you want Claude to be able to use. You define the name, the description, and what inputs it takes.

Claude does not recognise "web_search" as a special name. It reads the **description** you write and decides from that whether to call the tool.

So you could name it "web_search", "find_jobs", "search", or anything else — it makes no difference to Claude.

**What actually matters:**

1. The **description** — Claude reads this to decide when to use the tool.
2. The **name must match** between your tool definition and your Python `if` statement.

Example:

```python
# You define the tool with this name and description
{
    "name": "find_jobs",
    "description": "Search for job listings matching a query.",
    ...
}

# Claude calls it and returns this name in its response
# Your code checks for the same name
if tool_name == "find_jobs":
    result = mock_web_search(tool_input["query"])
```

That matching string is the only contract. The name is just a label so your code knows which function to run.

## Q: Does Claude read my tool function's docstring to decide which tool to call? Or does it read the prompt in create_react_agent?

Both — but they serve different purposes.

**The prompt** tells Claude the overall goal and sequence:
> "Search once, scrape each result, save each job, then stop."

**The docstrings** tell Claude what each individual tool does and when to use it:
> "Search for job listings matching the query. Returns a list of results with title, url, and snippet."

The flow is:
```
Prompt → Claude reasons about the next step
           → reads tool docstrings to pick the right tool
           → calls it → observes result → repeats
```

The prompt is your job description ("build a house"). The docstrings are the labels on your tools ("this is a hammer"). You need both.

---

## Q: Does Claude see my function implementation code? When it calls web_search, does it look at the code or call the function on my machine?

Claude never sees your function implementation code. It only sees:
1. The **function name**
2. The **docstring** (description)
3. The **type hints** (parameter names and types)

LangGraph extracts these and sends them to Claude as a tool schema — exactly like the JSON schemas you wrote manually in Phase 1.

**What actually happens when Claude "calls" a tool:**
```
Claude → emits: { "name": "web_search", "input": {"query": "..."} }
                                    ↓
              LangGraph looks up "web_search" in its tool registry,
              calls the real Python function on YOUR machine
                                    ↓
              result is sent back to Claude as a tool_result
```

Claude never calls the function directly. It just says "I want to call web_search with these inputs" — your machine does the actual execution and sends the result back.

**Analogy:** Claude is like a manager who says "go check the weather in Dublin". It doesn't know how you check it. It just gets the answer back and continues reasoning. Your function implementation is always local.

---

## Q: Where does LadderState live? How does state get updated between nodes?

**LadderState is a plain Python dict in your local process's memory. It never leaves your machine.**

The LLM never sees the state dict — it only ever sees the `messages` list.

### The two separate worlds

```
YOUR LOCAL PROCESS (Python)          ANTHROPIC API (remote)
─────────────────────────────        ──────────────────────
LadderState dict                     never sent here
MemorySaver (in-memory cache)

scraper_node runs
  → packages messages list
  → sends HTTP POST ────────────────► Claude model
                                      Claude replies with tool_call or text
  ← receives response ◄───────────────
  → executes tool locally
  → appends result to messages
  → loops (ReAct)
  → returns {"messages": [...]}

LangGraph merges return value
into LadderState dict
```

### How state gets updated — step by step

1. **Node receives the full state** — e.g. `{"search_query": "...", "messages": [], "scored_jds": [], ...}`
2. **Node runs the agent** — the ReAct loop runs entirely locally. Claude is called via HTTP, but tool execution (web_search, scrape_page, save_jd) all happens in your process.
3. **Node returns only what changed** — e.g. `{"messages": result["messages"]}` — a partial update.
4. **LangGraph merges it into LadderState** using reducers:
   - `messages` has `Annotated[list, add_messages]` → **appends** new messages (doesn't replace)
   - All other keys use the default reducer → **replaces** the value

### Where MemorySaver fits in

`MemorySaver` snapshots the entire `LadderState` after each node, keyed by `thread_id`. This is what makes `interrupt()` work — the graph can pause (at the human checkpoint), your `input()` runs, and then `graph.stream(Command(resume=...))` picks up from exactly where it left off. Without `MemorySaver`, state would be lost between the two `stream()` calls.

### The key insight

> The state dict is a local coordinator. The LLM is a stateless function.

Each API call reconstructs all context by passing the full messages list. Claude has no memory between calls — `LadderState["messages"]` *is* the memory. This is why `add_messages` accumulates instead of replacing.

---

## Q: What is MCP? What transport does it use? What is stdio?

### The protocol: stdio (locally) or HTTP/SSE (remotely)

**stdio = standard input/output** — the same stdin/stdout pipes every terminal program uses. MCP uses these pipes as a transport: the client and server talk by writing JSON-RPC messages to each other's stdin/stdout.

```
scraper_node (client)          mcp_server.py (subprocess)
      │                                │
      │──── stdin pipe ───────────────▶│  {"method": "tools/call", "params": {"name": "web_search", ...}}
      │                                │  [runs web_search() locally]
      │◀─── stdout pipe ───────────────│  {"result": [{"title": "...", "url": "..."}]}
```

Your process spawns `mcp_server.py` as a child process and they communicate through these pipes. That's stdio transport.

### Does stdio MCP help with concurrency? No.

stdio MCP is **1 client → 1 server subprocess**. It is 1:1. Spawning 1,000 subprocesses for 1,000 users is worse than not using MCP at all.

The reason to build an MCP server in Phase 2 is to **learn the protocol** — not for scalability.

### When does MCP actually help? HTTP transport at scale.

```
Without MCP (1,000 users):
  Each user's process independently calls web_search() → Firecrawl API
  No shared cache. No shared rate limiting. Each process needs the API key.

With HTTP MCP server (1,000 users):
  User 1    ──▶ ╮
  User 2    ──▶ ╠══▶  MCP server (deployed on ECS/Lambda)  ──▶  Firecrawl API
  User 1000 ──▶ ╯     shared cache, rate limiting, one API key
```

| Problem | Without central MCP server | With HTTP MCP server |
|---|---|---|
| API key | Every process needs it | Only the server holds it |
| Caching | Same query scraped 1,000 times | Server caches, serves from cache |
| Rate limiting | Each process independently hammers the API | One server enforces a shared limit |
| Tool updates | Redeploy every client | Update the server once |
| Tool reuse | Locked inside your Python app | Any MCP-compatible agent can call it |

### The real reason MCP exists

MCP **decouples tools from agents**. The analogy is REST APIs:
- Before REST: every app embedded its own DB queries
- After REST: apps call a shared API that owns the data layer

MCP does the same for agent tools:
- Before MCP: tools are Python functions imported into your agent
- After MCP: tools are a service any agent (Claude, GPT, any framework) can discover and call over HTTP

### Summary of what you understood correctly

1. **Parallelism** — HTTP MCP server handles concurrent requests; agents just fire HTTP calls and await.
2. **Shared cache** — one server caches results; duplicate queries across all callers are served from cache without hitting the upstream API again.
3. **Tools usable outside your framework** — any MCP-compatible client can call your tools, regardless of language or agent framework.

> Caching and parallelism aren't given to you by MCP automatically — they're things you implement in the server. MCP gives you the right architecture to add them in one place.

---

## Q: What is a Lambda Layer and why use it?

A Lambda Layer is a pre-packaged zip of Python dependencies (like `anthropic`, `langgraph`, `langsmith`) that you attach to a Lambda function. It is the Lambda equivalent of running `pip install -r requirements.txt` locally — except you do the install once on your machine, zip the result, upload it to AWS, and Lambda mounts it at `/opt/python/` at runtime.

**Why not just bundle dependencies into `src/`?**

You can, but then every deployment re-uploads the full package (50MB+) even when only your handler code changed.

With a layer:
- First deploy: uploads the layer (50MB) + your code (tiny)
- Every subsequent deploy: uploads only your code (tiny) — the layer is already on AWS

**The analogy:**
| Local dev | Lambda |
|---|---|
| `requirements.txt` | Lambda Layer |
| `pip install -r requirements.txt` | `pip install -t layer/python/` |
| packages land in `.venv/lib/` | packages land in `layer/python/` |
| Python finds them automatically | Lambda finds them at `/opt/python/` |

**Key points:**
- No dynamic install happens at runtime — packages are pre-built and shipped
- The total size AWS stores is the same either way — the benefit is faster re-deployments when iterating on code
- One layer can be shared across multiple Lambda functions

---

## Q: Why I only get 4 JDs saved?
1. Date filter is too narrow — days_ago=7 combined with specific job sites may have very few recent matches.
2. Site filter is too restrictive — cwjobs.co.uk and technojobs.co.uk may not have many indexed results for your exact query.
3. Firecrawl free tier — may cap actual results regardless of limit.
4. Claude only scrapes some URLs — even if Firecrawl returns more URLs, Claude decides which ones look like real job listings worth scraping.

To diagnose, add a log right after web_search returns to see how many URLs Firecrawl actually give back:

```python
if tool_name == "web_search":                                                                                                                                                                                                         
    result = web_search(tool_input["query"], limit=100, days_ago=tool_input.get("days_ago", 7))
    logging.info(f"[web_search] returned {len(result)} results")
```
                                
                                                                                                                                                                                                                                    
