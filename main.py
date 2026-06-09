"""
This is the orchestrator for the agents. It runs the pipeline 
"""
from agents.scraper import run_scraper_agent
from agents.analyst import run_analyst_agent

state = {
    "search_query": "Senior AI Engineer UK",
    "scored_jds": [],
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
    # Agent 1 - Scrapping jobs with search_query
    # run_scraper_agent(state["search_query"])

    # Agent 2
    scored_jds = run_analyst_agent()
    state["scored_jds"] = scored_jds

    # Human checkpoint
    state["approved_paths"] = human_checkpoint(scored_jds)