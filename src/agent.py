import os
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langsmith import Client
from tools.anomaly_tools import load_transactions, detect_anomalies, fire_alert


def _load_prompt() -> str:
    """Pull system prompt from LangSmith. Falls back to hardcoded prompt if unavailable."""
    try:
        client = Client(
            api_url=os.environ.get("LANGSMITH_ENDPOINT", "https://eu.api.smith.langchain.com"),
            api_key=os.environ.get("LANGSMITH_API_KEY"),
        )
        prompt = client.pull_prompt("anomaly-detector-system-prompt")
        # Extract the system message content from the prompt template
        content = prompt.messages[0].prompt.template
        print(f"Successfully pulled prompt from LangSmith: '{content[:50]}...'")
        return content
    except Exception as e:
        print(f"Failed to pull prompt from LangSmith ({e}), using hardcoded prompt.")
        return (
            "You are an anomaly detection agent monitoring property transaction data. "
            "Each run: load the latest transactions, detect anomalies using z-score analysis, "
            "fire alerts for any found, then stop. Be concise."
        )


anomaly_agent = create_react_agent(
    model=ChatAnthropic(model="claude-haiku-4-5-20251001"),
    tools=[load_transactions, detect_anomalies, fire_alert],
    prompt=_load_prompt()
)


def run_anomaly_agent() -> str:
    result = anomaly_agent.invoke({
        "messages": [("user", "Run anomaly detection on the latest transaction data.")]
    })
    return result["messages"][-1].content
