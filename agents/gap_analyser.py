"""
Agent 3 - Gap Analyser.

Reads approved JDs and the candidate profile, aggregates required skills
across all JDs (frequency ranked), compares against the profile, and writes:
  - data/gap_report.md  (human-readable)
  - data/gap_report.json (consumed by Agent 4)
"""
import anthropic
import json
import logging
from dotenv import load_dotenv
from tools.file_tools import read_jd, read_profile, write_gap_report

load_dotenv()
logging.basicConfig(level=logging.INFO)
client = anthropic.Client()

TOOLS = [
    {
        "name": "read_jd",
        "description": "Read a JD JSON file by path and return its contents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Full path to the JD JSON file."}
            },
            "required": ["path"]
        }
    },
    {
        "name": "read_profile",
        "description": "Read the candidate's profile from my_profile.md.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "write_gap_report",
        "description": "Save the gap report. Call this once with the full list of gaps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gaps": {
                    "type": "array",
                    "description": "List of skill gaps.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "skill":     {"type": "string"},
                            "frequency": {"type": "integer", "description": "How many JDs require this skill."},
                            "priority":  {"type": "string", "enum": ["high", "medium", "low"]},
                            "status":    {"type": "string", "enum": ["gap", "partial", "have"]}
                        },
                        "required": ["skill", "frequency", "priority", "status"]
                    }
                }
            },
            "required": ["gaps"]
        }
    }
]

MAX_ITERATIONS = 20

def run_gap_analyser_agent(approved_paths: list[str]) -> str:
    """Runs the gap analyser agent. Returns the path to gap_report.json."""
    messages = [
        {"role": "user", "content": (
            f"Analyse the skill gaps for these approved JDs: {json.dumps(approved_paths)}.\n"
            "Steps:\n"
            "1. Call read_jd for each path to get the requirements.\n"
            "2. Call read_profile to get the candidate's current skills.\n"
            "3. Aggregate all required skills across JDs. Count how many JDs require each skill.\n"
            "4. Compare against the profile — mark each skill as 'gap', 'partial', or 'have'.\n"
            "5. Set priority: 'high' if frequency >= 3, 'medium' if 2, 'low' if 1.\n"
            "6. Call write_gap_report with the full list of gaps sorted by frequency descending."
        )}
    ]

    i = 0
    while i < MAX_ITERATIONS:
        i += 1
        logging.info(f"Gap analyser iteration {i}/{MAX_ITERATIONS}")
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=(
                "You are a gap analysis agent. "
                "Read each approved JD, read the candidate profile, "
                "identify skill gaps by comparing JD requirements to the profile, "
                "then call write_gap_report once with all gaps. Then stop."
            ),
            tools=TOOLS,
            messages=messages
        )

        for block in response.content:
            if block.type == "text":
                logging.info(f"[Claude] {block.text}")
            elif block.type == "tool_use":
                logging.info(f"[Tool call] {block.name}({json.dumps(block.input)})")

        if response.stop_reason == "tool_use":
            tool_results = []
            for tool_use in [b for b in response.content if b.type == "tool_use"]:
                if tool_use.name == "read_jd":
                    result = read_jd(tool_use.input["path"])
                elif tool_use.name == "read_profile":
                    result = read_profile()
                elif tool_use.name == "write_gap_report":
                    result = write_gap_report(tool_use.input["gaps"])

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(result)
                })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            logging.info(f"Gap analyser done. stop_reason={response.stop_reason}")
            return
