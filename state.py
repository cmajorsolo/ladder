'''
    state.py is a standardized definition of the state structure used across agents. 
    
    It defines the keys and types of data that will be stored in the state dictionary, 
    ensuring consistency and clarity when agents read from or write to the state. 
    
    It is single source of truth, you change it in one place and all nodes pick it up automatically.
    
'''

from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class LadderState(TypedDict):
    search_query: str
    messages: Annotated[list, add_messages] # agent message history
    scored_jds: list[dict]
    approved_paths: list[str]
    gap_report_path: str