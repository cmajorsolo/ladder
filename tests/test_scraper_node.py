"""
Unit test for the scraper node.
Tests that the node acepts LadderState and returns updated messages. 
"""

import pytest 
from unittest.mock import patch
from nodes.scraper import scraper_node 

@pytest.fixture
def initial_state():
    return {
        "search_query": "Senior AI Engineer UK remote",
        "messages": [],
        "scored_jds": [],
        "approved_paths": [],
        "gap_report_path": "",
    }

def test_scraper_node_passes_search_query(initial_state):
    """Node should pass the search_query from state to the agent."""
    mock_result = {"messages": [("assistant", "Done.")]}

    with patch("nodes.scraper.scraper_agent.invoke", return_value=mock_result) as mock_invoke:
        scraper_node(initial_state)
    
    call_args = mock_invoke.call_args[0][0]
    assert call_args["messages"][0] == ("user", "Senior AI Engineer UK remote")

def test_scraper_node_returns_messages(initial_state):
    """Node should return a dict with updated messages."""
    mock_result = {
        "messages": [("assistant", "I found 3 jobs and saved them.")]
    }
    with patch("nodes.scraper.scraper_agent.invoke", return_value=mock_result):
        result = scraper_node(initial_state)

    assert "messages" in result
    assert len(result["messages"]) > 0

