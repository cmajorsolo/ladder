# Phase 3 — Production Engineering: Step-by-Step Guide
> Project: Autonomous Anomaly Alerting Service
> Duration: 4 weeks (Weeks 6–9) | Goal: Deploy a real agent to AWS, with full observability

---

## The Golden Rule

Phase 3 is not about learning new AI concepts — it is about making what you already built *production-grade*. Every senior AI Engineer JD has "deploy to AWS", "observability", and "cost control". This phase is where you close all three gaps at once.

By the end, you will have a deployed AWS Lambda service that runs your anomaly detection logic, traces every LLM call with LangSmith, and manages cost. That is the missing piece on most AI portfolios.

---

## What You Are Building

**"Autonomous Anomaly Alerting Service"** — a deployed agent that:
- Ingests a stream of mock property transaction data (time series)
- Uses your PhD-level anomaly detection instincts (via an LLM agent with custom tools)
- Fires alerts to CloudWatch when anomalies are detected
- Is deployed on AWS Lambda via CDK
- Has full LangSmith tracing for every LLM call, tool call, latency, and cost

```
Mock Transaction Data (S3 or inline)
        ↓
AWS Lambda (triggered on schedule or event)
        ↓
LangGraph Agent — Anomaly Detector
  ├── tool: load_transactions()    ← reads data
  ├── tool: detect_anomalies()     ← your ML logic (statistical / threshold)
  └── tool: fire_alert()           ← writes to CloudWatch + logs
        ↓
CloudWatch Logs + Metrics
        ↓
LangSmith Traces (every LLM call traced)
```

---

## Phase 2 vs Phase 3 — Side by Side

| Phase 2 (local) | Phase 3 (production) |
|---|---|
| Runs on your laptop | Deployed on AWS Lambda |
| No tracing | LangSmith traces every call |
| No cost visibility | Token cost tracked per run |
| `MemorySaver` (in-process) | DynamoDB or no persistence needed for Lambda |
| Tools imported directly | Tools packaged in Lambda layer |
| `python main.py` | Triggered by EventBridge schedule |

---

## Week 6 — AWS CDK + Lambda Fundamentals

### Day 1–2: Set Up AWS CDK

**Goal:** Get a working CDK project that deploys a Hello World Lambda.

Install prerequisites:
```bash
npm install -g aws-cdk
pip install aws-cdk-lib constructs
```

Verify AWS credentials are configured:
```bash
aws configure        # set Access Key, Secret, region (eu-west-1 for Ireland)
aws sts get-caller-identity   # confirms you're authenticated
```

Bootstrap CDK for your account (one-time):
```bash
cdk bootstrap aws://YOUR_ACCOUNT_ID/eu-west-1
```

Create a CDK app in a new `infra/` folder:
```
infra/
├── app.py              # CDK entry point
└── stacks/
    └── anomaly_stack.py   # your Lambda + permissions defined here
```

Deploy a minimal Lambda to confirm the toolchain works before touching any agent code:
```python
# infra/stacks/anomaly_stack.py
from aws_cdk import Stack, aws_lambda as _lambda
from constructs import Construct

class AnomalyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        _lambda.Function(
            self, "AnomalyDetector",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("src"),
        )
```

**Why CDK over console clicks:** CDK is infrastructure-as-code. Every deployment is repeatable, reviewable, and deletable. Interviewers can see exactly what you deployed.

### Day 3–4: Package the Agent as a Lambda Handler

**Goal:** Wrap your LangGraph agent in a Lambda handler function.

Lambda functions have one entry point:
```python
# src/handler.py
def lambda_handler(event, context):
    # event comes from EventBridge or direct invocation
    result = run_anomaly_agent(event.get("data", []))
    return {"statusCode": 200, "body": result}
```

Key Lambda constraints to handle:
- **No persistent filesystem** — don't write files, use `/tmp` only if needed
- **Cold start** — import LangGraph and model clients at module level, not inside the handler
- **15-minute timeout max** — agents must complete within this window
- **Environment variables** — `ANTHROPIC_API_KEY`, `LANGSMITH_API_KEY` set via CDK, not `.env`

Set env vars via CDK (never hardcode secrets):
```python
_lambda.Function(
    self, "AnomalyDetector",
    ...
    environment={
        "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
        "LANGSMITH_API_KEY": os.environ["LANGSMITH_API_KEY"],
        "LANGSMITH_TRACING": "true",
        "LANGSMITH_PROJECT": "anomaly-alerting-service",
    }
)
```

### Day 5: Add a Lambda Layer for Dependencies

LangGraph + anthropic + langsmith are too large to bundle inline. Use a Lambda layer:

```bash
# Build the layer locally
mkdir -p layer/python
pip install langgraph anthropic langsmith -t layer/python/
```

```python
# In CDK stack
layer = _lambda.LayerVersion(
    self, "AgentDeps",
    code=_lambda.Code.from_asset("layer"),
    compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
)

fn = _lambda.Function(self, "AnomalyDetector", ..., layers=[layer])
```

