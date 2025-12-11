"""Tests for voting_history.py vote recording (MIGRATED TO SQLITE)."""

import pytest
from backend.voting_history import record_votes
from backend import models

class TestVotingHistory:
    """Tests for voting history functions using SQLite."""

    def test_record_votes(self, tenant_db_session):
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

        # Verify DB insertions
        votes = tenant_db_session.query(models.Vote).filter_by(conversation_id=conversation_id).all()
        # Total rows = 6 (2 voters * 3 rankings each)
        assert len(votes) == 6
        
        # Check first vote
        vote1 = next(v for v in votes if v.voter_model == "voter1")
        assert vote1.voter_model == "voter1"
        # Since 'personality_name' is not stored in DB (we store ID), let's check what we store.
        # voting_history.py: voter_personality_id=voter_personality_id (from stage2 result)
        # The test provided personality_name but record_votes looks for personality_id or fallback.
        # Let's check logic: voter_personality_id = result.get("personality_id")
        # In test payload: "personality_name": "Personality1" -> NO "personality_id"
        # So personality_id should be None in DB.
        
        assert vote1.voter_personality_id is None
        
        # Rankings are simpler rows now? No, wait. 
        # models.py says: rank=Integer, label=String. Each vote is ONE ROW per ranking? 
        # voting_history.py says: 
        # for result in stage2_results:
        #    for rank, label in enumerate(parsed_ranking):
        #        vote = Vote(...)
        #        votes_to_insert.append(vote)
        
        # So one "Vote" model instance = ONE ranked item per voter.
        # stage2_results has 2 voters.
        # Voter 1 parsed_ranking has 3 items.
        # Voter 2 parsed_ranking has 3 items.
        # Total rows = 6.
        
        # Let's re-verify count.
        assert len(votes) == 6
        
        # Check specific row
        # Voter 1 ranked Response A as #1
        vote_v1_r1 = next(v for v in votes if v.voter_model == "voter1" and v.rank == 1)
        assert vote_v1_r1.label == "Response A"
        assert vote_v1_r1.candidate_model == "ModelA"  # from label_to_model
        
    def test_record_votes_empty_rankings(self, tenant_db_session):
        """Test handling of empty rankings."""
        stage2_results = []
        label_to_model = {}

        # Should not raise error, but should not create entries
        record_votes("test-conv-empty", stage2_results, label_to_model, org_id="org1")

        count = tenant_db_session.query(models.Vote).filter_by(conversation_id="test-conv-empty").count()
        assert count == 0

    def test_record_votes_with_missing_labels(self, tenant_db_session):
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

        votes = tenant_db_session.query(models.Vote).filter_by(conversation_id=conversation_id).all()
        
        # Response X should be skipped because target_info is None
        # So only 2 votes (A and B)
        assert len(votes) == 2
        
        labels = [v.label for v in votes]
        assert "Response A" in labels
        assert "Response B" in labels
        assert "Response X" not in labels

    # load_voting_history is deprecated and returns [], so no point testing it extensively
    # unless we want to verify it returns empty list.
    def test_load_voting_history_deprecated(self):
        from backend.voting_history import load_voting_history
        assert load_voting_history("org1") == []

    def test_record_votes_multiple_sessions(self, tenant_db_session):
        """Test recording multiple voting sessions."""
        label_to_model = {"Response A": "ModelA"}

        # Session 1
        record_votes(
            "conv-1",
            [{"model": "v1", "parsed_ranking": ["Response A"]}],
            label_to_model,
            turn_number=1,
            org_id="org1",
        )

        # Session 2
        record_votes(
            "conv-1",
            [{"model": "v1", "parsed_ranking": ["Response A"]}],
            label_to_model,
            turn_number=2,
            org_id="org1",
        )

        votes = tenant_db_session.query(models.Vote).filter_by(conversation_id="conv-1").all()
        assert len(votes) == 2
        
        turns = [v.turn_number for v in votes]
        assert 1 in turns
        assert 2 in turns


