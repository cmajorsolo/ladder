"""
This code is used for all agents to read files, save job descriptions, save analysis results, and write gap report etc. 

"""

import json
import logging
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "JD")

def save_jd(jd: dict) -> str:
    """Save a structured job description to disk as both .md and .json. Returns the .md file path."""
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

def read_profile()->str:
    """Read the candidate profile from my_profile.md."""
    profile_path = os.path.join(os.path.dirname(__file__), "..", "data", "my_profile.md")
    with open(profile_path, "r") as f:
        return f.read()

def write_gap_report(gaps: list[dict]) -> str:
    """Write gap_report.md and gap_report.json from a list of gap dicts.
    Each gap dict: {skill, frequency, priority, status}
    Returns the path to gap_report.json.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    data_dir = os.path.abspath(data_dir)

    # Write JSON for Agent 4
    json_path = os.path.join(data_dir, "gap_report.json")
    with open(json_path, "w") as f:
        json.dump(gaps, f, indent=2)

    # Write Markdown for human review
    md_path = os.path.join(data_dir, "gap_report.md")
    with open(md_path, "w") as f:
        f.write("# Gap Report\n\n")
        f.write("| Skill | Frequency | Priority | Status |\n")
        f.write("|---|---|---|---|\n")
        for g in gaps:
            f.write(f"| {g['skill']} | {g['frequency']} | {g['priority']} | {g['status']} |\n")

    logging.info(f"[write_gap_report] saved to: {json_path}")
    return json_path

def read_file(path: str) -> str:
    """Read any file and return its contents as a string."""
    abs_path = os.path.abspath(path)
    with open(abs_path, "r") as f:
        return f.read()

def append_to_study_plan(content: str) -> str:
    """Append new learning items to study_plan.md under a Gap-Driven Learning Items section."""
    study_plan_path = os.path.join(os.path.dirname(__file__), "..", "data", "study_plan.md")
    study_plan_path = os.path.abspath(study_plan_path)
    logging.info(f"[append_to_study_plan] writing to: {study_plan_path}")
    logging.info(f"[append_to_study_plan] file exists: {os.path.exists(study_plan_path)}")
    with open(study_plan_path, "a") as f:
        f.write("\n\n## Gap-Driven Learning Items\n")
        f.write("> Auto-generated by Agent 4 based on gap_report.json\n\n")
        f.write(content)
    logging.info(f"[append_to_study_plan] done")
    return study_plan_path