---

## Week 7 — Build the Anomaly Detection Agent

### Day 1–2: Define the Agent Tools

**Goal:** Build three tools that the LangGraph agent will call.

```python
# src/tools/anomaly_tools.py
import json
import boto3
import numpy as np

def load_transactions(source: str = "inline") -> list[dict]:
    """Load mock property transaction data."""
    # For now: return hardcoded mock data
    # Later: read from S3
    return [
        {"date": "2026-01-01", "price": 450000, "volume": 12},
        {"date": "2026-01-02", "price": 455000, "volume": 11},
        # ... more rows
        {"date": "2026-01-15", "price": 620000, "volume": 3},  # anomaly
    ]

def detect_anomalies(transactions: list[dict], threshold: float = 2.0) -> list[dict]:
    """Detect price anomalies using z-score. PhD edge: this is your ML expertise."""
    prices = [t["price"] for t in transactions]
    mean = np.mean(prices)
    std = np.std(prices)
    anomalies = []
    for t in transactions:
        z = abs((t["price"] - mean) / std) if std > 0 else 0
        if z > threshold:
            anomalies.append({**t, "z_score": round(z, 2), "mean": mean, "std": std})
    return anomalies

def fire_alert(anomalies: list[dict]) -> str:
    """Log anomalies to CloudWatch as structured log entries."""
    if not anomalies:
        return "No anomalies detected."
    client = boto3.client("logs", region_name="eu-west-1")
    for a in anomalies:
        print(json.dumps({"alert": "ANOMALY_DETECTED", **a}))  # CloudWatch picks this up
    return f"Fired {len(anomalies)} alert(s)."
```

Note: `print()` in a Lambda function writes to CloudWatch Logs automatically. No SDK call needed for basic alerting.

### Day 3: Build the LangGraph Agent

**Goal:** Wire the three tools into a LangGraph `create_react_agent`.

```python
# src/agent.py
from langgraph.prebuilt import create_react_agent
from tools.anomaly_tools import load_transactions, detect_anomalies, fire_alert

anomaly_agent = create_react_agent(
    model="claude-haiku-4-5-20251001",   # cheapest model — production cost control
    tools=[load_transactions, detect_anomalies, fire_alert],
    prompt=(
        "You are an anomaly detection agent monitoring property transaction data. "
        "Each run: load the latest transactions, detect anomalies using z-score analysis, "
        "fire alerts for any found, then stop. Be concise."
    )
)

def run_anomaly_agent(data=None) -> str:
    result = anomaly_agent.invoke({
        "messages": [("user", "Run anomaly detection on the latest transaction data.")]
    })
    return result["messages"][-1].content
```

### Day 4–5: Add CloudWatch Metrics (Custom)

Beyond logs, push a custom metric to track anomaly count per run:

```python
import boto3

def push_metric(anomaly_count: int):
    cw = boto3.client("cloudwatch", region_name="eu-west-1")
    cw.put_metric_data(
        Namespace="AnomalyAlertingService",
        MetricData=[{
            "MetricName": "AnomalyCount",
            "Value": anomaly_count,
            "Unit": "Count"
        }]
    )
```

This creates a metric you can graph in CloudWatch dashboards — strong portfolio visual.

---

## Week 8 — LangSmith Observability

### Day 1–2: Set Up LangSmith Tracing

**Goal:** Every LLM call, tool call, latency, and token count is traced automatically.

Sign up for LangSmith free tier. Get your API key.

LangSmith tracing with LangGraph is automatic — just set env vars:
```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=your_key
export LANGSMITH_PROJECT=anomaly-alerting-service
```

That's it. Every `agent.invoke()` call is now traced. You will see:
- Full message history
- Which tools were called, in what order
- Token count per call
- Latency per node
- Total cost per run

### Day 3: Explore the LangSmith UI

Spend half a day exploring your traces. Understand:
- The timeline view — see where time is spent
- Token breakdown — which node is most expensive
- Error traces — what a failed tool call looks like
- Comparing runs — before/after prompt changes

This is what "agent observability" means in the JD. You can now demo it.

### Day 4–5: Prompt Versioning

**Goal:** Understand how to version prompts and compare evaluation results.

In LangSmith, you can save prompts as versioned "prompt objects" and pull them at runtime:

```python
from langsmith import Client

client = Client()
prompt = client.pull_prompt("anomaly-detector-system-prompt")
```

For now, just create the prompt in the LangSmith UI and pull it in your agent. The key concept: **prompts are versioned artifacts, not hardcoded strings**. This matters for production because you can A/B test prompt changes.

---

## Week 9 — Cost Control + Trigger + Final Deployment

### Day 1–2: Anthropic Prompt Caching

**Goal:** Use Anthropic's prompt caching to reduce cost on repeated system prompts.

