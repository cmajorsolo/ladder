# AI Engineering Study Plan

> **Goal:** Become portfolio-ready for a production AI engineering role with a focus on agent systems and prop-tech AI.
> **Duration:** ~12 weeks | ~2–3 focused hours/day
> **Last updated:** June 2026
> **Profile:** `my_profile.md` | **JD folder:** `JD/`

---

## Gap Analysis

| Have | Need to Close |
|---|---|
| 14 years engineering experience | Agent architecture patterns |
| PhD in deep learning for time series | MCP / tool use patterns |
| AI tool familiarity | LangChain / LangGraph or similar frameworks |
| Python (strong) | AWS production patterns for AI |
| | TypeScript for AI services |

---

## Phase 1 — Agent Fundamentals (Weeks 1–2)

### Concepts
- What makes an "agent" vs a chatbot: the ReAct loop (Reason → Act → Observe)
- Tool use / function calling (Anthropic API)
- Memory patterns: in-context, external (vector store), episodic
- Single-agent vs multi-agent orchestration
- Web scraping and structured data extraction as agent tools

### Portfolio Project: "Job Hunting Agent" 🎯
> *A real tool you'll use every day — and a perfect agent demo for interviews.*

A multi-agent pipeline that automates your own job search:

**Agent 1 — Job Scraper**
- Searches LinkedIn, Wellfound, and Indeed for "Senior AI Engineer" roles in UK/Ireland (remote)
- Uses web scraping / search tools to collect raw JD text
- Saves each JD to the `JD/` folder as a numbered markdown file

**Agent 2 — JD Analyst**
- Reads and parses all JDs in the `JD/` folder
- Extracts: required skills, nice-to-haves, years of experience, stack, contract vs perm
- Scores each JD for fit against `my_profile.md` (0–100)
- Filters and ranks — outputs a shortlist of top matches

**Agent 3 — Gap Analyser**
- Aggregates requirements across all collected JDs
- Extracts the most common requirements (frequency-ranked)
- Compares against `my_profile.md` to identify gaps
- Outputs a structured gap report: `gap_report.md`

**Agent 4 — Study Plan Updater**
- Reads `gap_report.md`
- Generates new "learn by doing" study items with a practical project per gap
- Appends them to `study_plan.md` under a new section: **"Gap-Driven Learning Items"**

**Human-in-the-loop checkpoint:** After Agent 2 ranks JDs, you review and approve the shortlist before Agents 3 & 4 run.

#### Architecture
```
Web Search Tool → Agent 1 (Scraper)
                      ↓
              JD markdown files
                      ↓
Agent 2 (Analyst) → scored shortlist → [YOU APPROVE]
                      ↓
Agent 3 (Gap Analyser) → gap_report.md
                      ↓
Agent 4 (Study Plan Updater) → study_plan.md updated
```

#### Why this is the perfect Phase 1 project
- Forces you to learn tool use, file I/O as tools, and the ReAct loop with a real problem
- Produces immediate value — your own job search is automated
- Demonstrates multi-agent orchestration to interviewers with a relatable use case
- Is genuinely impressive: "I built an agent to find the job I'm interviewing for"

### Target Job Platforms
| Platform | Why |
|---|---|
| LinkedIn | Volume + recruiter reach in UK/Ireland |
| Wellfound (AngelList) | Best for AI startups and scale-ups |
| Indeed UK/IE | Broad coverage including contract roles |
| Built In London / Built In Dublin | Tech-focused, high signal-to-noise |
| CWJobs / Technojobs | UK contract market (outside IR35 roles) |

