"""Tests for voting_history.py vote recording."""

import os
import tempfile

import pytest

from backend.voting_history import (
    load_voting_history,
    record_votes,
)


class TestVotingHistory:
    """Tests for voting history functions."""

    @pytest.fixture
    def temp_data_dir(self, monkeypatch):
        """Create a temporary data directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create data/conversations structure
            data_dir = os.path.join(tmpdir, "data")
            conversations_dir = os.path.join(data_dir, "conversations")
            os.makedirs(conversations_dir, exist_ok=True)
            # Patch config.DATA_DIR so voting_history uses the temp directory
            # Patch config.DATA_DIR so voting_history uses the temp directory
            # We need to mock ORGS_DATA_DIR since voting history is now org-scoped
            orgs_dir = os.path.join(tmpdir, "data", "organizations")
            os.makedirs(orgs_dir, exist_ok=True)
            monkeypatch.setattr("backend.voting_history.ORGS_DATA_DIR", orgs_dir)

            yield tmpdir

    def test_record_votes(self, temp_data_dir):
        """Test recording votes from Stage 2 results."""
        conversation_id = "test-conv-123"
        stage2_results = [
            {
                "model": "voter1",
                "personality_name": "Personality1",
                "parsed_ranking": ["Response A", "Response B", "Response C"],
            },
            {
                "model": "voter2",
                "personality_name": "Personality2",
                "parsed_ranking": ["Response B", "Response A", "Response C"],
            },
        ]
        label_to_model = {"Response A": "ModelA", "Response B": "ModelB", "Response C": "ModelC"}

        record_votes(
            conversation_id,
            stage2_results,
            label_to_model,
            conversation_title="Test Conversation",
            turn_number=1,
            org_id="org1",
        )

        history = load_voting_history("org1")
        # Find the session we just created
        session = next((s for s in history if s["conversation_id"] == conversation_id), None)
        assert session is not None
        assert session["conversation_id"] == conversation_id
        assert session["conversation_title"] == "Test Conversation"
        assert session["turn_number"] == 1
        assert "id" in session
        assert "timestamp" in session
        assert len(session["votes"]) == 2

        # Check first vote
        vote1 = session["votes"][0]
        assert vote1["voter_model"] == "voter1"
        assert vote1["voter_personality"] == "Personality1"
        assert len(vote1["rankings"]) == 3
        assert vote1["rankings"][0]["rank"] == 1
        assert vote1["rankings"][0]["candidate"] == "ModelA"
        assert vote1["rankings"][0]["label"] == "Response A"

    def test_record_votes_empty_rankings(self, temp_data_dir):
        """Test handling of empty rankings."""
        initial_history = load_voting_history("org1")
        initial_count = len(initial_history)

        stage2_results = []
        label_to_model = {}

        # Should not raise error, but should not create a session
        record_votes("test-conv-empty", stage2_results, label_to_model, org_id="org1")

        history = load_voting_history("org1")
        # Should be unchanged (no new session added)
        assert len(history) == initial_count

    def test_record_votes_with_missing_labels(self, temp_data_dir):
        """Test recording votes when some labels are missing from label_to_model."""
        conversation_id = "test-conv-missing"
        stage2_results = [
            {
                "model": "voter1",
                "parsed_ranking": [
                    "Response A",
                    "Response B",
                    "Response X",
                ],  # Response X not in mapping
            }
        ]
        label_to_model = {
            "Response A": "ModelA",
            "Response B": "ModelB",
            # Response X is missing
        }

        record_votes(conversation_id, stage2_results, label_to_model, org_id="org1")

        history = load_voting_history("org1")
        # Find the session we just created
        session = next((s for s in history if s["conversation_id"] == conversation_id), None)
        assert session is not None
        vote = session["votes"][0]
        # Should only include labels that are in label_to_model
        assert len(vote["rankings"]) == 2
        assert vote["rankings"][0]["candidate"] == "ModelA"
        assert vote["rankings"][1]["candidate"] == "ModelB"

    def test_get_voting_history(self, temp_data_dir):
        """Test retrieving voting history."""
        initial_history = load_voting_history("org1")
        initial_count = len(initial_history)

        # Record some votes
        stage2_results = [{"model": "voter1", "parsed_ranking": ["Response A", "Response B"]}]
        label_to_model = {"Response A": "ModelA", "Response B": "ModelB"}

        record_votes("conv-1", stage2_results, label_to_model, org_id="org1")

        # Retrieve history
        history = load_voting_history("org1")
        assert len(history) == initial_count + 1
        # Find the session we just created
        new_session = next((s for s in history if s["conversation_id"] == "conv-1"), None)
        assert new_session is not None
        assert new_session["conversation_id"] == "conv-1"

    def test_get_voting_history_multiple_sessions(self, temp_data_dir):
        """Test retrieving history with multiple voting sessions."""
        initial_history = load_voting_history("org1")
        initial_count = len(initial_history)

        label_to_model = {"Response A": "ModelA", "Response B": "ModelB"}

        # Record votes for conversation 1
        record_votes(
            "conv-1",
            [{"model": "v1", "parsed_ranking": ["Response A"]}],
            label_to_model,
            turn_number=1,
            org_id="org1",
        )

        # Record votes for conversation 2
        record_votes(
            "conv-2",
            [{"model": "v2", "parsed_ranking": ["Response B"]}],
            label_to_model,
            turn_number=1,
            org_id="org1",
        )

        # Record votes for conversation 1, turn 2
        record_votes(
            "conv-1",
            [{"model": "v1", "parsed_ranking": ["Response B"]}],
            label_to_model,
            turn_number=2,
            org_id="org1",
        )

        history = load_voting_history("org1")
        assert len(history) == initial_count + 3

        # Check that all sessions are present
        conv1_sessions = [s for s in history if s["conversation_id"] == "conv-1"]
        assert len(conv1_sessions) == 2
        assert conv1_sessions[0]["turn_number"] in [1, 2]
        assert conv1_sessions[1]["turn_number"] in [1, 2]

        conv2_sessions = [s for s in history if s["conversation_id"] == "conv-2"]
        assert len(conv2_sessions) == 1

    def test_record_votes_personality_name_fallback(self, temp_data_dir):
        """Test that personality_name falls back to model name if not provided."""
        stage2_results = [
            {
                "model": "voter1",
                # No personality_name field
                "parsed_ranking": ["Response A"],
            }
        ]
        label_to_model = {"Response A": "ModelA"}

        record_votes("conv-1", stage2_results, label_to_model, org_id="org1")

        history = load_voting_history("org1")
        # Find the session we just created
        new_session = next((s for s in history if s["conversation_id"] == "conv-1"), None)
        assert new_session is not None
        vote = new_session["votes"][0]
        assert vote["voter_personality"] == "voter1"  # Should fallback to model name