Your system prompt is the same on every Lambda invocation. Without caching, you pay to process it every time. With caching, after the first call, the prompt tokens are served from cache at ~10x lower cost.

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are an anomaly detection agent...",
            "cache_control": {"type": "ephemeral"}   # ← cache this
        }
    ],
    messages=[{"role": "user", "content": "Run anomaly detection."}]
)
```

Note: LangGraph's `create_react_agent` doesn't expose cache_control directly. For this, call the Anthropic client directly for the system prompt, or use a custom LangGraph node that constructs the message manually. This is a good exercise in going below the framework abstraction when needed.

### Day 3: Add EventBridge Trigger (Scheduled Run)

**Goal:** Make the Lambda run automatically on a schedule.

```python
# In CDK stack
from aws_cdk import aws_events as events, aws_events_targets as targets
from aws_cdk import Duration

rule = events.Rule(
    self, "AnomalySchedule",
    schedule=events.Schedule.rate(Duration.hours(1))  # run every hour
)
rule.add_target(targets.LambdaFunction(fn))
```

This is the production version of `cron`. The agent now runs without you touching it.

### Day 4: Data Isolation Pattern

**Goal:** Understand how to keep client data isolated — critical for prop-tech.

In a real prop-tech product, each client's transaction data must be isolated. The pattern:

```
Client A data → S3 bucket prefix: s3://data/client-a/transactions/
Client B data → S3 bucket prefix: s3://data/client-b/transactions/

Lambda invocation payload: {"client_id": "client-a", "date": "2026-06-29"}

Agent reads only from: s3://data/{client_id}/transactions/{date}.json
```

Implement this in your `load_transactions` tool:
```python
def load_transactions(client_id: str, date: str) -> list[dict]:
    s3 = boto3.client("s3")
    key = f"{client_id}/transactions/{date}.json"
    obj = s3.get_object(Bucket="prop-data-bucket", Key=key)
    return json.loads(obj["Body"].read())
```

Add an S3 bucket to CDK with bucket policies that enforce client prefix isolation. This is a 2-hour addition that adds significant depth to your portfolio.

### Day 5: Final Deployment + README

**Goal:** Deploy everything end-to-end and document it.

Final deployment commands:
```bash
cd infra
cdk deploy AnomalyStack
```

Confirm in AWS Console:
- Lambda function exists and last run succeeded
- CloudWatch Logs show structured anomaly alerts
- CloudWatch Metrics shows `AnomalyAlertingService/AnomalyCount`
- EventBridge rule is enabled

Update your README with:
- Architecture diagram (export from draw.io or use Mermaid)
- LangSmith trace screenshot
- CloudWatch dashboard screenshot
- "How to deploy" section (3 commands)

---

## Key Concepts Learned in Phase 3

| Concept | Where you encounter it |
|---|---|
| AWS Lambda deployment | `infra/stacks/anomaly_stack.py` |
| AWS CDK infrastructure-as-code | `infra/` folder |
| Lambda layers for dependencies | `layer/` folder |
| Lambda handler pattern | `src/handler.py` |
| EventBridge scheduled trigger | CDK `events.Rule` |
| CloudWatch Logs + custom metrics | `fire_alert()`, `push_metric()` |
| LangSmith tracing | Env vars + automatic via LangGraph |
| Prompt versioning | LangSmith UI + `pull_prompt()` |
| Anthropic prompt caching | `cache_control` on system prompt |
| Data isolation patterns | S3 prefix per client, bucket policies |

---

## Folder Structure

```
anomaly-alerting-service/
├── src/
│   ├── handler.py           # Lambda entry point
│   ├── agent.py             # LangGraph anomaly agent
│   └── tools/
│       └── anomaly_tools.py # load_transactions, detect_anomalies, fire_alert
├── infra/
│   ├── app.py               # CDK entry point
│   └── stacks/
│       └── anomaly_stack.py # Lambda + EventBridge + S3 + IAM
├── layer/
│   └── python/              # pip-installed deps for Lambda layer
├── tests/
│   └── test_tools.py        # unit tests for anomaly tools
├── requirements.txt
└── README.md
```

---

## Definition of Done

- [ ] `cdk deploy` succeeds with no errors
- [ ] Lambda invocation runs the full agent pipeline end-to-end
- [ ] CloudWatch Logs show structured anomaly alert JSON
- [ ] CloudWatch custom metric `AnomalyAlertingService/AnomalyCount` is visible
- [ ] EventBridge rule triggers Lambda on schedule
- [ ] LangSmith traces show every LLM + tool call with token counts
- [ ] Prompt is versioned in LangSmith and pulled at runtime
- [ ] `load_transactions` reads from S3 with client_id isolation
- [ ] README has architecture diagram, trace screenshot, and deploy instructions

---

## Why This Is a Killer Portfolio Piece

- **Maps directly to the JD:** "trend detection", "anomaly identification", "AWS Lambda", "CloudWatch", "production-grade"
- **Unique technical edge:** Z-score anomaly detection backed by a PhD in time series — most candidates fake this
- **Full stack:** infra-as-code + agent logic + observability + cost control, all in one repo
- **Live demo:** you can trigger it live during an interview with `aws lambda invoke` and show traces in LangSmith in real time
