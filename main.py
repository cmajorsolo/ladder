"""
This is the orchestrator for the agents. It runs the pipeline 
"""
from agents.scraper import run_scraper_agent
from agents.analyst import run_analyst_agent
from agents.gap_analyser import run_gap_analyser_agent

state = {
    "search_query": "Senior AI Engineer UK",
    "scored_jds": [],
    "approved_paths": [],
    "gap_report_path": "",
}

def human_checkpoint(scored_jds: list[dict]) -> list[str]:
    """Show ranked JDs and ask human to approve a shortlist."""                                                                                              
    print("\n=== RANKED JDs — REVIEW AND APPROVE ===\n")
    for i, jd in enumerate(scored_jds):                                                                                                                           
        print(f"[{i+1}] {jd['score']:>3}/100  {jd['title']} @ {jd['company']}")
        print(f"      {jd['reasoning']}\n")                                                                                                                       
                
    print("Type the numbers to approve, e.g: 1,3  or 'all'")                                                                                                      
    user_input = input("Approve: ").strip().lower()
                                                                                                                                                                
    if user_input == "all":
        approved = scored_jds                                                                                                                                     
    else:       
        indices = [int(x.strip()) - 1 for x in user_input.split(",")]
        approved = [scored_jds[i] for i in indices]                                                                                                               

    # Return the JD file paths for approved JDs                                                                                                                   
    approved_paths = [jd["path"] for jd in approved]
    print(f"\nApproved {len(approved_paths)} JDs: {approved_paths}")                                                                                              
    return approved_paths

if __name__ == "__main__":
    ## Agent 1 - Scrapping jobs with search_query
    # run_scraper_agent(state["search_query"])

    ## Agent 2
    # scored_jds = run_analyst_agent()
    # state["scored_jds"] = scored_jds

    # # Human checkpoint
    # state["approved_paths"] = human_checkpoint(scored_jds)

    # Agent 3 - Gap Analyser (hardcoded paths for isolated testing)
    state["approved_paths"] = [
        "data/JD/JD1_Sr._Forward_Deployed_AI_Engineer_(Remote_Eligible_in_the_UK)_Smartsheet.json",
        "data/JD/JD2_Senior_AI_Engineer_TalentHub_Global_Ltd.json",
        "data/JD/JD3_Senior_AI_Engineer_INSIGHT_INTERNATIONAL_UK_LTD.json",
        "data/JD/JD4_Senior_ML_&_AI_Engineer_Beatport.json",
    ]
    run_gap_analyser_agent(state["approved_paths"])