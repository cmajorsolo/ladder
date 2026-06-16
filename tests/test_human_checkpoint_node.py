"""
Unit tests for the human checkpoint node.
interrupt() is mocked to simulate human decisions without pausing the graph.
The logic under test is the approval branching inside the node itself.
"""

import pytest
from unittest.mock import patch
from nodes.human_checkpoint import human_checkpoint_node


@pytest.fixture
def scored_jds():
    return [
        {"path": "data/JD/JD1.json", "title": "Senior AI Engineer", "company": "Acme", "score": 90},
        {"path": "data/JD/JD2.json", "title": "ML Engineer", "company": "Beta", "score": 75},
        {"path": "data/JD/JD3.json", "title": "AI Lead", "company": "Gamma", "score": 60},
    ]


@pytest.fixture
def initial_state(scored_jds):
    return {
        "search_query": "Senior AI Engineer UK remote",
        "messages": [],
        "scored_jds": scored_jds,
        "approved_paths": [],
        "gap_report_path": "",
    }


def test_approve_all(initial_state, scored_jds):
    """When human types 'all', all JD paths should be approved."""
    with patch("nodes.human_checkpoint.interrupt", return_value="all"):
        result = human_checkpoint_node(initial_state)

    assert result["approved_paths"] == [jd["path"] for jd in scored_jds]


def test_approve_by_index(initial_state, scored_jds):
    """When human types '1, 3', only JDs at index 0 and 2 should be approved."""
    with patch("nodes.human_checkpoint.interrupt", return_value="1, 3"):
        result = human_checkpoint_node(initial_state)

    assert result["approved_paths"] == [scored_jds[0]["path"], scored_jds[2]["path"]]


def test_approve_single(initial_state, scored_jds):
    """When human types '2', only the second JD should be approved."""
    with patch("nodes.human_checkpoint.interrupt", return_value="2"):
        result = human_checkpoint_node(initial_state)

    assert result["approved_paths"] == [scored_jds[1]["path"]]


def test_interrupt_receives_scored_jds(initial_state, scored_jds):
    """interrupt() should be called with the scored_jds from state."""
    with patch("nodes.human_checkpoint.interrupt", return_value="all") as mock_interrupt:
        human_checkpoint_node(initial_state)

    call_args = mock_interrupt.call_args[0][0]
    assert call_args["scored_jds"] == scored_jds


def test_returns_approved_paths_key(initial_state):
    """Node should return a dict with the approved_paths key."""
    with patch("nodes.human_checkpoint.interrupt", return_value="all"):
        result = human_checkpoint_node(initial_state)

    assert "approved_paths" in result
