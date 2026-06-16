"""
Unit tests for the study updater node.
Tests that the node invokes the agent with the correct message and returns updated messages.
"""

import pytest
from unittest.mock import patch
from nodes.study_updater import study_updater_node


@pytest.fixture
def initial_state():
    return {
        "search_query": "Senior AI Engineer UK remote",
        "messages": [],
        "scored_jds": [],
        "approved_paths": [],
        "gap_report_path": "data/gap_report.json",
    }


def test_study_updater_node_sends_correct_message(initial_state):
    """Node should invoke the agent with the hardcoded update instruction."""
    mock_result = {"messages": [("assistant", "Done.")]}

    with patch("nodes.study_updater.study_updater_agent.invoke", return_value=mock_result) as mock_invoke:
        study_updater_node(initial_state)

    call_args = mock_invoke.call_args[0][0]
    assert call_args["messages"][0] == ("user", "Update the study plan based on the gap report.")


def test_study_updater_node_returns_messages(initial_state):
    """Node should return a dict with updated messages."""
    mock_result = {
        "messages": [("assistant", "Study plan updated with 3 new learning items.")]
    }

    with patch("nodes.study_updater.study_updater_agent.invoke", return_value=mock_result):
        result = study_updater_node(initial_state)

    assert "messages" in result
    assert len(result["messages"]) > 0


def test_study_updater_node_ignores_all_state_fields(initial_state):
    """Study updater reads gap_report.json from disk directly — ignores all state fields."""
    initial_state["gap_report_path"] = "some/other/path.json"
    initial_state["search_query"] = "something completely different"
    mock_result = {"messages": [("assistant", "Done.")]}

    with patch("nodes.study_updater.study_updater_agent.invoke", return_value=mock_result) as mock_invoke:
        study_updater_node(initial_state)

    call_args = mock_invoke.call_args[0][0]
    # Message is always the fixed instruction regardless of state contents
    assert call_args["messages"][0] == ("user", "Update the study plan based on the gap report.")
