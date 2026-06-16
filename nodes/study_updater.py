"""
  Study updater node for LangGraph. 

  Reads gap_report.json and appends gap-driven learning items to study_plan.md.
  
TODO:  Reads gap_report.json, read the current study_plan.md, analysing missing gaps
and appends gap-driven learning items to study_plan.md.
"""

from langgraph.prebuilt import create_react_agent
from state import LadderState
from tools.file_tools import read_file, append_to_study_plan

study_updater_agent = create_react_agent(
    model='claude-haiku-4-5-20251001',
    tools=[read_file, append_to_study_plan],
    prompt=(
        "You are a study plan generator. "
        "1. Call read_file with 'data/gap_report.json' to get the skill gaps. "
        "2. Call read_file with 'data/study_plan.md' to understand the existing plan. "
        "3. For each gap with status 'gap' or 'partial', generate a practical learn-by-doing project. "
        "4. Call append_to_study_plan once with all items as markdown, sorted by priority. Then stop."
    )
)

def study_updater_node(state: LadderState) -> dict:
    """LangGraph node - reads gap-driven learning items and appends them to study_plan.md"""
    result = study_updater_agent.invoke({
        "messages": [("user", "Update the study plan based on the gap report.")]
    })
    return {"messages": result["messages"]}

