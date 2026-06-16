"""
Unit tests for the gap analyst node.
Tests that the node invokes the agent with the correct message and returns updated messages.
"""
import pytest
from unittest.mock import patch
from nodes.gap_analyser import gap_analyst_node

@pytest.fixture
def initial_state():
    return {
        "search_query": "Senior AI Engineer UK remote",
        "messages": [],
        "scored_jds": [],
        "approved_paths": ["approved_path_1"],
        "gap_report_path": "",
    }

def test_gap_analyst_node_sends_correct_message(initial_state):
    """Node should invoke the agent with the hardcoded analyse instruction."""
    mock_result = {"messages": [("assistant", "Done.")]}

    with patch("nodes.gap_analyser.gap_analyser_agent.invoke", return_value=mock_result) as mock_invoke:
        gap_analyst_node(initial_state)
    call_args = mock_invoke.call_args[0][0]
    assert call_args["messages"][0] == ("user", "Analyse skill gaps for these approved JDs: ['approved_path_1']")

def test_gap_analyst_node_returns_messages(initial_state):
    """Node should return a dict with updated messages."""
    mock_result = {
        "messages": [("assistant", "Gap report generated.")]
    }

    with patch("nodes.gap_analyser.gap_analyser_agent.invoke", return_value=mock_result):
        result = gap_analyst_node(initial_state)

    assert "messages" in result
    assert len(result["messages"]) > 0

def test_gap_analyst_node_does_not_use_state_query(initial_state):
    """Gap analyst node ignores search_query — it reads approved paths from the approved_paths. """
    initial_state["search_query"] = "something completely different"
    mock_result = {"messages": [("assistant", "Done.")]}

    with patch("nodes.gap_analyser.gap_analyser_agent.invoke", return_value=mock_result) as mock_invoke:
        gap_analyst_node(initial_state)

    call_args = mock_invoke.call_args[0][0]
    # The message should always be the fixed instruction, not the search_query
    assert "Analyse skill gaps for these approved JDs" in call_args["messages"][0][1]