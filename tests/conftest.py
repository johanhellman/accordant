import pytest


@pytest.fixture
def mock_personalities():
    """Mock active personalities."""
    return [
        {
            "id": "personality1",
            "name": "Personality 1",
            "model": "openai/gpt-4",
            "personality_prompt": "You are helpful.",
            "temperature": 0.7,
        },
        {
            "id": "personality2",
            "name": "Personality 2",
            "model": "anthropic/claude-3",
            "personality_prompt": "You are analytical.",
            "temperature": 0.8,
        },
    ]


@pytest.fixture
def mock_system_prompts():
    """Mock system prompts."""
    return {
        "base_system_prompt": "You are a helpful assistant.",
        "ranking_prompt": "Rank {responses_text} for {user_query}",
        "chairman_prompt": "Synthesize {user_query} using {stage1_text} and {voting_details_text}",
        "title_prompt": "Generate a title for {user_query}",
    }


@pytest.fixture
def mock_models_config():
    """Mock models configuration."""
    return {
        "chairman_model": "gemini/gemini-pro",
        "title_model": "gemini/gemini-pro",
    }