### Resources
- [ ] Anthropic tool use docs (2–3 hours)
- [ ] [Building effective agents](https://www.anthropic.com/research/building-effective-agents) — Anthropic's own guide
- [ ] OpenAI function calling docs
- [ ] Python `requests` + `BeautifulSoup` for scraping (or Firecrawl API for cleaner extraction)

---

## Phase 2 — Frameworks + Multi-Agent (Weeks 3–5)

### Concepts
- LangGraph (preferred over LangChain — graph-based, more controllable)
- Agent-to-agent communication patterns: supervisor, swarm, sequential
- MCP (Model Context Protocol) — how tools/context are served to agents
- Structured outputs + guardrails

### Portfolio Project: "Lead Qualification Pipeline"
A multi-agent system with:
- **Agent 1:** Ingests CRM-style transaction data
- **Agent 2:** Scores and qualifies leads using ML instincts
- **Agent 3:** Drafts an outreach summary
- Wired together with LangGraph; includes a human-in-the-loop approval node

### Resources
- [ ] LangGraph docs + "agentic patterns" examples
- [ ] MCP quickstart (Anthropic docs) — build one MCP server exposing a "property data" tool
- [ ] Reverse-engineer Claude Code MCP integration

---

## Phase 3 — Production Engineering (Weeks 6–9)

> ⚠️ This is not a research role. Production deployment is the priority.

### Concepts
- Deploying agents as AWS Lambda functions or ECS containers
- Agent observability: LangSmith (trace every LLM call, tool call, latency, cost)
- Prompt versioning and evaluation
- Data isolation patterns (critical for prop-tech with client data)
- Cost control: caching, prompt compression, model routing

### Portfolio Project: "Autonomous Anomaly Alerting Service" ⭐
Deploy PhD-level time series anomaly detection as an MCP tool:
- Agent monitors a stream of mock transaction data
- Fires alerts and logs everything to CloudWatch
- Deployed on AWS Lambda with CDK
- LangSmith tracing included

**Why this is a killer piece:** directly maps to "trend detection and anomaly identification" in the JD, and showcases a unique technical edge most candidates don't have.

### Resources
- [ ] AWS CDK workshop (free, ~1 day)
- [ ] LangSmith tracing quickstart
- [ ] Anthropic prompt caching docs (cost control)

---

## Phase 4 — TypeScript + Full Stack AI (Weeks 10–12)

### Concepts
- Vercel AI SDK (best TS library for AI apps)
- Building AI endpoints in Next.js or standalone Node services
- Streaming responses to frontends
- Connecting TS agent services to Python ML backend via APIs

### Portfolio Project: "Agent Dashboard"
A Next.js UI that:
- Accepts a property address from a user
- Triggers the multi-agent pipeline (from Phase 2) via an API
- Streams the agent's reasoning steps back to the UI in real time
- Displays a cost/token counter per run

### Resources
- [ ] Vercel AI SDK docs
- [ ] TypeScript for Python developers cheatsheet (a few hours, not weeks)

---

## Full Stack Reference

| Layer | Tool |
|---|---|
| Agent framework | LangGraph (Python), Vercel AI SDK (TS) |
| LLM APIs | Anthropic + OpenAI |
| Tool protocol | MCP |
| Observability | LangSmith |
| Cloud | AWS (Lambda + CDK) |
| Data | PostgreSQL/MySQL locally, S3 for files |

---

## Unique Edge to Emphasise

PhD in time series + DL is genuinely rare in the agent engineering space. Most AI engineers are software people who learned prompting. Leverage this by:

- Building the **anomaly detection and trend analysis** components others can't
- Designing **self-learning workflows** with actual ML rigour
- Speaking credibly about **model evaluation and MLOps**
- Framing projects around prop-tech data: price time series, transaction volumes, lead conversion rates

---

## Key Milestone

> 🚀 **Deploy something real on AWS by Week 9.**
> That's the gap most candidates have, and it's what "production-grade" in the JD is testing for.

---

## Progress Tracker

| Phase | Status | Notes |
|---|---|---|
| Phase 1 — Job Hunting Agent | 🔲 Not started | |
| Phase 2 — Frameworks + Multi-Agent | 🔲 Not started | |
| Phase 3 — Production Engineering | 🔲 Not started | |
| Phase 4 — TypeScript + Full Stack AI | 🔲 Not started | |
