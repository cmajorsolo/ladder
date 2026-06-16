"""   
  Gap analyser node for LangGraph.
  Reads approved JDs and the candidate profile, identifies skill gaps,
  and writes gap_report.md and gap_report.json.
"""

from langgraph.prebuilt import create_react_agent 
from state import LadderState
from tools.file_tools import read_jd, read_profile, write_gap_report

gap_analyser_agent = create_react_agent(
    model="claude-haiku-4-5-20251001",    
    tools=[read_jd, read_profile, write_gap_report],
    prompt=(
          "You are a gap analyst. Your task is analyse the skill gaps for the approved JDs. Steps:"
          "1. Call read_profile to get the candidate profile. "
          "2. Call read_jd for each approved JD path provided. "
          "3. Aggregate all required skills across JDs — count frequency per skill. "
          "4. Compare against the profile — mark each skill as 'gap', 'partial', or 'have'. "
          "5. Set priority: 'high' if frequency >= 3, 'medium' if 2, 'low' if 1. "
          "6. Call write_gap_report once with all gaps sorted by frequency descending. Then stop."
    )
)

def gap_analyst_node(state: LadderState) -> dict:
    """LangGraph node — analyses skill gaps between approved JDs and the candidate profile."""    
    approved_paths = state["approved_paths"]
    result = gap_analyser_agent.invoke({
        "messages": [("user", f"Analyse skill gaps for these approved JDs: {approved_paths}")]
    })
    return {"messages": result["messages"]}