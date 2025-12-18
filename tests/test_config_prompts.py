from backend.config.prompts import load_consensus_prompt


def test_load_balanced_prompt():
    """Verify that the balanced consensus prompt loads correctly."""
    prompt = load_consensus_prompt("balanced")
    assert prompt is not None
    assert "ERROR" not in prompt
    assert "# Instructions" in prompt
    assert "contributors" in prompt  # Ensure JSON instruction is present


def test_load_missing_prompt_fallbacks():
    """Verify fallback behavior for missing prompt."""
    # Should fallback to balanced
    prompt = load_consensus_prompt("non_existent_strategy")
    assert "ERROR" not in prompt
    assert "# Instructions" in prompt
