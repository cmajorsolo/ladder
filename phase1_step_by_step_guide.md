# Phase 1 — Agent Fundamentals: Step-by-Step Guide
> Project: Job Hunting Agent
> Duration: 2 weeks | Goal: Build a 4-agent pipeline that automates your job search

---

## The Golden Rule
**Don't touch LangGraph yet.** Build everything raw with the Anthropic API first.
You need to feel the ReAct loop manually before a framework hides it from you.
In Phase 2, LangGraph replaces your manual wiring — you'll appreciate it far more having done it by hand.

---

## Week 1 — Build Agent 1 (The Scraper)

### Day 1–2: Tool Use Fundamentals

**Goal:** Make Claude call a tool end-to-end. Just this. Nothing else.

1. Read the [Anthropic tool use docs](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) — 2 hours max
2. Create the project folder structure (see below)
3. Get your `ANTHROPIC_API_KEY` into `.env`
4. Write a single Python script where Claude calls one tool:

```python
# Your literal Day 1 task
web_search("Senior AI Engineer UK remote")
```

Print the result. That's it. Everything else builds from there.

5. Start with a **mock tool** — a function that returns hardcoded JSON job listings. Call it from Claude via tool use. Make this work end to end before touching real web data.

---

### Day 3–4: Real Web Data

**Goal:** Swap the mock tool for real scraping.

