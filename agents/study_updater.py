"""
Agent 4 - Study Plan Updater.

Reads gap_report.json and study_plan.md, generates a practical "learn by doing"
study item for each gap, and appends them to study_plan.md under
"Gap-Driven Learning Items".
"""
import anthropic
import json
import logging
from dotenv import load_dotenv
from tools.file_tools import read_file, append_to_study_plan

load_dotenv()
logging.basicConfig(level=logging.INFO)
client = anthropic.Client()

GAP_REPORT_PATH = "data/gap_report.json"
STUDY_PLAN_PATH = "data/study_plan.md"

TOOLS = [
    {
        "name": "read_file",
        "description": "Read any file and return its contents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read."}
            },
            "required": ["path"]
        }
    },
    {
        "name": "append_to_study_plan",
        "description": "Append the generated learning items to study_plan.md.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Markdown content to append."}
            },
            "required": ["content"]
        }
    }
]

MAX_ITERATIONS = 15

def run_study_updater_agent() -> None:
    """Reads gap report and updates study_plan.md with gap-driven learning items."""
    messages = [
        {"role": "user", "content": (
            f"Read the gap report at '{GAP_REPORT_PATH}' and the study plan at '{STUDY_PLAN_PATH}'.\n"
            "For each gap with status 'gap' or 'partial', generate a practical 'learn by doing' study item.\n"
            "Each item should include:\n"
            "- A heading with the skill name and priority\n"
            "- One concrete project idea that directly builds that skill\n"
            "- Why it matters for Senior AI Engineer roles\n"
            "Sort items by priority (high first). Then call append_to_study_plan with the full markdown content."
        )}
    ]

    i = 0
    while i < MAX_ITERATIONS:
        i += 1
        logging.info(f"Study updater iteration {i}/{MAX_ITERATIONS}")
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=(
                "You are a study plan generator. "
                "1. Read the gap report JSON. "
                "2. Read the existing study plan to understand the context and avoid duplication. "
                "3. Generate practical, project-based learning items for each gap. "
                "4. Call append_to_study_plan once with all items. Then stop."
            ),
            tools=TOOLS,
            messages=messages
        )

        for block in response.content:
            if block.type == "text":
                logging.info(f"[Claude] {block.text}")
            elif block.type == "tool_use":
                logging.info(f"[Tool call] {block.name}({json.dumps(block.input)[:100]}...)")

        if response.stop_reason == "tool_use":
            tool_results = []
            for tool_use in [b for b in response.content if b.type == "tool_use"]:
                if tool_use.name == "read_file":
                    result = read_file(tool_use.input["path"])
                elif tool_use.name == "append_to_study_plan":
                    result = append_to_study_plan(tool_use.input["content"])

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(result)
                })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            logging.info(f"Study updater done. stop_reason={response.stop_reason}")
            return
