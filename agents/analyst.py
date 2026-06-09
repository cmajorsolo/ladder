"""
Agent for analysing the scraped job descriptions and extracting key information such as required skills, experience, and job responsibilities.

The agent is designed to:
    1. Reads all JD JSON files from data/JD/                                                                                                                                                                                 
    2. Reads the relevant section of my_profile.md (skills + gaps table — not the whole file)                                                                                                                                
    3. Scores each JD 0–100 for fit against your profile                                     
    4. Returns a ranked list with scores and reasoning  
The output of this agent is: 
    - 
"""
import anthropic
import json
import logging

from dotenv import load_dotenv
from tools.file_tools import list_jds, read_jd, save_scored_jds

load_dotenv()
logging.basicConfig(level=logging.INFO)
client = anthropic.Client()

PROFILE_SKILLS = """                                                                                                                                                                                                     
    ## Technical Skills
    - Python (strong), C#/.NET, JavaScript/ReactJS                                                                                                                                                                           
    - Deep learning: LSTM, Transformer (PyTorch)
    - AWS SageMaker, Kubernetes, Docker                                                                                                                                                                                      
    - RAG, sentiment analysis, time series forecasting (PhD level)
    - LangChain/multi-agent (in progress)                                                                                                                                                                                    
                    
    ## Gaps                                                                                                                                                                                                                  
    - LangGraph: in progress
    - MCP: not started                                                                                                                                                                                                       
    - TypeScript: partial
    - AWS Lambda/CDK: partial                                                                                                                                                                                                
    - LLM APIs in production: partial
    - Agent observability (LangSmith): gap
"""  

TOOLS = [
    {
        "name": "list_jds",
        "description": "List all saved JD file paths.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "read_jd",
        "description": "Read a JD JSON file by path and return its contents.",
        "input_schema": { 
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The full path to the JD JSON file."
                }
            },
            "required": ["path"]
        },
    }
]
MAX_ITERATIONS = 10  # To prevent infinite loops, we set a max iteration limit for the agent. Adjust as needed.

def run_analyst_agent() -> list[dict]:
    messages = [
        {
            "role": "user",
            "content": (
                "List all saved job descriptions, read each one, "
                "and score each JD from 0 to 100 based on fit against this profile: \n\n"
                f"{PROFILE_SKILLS}\n\n"
                "For each JD return: id, title, company, score (0-100), path (the file path to the JD JSON), and 2-3 sentences of reasoning."
                "Return the final result as a JSON array sorted by score descending."
            )
        }
    ]

    i = 0    
    while i < MAX_ITERATIONS:
        i += 1
        logging.info(f"Analyst agent iteration {i}/{MAX_ITERATIONS}")
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=(
                "You are a JD analyst."    
                "1. Call list_jds to get all JD file paths."
                "2. Call read_jd for each path."
                "3. Score each JD against the provided profile."
                "4. Return a JSON array of scored JDs sorted by score. Then Stop."
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
            for tool_use in [b for b in response.content if b.type=="tool_use"]:
                if tool_use.name == "list_jds":
                    result = list_jds()
                elif tool_use.name == "read_jd":
                    result = read_jd(tool_use.input["path"])
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(result)
                })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            logging.info(f"Analyst done. stop_reason={response.stop_reason}")
            # Extract the JSON from Claude's final text response
            final_text = next(b.text for b in response.content if b.type == "text")
            # Parse the JSON array from Claude's response
            start = final_text.find("[")
            end = final_text.rfind("]") + 1
            scored_jds = json.loads(final_text[start:end])
            # Save for Agent 3 and human review                                                                                                                         
            save_scored_jds(scored_jds)                                                                                                                                   
                                                                                                                                                                  
            # Print ranked list for human checkpoint                                                                                                                      
            print("\n=== RANKED JDs ===")
            for jd in scored_jds:                                                                                                                                         
                print(f"{jd['score']:>3}/100  {jd['title']} @ {jd['company']}")                                                                                         
                print(f"       {jd['reasoning']}\n")                                                                                                                      
   
            return scored_jds