- Use [Firecrawl API](https://www.firecrawl.dev/) (free tier — cleaner, more agent-friendly) **or** `requests` + `BeautifulSoup`
- Start with **Indeed** and **Wellfound** — both are scraper-friendly
- ⚠️ **Avoid LinkedIn for now** — it actively blocks scrapers. Use its public search URLs or paste JDs manually into the `JD/` folder. Agent 2 will still analyse them. Add a LinkedIn tool later once the pipeline works.

Agent 1 flow:
```
receive search query
  → call scrape tool
  → get raw HTML/text
  → Claude extracts structured JD data
  → saves to JD/ as markdown file
```

---

### Day 5: File I/O as a Tool

**Goal:** Teach the agent to interact with the file system — a core pattern.

- Write a `save_jd` tool that takes structured JD content and writes it to:
  `JD/JD{n}_Title_Company.md`
- Agent 1 is now complete: search → scrape → structure → save ✅

---

## Week 2 — Agents 2, 3 & 4 (Chained, Still Raw API)

Each agent is a **separate Python function** that calls Claude with its own system prompt and tools.
Chain them manually — output of Agent 1 is input to Agent 2, and so on.

### Agent 2 — JD Analyst
- Reads each JD file from `JD/`
- Reads `my_profile.md` as the comparison baseline
- Scores each JD 0–100 for fit
- Outputs a ranked list with scores and reasoning

### 👤 Human Checkpoint
- You review the scores
- Type: `"approve [1,3,5]"` or `"approve all"`
- Only approved JDs pass to Agent 3

### Agent 3 — Gap Analyser
- Reads approved JDs
- Aggregates requirements across all JDs (frequency-ranked)
- Compares against `my_profile.md`
- Writes structured gap report to `gap_report.md`

### Agent 4 — Study Plan Updater
- Reads `gap_report.md`
- Reads `study_plan.md`
- Generates "learn by doing" study items — one practical project per gap
- Appends them to `study_plan.md` under **"Gap-Driven Learning Items"**

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                          │
│           (main.py — you run this)                       │
│  Controls flow, passes state, handles human checkpoint   │
└──────────┬──────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────┐
│   AGENT 1           │  Tools:
│   Job Scraper       │  • web_search(query) → raw results
│                     │  • scrape_page(url)  → JD text
│                     │  • save_jd(content)  → writes JD/JDn.md
│                     │
│                     │  Input:  search query string
│                     │  Output: list of saved JD file paths
└──────────┬──────────┘
           │  file paths
           ▼
┌─────────────────────┐
│   AGENT 2           │  Tools:
│   JD Analyst        │  • read_file(path)    → JD content
│                     │  • read_profile()     → my_profile.md
│                     │
│                     │  Input:  list of JD file paths
│                     │  Output: ranked list with scores + reasoning
└──────────┬──────────┘
           │
           ▼
    ┌─────────────┐
    │  👤 YOU     │  Review scores, approve shortlist
    │  CHECKPOINT │
    └──────┬──────┘
           │ approved JD paths
           ▼
┌─────────────────────┐
│   AGENT 3           │  Tools:
│   Gap Analyser      │  • read_file(path)          → JD content
│                     │  • read_profile()            → my_profile.md
│                     │  • write_gap_report(content) → gap_report.md
│                     │
│                     │  Input:  approved JD paths
│                     │  Output: gap_report.md written to disk
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   AGENT 4           │  Tools:
│   Study Updater     │  • read_file(gap_report.md)
│                     │  • read_file(study_plan.md)
│                     │  • append_to_study_plan(new_items)
│                     │
│                     │  Input:  gap_report.md
│                     │  Output: study_plan.md updated
└─────────────────────┘
```

---

## Shared State

Keep it simple — a plain Python dict passed between agents:

```python
state = {
    "search_query": "Senior AI Engineer UK remote",
    "jd_paths":       [],   # filled by Agent 1
    "scored_jds":     [],   # filled by Agent 2
    "approved_paths": [],   # filled by you at checkpoint
    "gap_report_path": "",  # filled by Agent 3
}
```

> In Phase 2, LangGraph replaces this dict with a proper typed state graph.

---

## Folder Structure

Set this up on Day 1:

```
job-hunting-agent/
├── main.py                  # orchestrator — runs the full pipeline
├── agents/
│   ├── scraper.py           # Agent 1
│   ├── analyst.py           # Agent 2
│   ├── gap_analyser.py      # Agent 3
│   └── study_updater.py     # Agent 4
├── tools/
│   ├── web_tools.py         # web_search, scrape_page
│   └── file_tools.py        # read_file, save_jd, write_gap_report, etc.
├── data/
│   ├── my_profile.md        # your background — comparison baseline
│   ├── gap_report.md        # auto-generated by Agent 3
│   ├── study_plan.md        # auto-updated by Agent 4
│   └── JD/                  # all job descriptions land here
├── .env                     # ANTHROPIC_API_KEY, FIRECRAWL_API_KEY
└── requirements.txt
```

---

## Job Platforms

| Platform | Why | Scraper-friendly? |
|---|---|---|
| Indeed UK/IE | Broad coverage, contract roles | ✅ Yes |
| Wellfound | Best for AI startups & scale-ups | ✅ Yes |
| Built In London / Dublin | High signal-to-noise for AI roles | ✅ Yes |
| CWJobs / Technojobs | UK contract market, outside IR35 | ✅ Yes |
| LinkedIn | Volume + recruiter reach | ⚠️ Blocks scrapers — add later |

---

## File Formats: What to Use and Why

**The rule:** `.md` for human-readable documents, `JSON` for data passed between agents.

Markdown is plain text under the hood — LLMs read it well, and the headings and tables in your files are meaningful structure. Don't change your `.md` files. But when one agent produces output that another agent consumes, use JSON. It's deterministic, cheap to parse, and removes all ambiguity.

### Format Per File

| File | Format | Reason |
|---|---|---|
| `my_profile.md` | Markdown | Human-readable, stable reference — fine as-is |
| `JD/*.md` | Markdown (normalised structure) | For you to read and review |
| `JD/*.json` | JSON | For agents to process — Agent 1 saves both |
| Agent 2 output (scored JDs) | JSON | Machine-consumed by Agent 3 |
| `gap_report.md` | Markdown + embedded JSON block | Human-readable + structured `gaps[]` array Agent 4 can parse |
| `study_plan.md` | Markdown | Human-edited, not machine-parsed |

### Agent 1: Save Two Files Per JD

When Agent 1 saves a JD, output **both** formats:
- `JD/JD1_Title_Company.md` — for you to review
- `JD/JD1_Title_Company.json` — for Agent 2 to process

```json
{
  "id": "JD1",
  "title": "Senior AI Engineer",
  "company": "PropTech UK",
  "rate": "£900/day",
  "contract_type": "Outside IR35",
  "required": ["LangGraph", "AWS Lambda", "TypeScript", "10+ years SE"],
  "nice_to_have": ["MLOps", "NLP", "microservices"],
  "stack": ["Python", "TypeScript", ".NET", "AWS"],
  "fit_score": null
}
```

Agent 2 reads the JSON, fills in `fit_score`, and passes the enriched JSON to Agent 3. Clean, deterministic, no parsing ambiguity.

### What Actually Matters More Than Format

1. **Token efficiency** — don't pass the whole file if the agent only needs one section. When Agent 2 is scoring a JD, pass only the skills and gaps table from `my_profile.md`, not the full career narrative.

2. **Consistent structure** — if every JD JSON has the same fields in the same order, extraction is reliable. Inconsistent structure causes hallucinations.

3. **Explicit labels** — `"required": ["5+ years Python"]` is better for LLM parsing than a sentence saying the same thing. Agent 1's job is to normalise raw JD text into this clean structure.

---

## Key Concepts You'll Learn by Building This

| Concept | Where you'll encounter it |
|---|---|
| ReAct loop (Reason → Act → Observe) | Every agent call |
| Tool use / function calling | All 4 agents |
| Structured outputs | Agent 2 scoring, Agent 3 gap report |
| File I/O as agent tools | Agents 1, 3, 4 |
| Human-in-the-loop | Checkpoint after Agent 2 |
| Agent chaining / pipeline | Orchestrator in main.py |
| State management (manual) | The shared `state` dict |
| Prompt engineering | Each agent's system prompt |
