"""
Agent for scraping the latest job descriptions from the web. 

The agent is designed to:
    - Scrape the latest job descriptions from:
    -  
The output of this agent is: 
    - 
"""
import anthropic
import json
import logging

from dotenv import load_dotenv

from tools.web_tools import web_search, scrape_page
from tools.file_tools import save_jd

logging.basicConfig(level=logging.INFO)

load_dotenv()  # Load environment variables from .env file
client = anthropic.Client()
TOOLS = [
    {
        "name": "web_search",
        "description": "Use this tool to search for the latest AI Engineer job descriptions on the web. The input should be a search query string, and the output will be a list of job descriptions in JSON format.",
        "input_schema": { 
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query, e.g. 'Senior AI Engineer UK remote'"
                },
                "days_ago": {
                    "type": "integer",                                                                                                                                                                                                            
                    "description": "Only return results published within this many days. Default 7."
                } 
            },
            "required": ["query"]   # days_ago is optional 
        },
    },
    {
        "name": "scrape_page",
        "description": "Scrape the full job description text form a URL",
        "input_schema": { 
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the job listing page to scrape."
                }
            },
            "required": ["url"]
        },
    },
    {
        "name": "save_jd",
        "description": "Save a structured job description to disk after scraping. Call this once you have extracted the structured data from a job page.",
        "input_schema": { 
            "type": "object",
            "properties": {                                                                                                                                                                                                                   
              "title":         {"type": "string"},                                                                                                                                                                                        
              "company":       {"type": "string"},                                                                                                                                                                                          
              "rate":          {"type": "string"},
              "contract_type": {"type": "string"},                                                                                                                                                                                          
              "required":      {"type": "array", "items": {"type": "string"}},                                                                                                                                                              
              "nice_to_have":  {"type": "array", "items": {"type": "string"}},
              "stack":         {"type": "array", "items": {"type": "string"}},                                                                                                                                                              
              "url":           {"type": "string"}                                                                                                                                                                                           
          },
          "required": ["title", "company"]                
        },
    }
]
MAX_ITERATIONS = 10  # To prevent infinite loops, we set a max iteration limit for the agent. Adjust as needed.


def run_scraper_agent(query: str) -> list[dict]:
    """Runs the scraper agent with the given query and returns the scraped job descriptions."""
    # This is the message to Claude to tell it what we want it to do. 
    # It is like the prompt for a single-turn question, but here we can also specify the tools we have and how to use them.
    messages = [
        {"role": "user", "content": (
            f"Search for jobs matching: {query}. "
            "For each result, scrape the page using scrape_page to get the full job description. "
            "Then extract the structured data (title, company, rate, contract_type, required skills, nice_to_have, stack, url) "
            "and save it using the save_jd tool. Do this for each job found."
        )}
    ]

    i = 0    
    while i < MAX_ITERATIONS:
        i += 1
        logging.info(f"Scraper agent iteration {i}/{MAX_ITERATIONS}")
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            # When the max_tokens is too low, the tool calls may be truncated and the agent won't be able to complete the task. 
            # You can adjust this based on your needs and the expected length of the responses and tool calls.
            max_tokens=4096,
            # The system prompt is crucial for guiding the agent's behavior. 
            # Without this, the agent may keeps running as it thinks that no clear stop signal received. 
            # Here we explicitly tell it when to stop and to use the tools in a specific way to achieve our goal.
            system=(
                "You are a job scraping agent. Your job is: "
                "1. Call web_search once to find job listings. "
                "2. Call scrape_page for each URL to get the full job description. "
                "3. Call save_jd for each job to save the structured data. "
                "4. Once all jobs are saved, stop. Do not repeat any steps."
            ),
            tools=TOOLS,
            messages=messages
        )
        for block in response.content:
            if block.type == "text":
                logging.info(f"[Claude response]: {block.text}")
            elif block.type == "tool_use":
                logging.info(f"[Tool call] {block.name}({json.dumps(block.input, indent=2)})")

        #  Cluade wnats to call a tool
        # NOTE: "tool_use" means "I am still working on the answer, I might need to use tools to find the answer."
        if response.stop_reason == "tool_use":
            # Collect results for ALL tool calls in this response
            tool_results = []
            for tool_use in [b for b in response.content if b.type == "tool_use"]:
                tool_name = tool_use.name
                tool_input = tool_use.input

                logging.info(f"[Executing tool] {tool_name}")
                if tool_name == "web_search":
                    result = web_search(tool_input["query"], limit=100, days_ago=tool_input.get("days_ago", 7))
                elif tool_name == "scrape_page":
                    result = scrape_page(tool_input["url"])
                elif tool_name == "save_jd":
                    try:
                        md_path = save_jd(tool_input)
                        result = {"saved": md_path}
                        logging.info(f"[save_jd] saved to: {md_path}")
                    except Exception as e:
                        logging.error(f"[save_jd] failed: {e}")
                        result = {"error": str(e)}
                else:
                    logging.warning(f"[Unknown tool] {tool_name} — not handled")
                    result = {}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(result)
                })

            # Send ALL tool results back in one message
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            logging.info(f"Claude finished. stop_reason={response.stop_reason}")
            return