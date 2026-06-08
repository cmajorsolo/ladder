"""
This is the orchestrator for the agents. It runs the pipeline 
"""
from agents.scraper import run_scraper_agent

state = {
    "search_query": "Senior AI Engineer UK remote",
    "job_descriptions": [],
    "scored_jds": [],
    "approved_paths": [],
    "gap_report_path": "",
}

if __name__ == "__main__":
    results = run_scraper_agent(state["search_query"])