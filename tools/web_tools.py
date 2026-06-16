"""
This code is used for scraper agent to do web search and scrape pages. 

"""
from firecrawl import FirecrawlApp
from datetime import datetime, timedelta

import os
import logging


logging.basicConfig(level=logging.INFO)

# Tell Firecrawl to only search these job sites. 
JOB_SITES = [                                                                                                                                                                                                                             
    "indeed.com",
    "wellfound.com",                                                                                                                                                                                                                      
    "cwjobs.co.uk",
    "technojobs.co.uk",
]                                                                                                                                                                                                                                         
   

def web_search(query: str, limit: int=5, days_ago: int=7) -> list[dict]:
    """Search for job listings matching the query. Returns a list of results with title, url, and snippet."""
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    since_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    sites = " OR ".join([f'site:{site}' for site in JOB_SITES])                                                                                                                                                                                
    full_query = f"{query} ({sites}) after:{since_date}"                     
    results = app.search(query=full_query, limit=limit)
    return [
        {                                                                                                                                                                                                    
            "title": r.title or "",
            "url": r.url or "",                                                                                                                                                                                                                   
            "snippet": r.description or ""
        }
        for r in results.web
    ]

def scrape_page(url: str) -> str:
    """Scrape the full job description text from a URL. Returns markdown content."""
    logging.info(f"Scraping page: {url}")
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    result = app.scrape(url=url, formats=["markdown"])
    return result.markdown or ""    
