from unittest.mock import MagicMock, mock_open, patch

import pytest

from backend.config.consensus_strategies import ConsensusStrategyService
from backend.models import ConsensusStrategy


@pytest.fixture
def mock_session():
    return MagicMock()


def test_get_all_strategies_merges_system_and_db(mock_session):
    # Mock DB results
    db_strat = ConsensusStrategy(
        id="custom_1",
        display_name="Custom Strat",
        description="Desc",
        prompt_content="Custom Prompt",
    )
    mock_session.query.return_value.all.return_value = [db_strat]

    # Mock System Files
    with (
        patch("os.path.exists", return_value=True),
        patch("os.listdir", return_value=["sys_1.md"]),
        patch("builtins.open", mock_open(read_data="System Prompt")),
    ):
        strategies = ConsensusStrategyService.get_all_strategies(mock_session, "org1")

        assert len(strategies) == 2
        # Check Custom
        custom = next(s for s in strategies if s["id"] == "custom_1")
        assert custom["source"] == "custom"
        assert custom["prompt_content"] == "Custom Prompt"

        # Check System
        system = next(s for s in strategies if s["id"] == "sys_1")
        assert system["source"] == "system"
        assert system["prompt_content"] == "System Prompt"


def test_get_strategy_db_priority(mock_session):
    # If DB has it, return DB version (shadowing not implemented yet, but simpler logic here)
    # Actually service logic checks DB first.
    db_strat = ConsensusStrategy(id="target", display_name="Hit", prompt_content="DB Content")
    mock_session.query.return_value.filter_by.return_value.first.return_value = db_strat

    strat = ConsensusStrategyService.get_strategy(mock_session, "target")
    assert strat["source"] == "custom"
    assert strat["prompt_content"] == "DB Content"


def test_create_custom_strategy(mock_session):
    # Mock no system conflict
    with patch("os.path.exists", return_value=False):
        # Mock no DB conflict
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = ConsensusStrategyService.create_custom_strategy(
            mock_session, "new_id", "New", "Content", "Desc"
        )

        assert result["id"] == "new_id"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
