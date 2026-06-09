"""
This code is used for all agents to read files, save job descriptions, save analysis results, and write gap report etc. 

"""

import json
import logging
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "JD")

def save_jd(jd:dict)->str:
    resolved = os.path.abspath(DATA_DIR)
    logging.info(f"[save_jd] saving to: {resolved}")
    os.makedirs(DATA_DIR, exist_ok=True)

    # Auto-increment ID based on existing files 
    existing = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    jd_id = f"JD{len(existing)+1}"
    
    safe_title = jd.get("title", "Unknown").replace(" ", "_")
    safe_company = jd.get("company", "Unknown").replace(" ", "_")
    base_name = f"{jd_id}_{safe_title}_{safe_company}"

    jd["id"] = jd_id

    # Save JSON for the agents to easily understand and use 
    json_path = os.path.join(DATA_DIR, f"{base_name}.json")
    with open(json_path, "w") as f:
        json.dump(jd, f, indent=2)

    # save markdown for human to read and review
    md_path = os.path.join(DATA_DIR, f"{base_name}.md") 
    with open(md_path, "w") as f:
        f.write(f"# {jd.get('title', 'Unknown')} — {jd.get('company', 'Unknown')}\n\n")                                                                                                                                                   
        f.write(f"**Rate:** {jd.get('rate', 'Not specified')}\n\n")                                                                                                                                                                       
        f.write(f"**Contract:** {jd.get('contract_type', 'Not specified')}\n\n")                                                                                                                                                          
        f.write(f"**Required:** {', '.join(jd.get('required', []))}\n\n")                                                                                                                                                                 
        f.write(f"**Nice to have:** {', '.join(jd.get('nice_to_have', []))}\n\n")                                                                                                                                                         
        f.write(f"**Stack:** {', '.join(jd.get('stack', []))}\n\n")                                                                                                                                                                       
        f.write(f"**URL:** {jd.get('url', '')}\n")    

    return md_path

def read_jd(json_path:str)->dict:
    '''Read a JD JSON file and return its contents.'''
    with open(json_path, "r") as f:
        return json.load(f)

def list_jds()->list[dict]:
    '''Return all JD JSON file paths in the JD folder'''
    return [
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if f.endswith(".json")
    ]

def save_scored_jds(scored_jds: list[dict]) -> str:
    """Save Agent 2's scored and ranked JD list to data/scored_jds.json."""
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "scored_jds.json")
    output_path = os.path.abspath(output_path)
    with open(output_path, "w") as f:
        json.dump(scored_jds, f, indent=2)
    logging.info(f"[save_scored_jds] saved to: {output_path}")
    return output_path