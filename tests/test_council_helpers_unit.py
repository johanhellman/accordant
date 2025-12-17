"""Direct unit tests for council_helpers.py helper functions.

These tests directly test helper functions to ensure they are covered
by test coverage metrics.
"""

import datetime
from unittest.mock import patch

from backend.council_helpers import (
    build_llm_history,
    build_message_chain,
    build_ranking_prompt,
    get_system_time_instruction,
    get_time_instructions,
    get_user_time_instruction,
    prepare_history_context,
)


class TestGetTimeInstructions:
    """Tests for get_time_instructions function."""

    def test_get_time_instructions_returns_tuple(self):
        """Test get_time_instructions returns a tuple of two strings."""
        system_instruction, user_instruction = get_time_instructions()

        assert isinstance(system_instruction, str)
        assert isinstance(user_instruction, str)
        assert "Current System Time:" in system_instruction
        assert "[SYSTEM NOTE:" in user_instruction

    def test_get_time_instructions_includes_timestamp(self):
        """Test get_time_instructions includes current timestamp."""
        # Patch the datetime CLASS in the module where it is imported
        with patch("backend.council_helpers.datetime") as mock_datetime:
            mock_now = datetime.datetime(2025, 12, 8, 15, 30, 45)
            # Configure the mock CLASS's now() method (mock_datetime.datetime.now)
            mock_datetime.datetime.now.return_value = mock_now
            # Ensure strftime works on the return value (it's a real datetime so it does)

            system_instruction, user_instruction = get_time_instructions()

            assert "2025-12-08 15:30:45" in system_instruction
            assert "2025-12-08 15:30:45" in user_instruction


class TestGetSystemTimeInstruction:
    """Tests for get_system_time_instruction function."""

    def test_get_system_time_instruction_returns_string(self):
        """Test get_system_time_instruction returns a string."""
        instruction = get_system_time_instruction()

        assert isinstance(instruction, str)
        assert "Current System Time:" in instruction

    def test_get_system_time_instruction_calls_get_time_instructions(self):
        """Test get_system_time_instruction calls get_time_instructions."""
        with patch("backend.council_helpers.get_time_instructions") as mock_get_time:
            mock_get_time.return_value = ("system", "user")
            result = get_system_time_instruction()

            mock_get_time.assert_called_once()
            assert result == "system"


class TestGetUserTimeInstruction:
    """Tests for get_user_time_instruction function."""

    def test_get_user_time_instruction_returns_string(self):
        """Test get_user_time_instruction returns a string."""
        instruction = get_user_time_instruction()

        assert isinstance(instruction, str)
        assert "[SYSTEM NOTE:" in instruction

    def test_get_user_time_instruction_calls_get_time_instructions(self):
        """Test get_user_time_instruction calls get_time_instructions."""
        with patch("backend.council_helpers.get_time_instructions") as mock_get_time:
            mock_get_time.return_value = ("system", "user")
            result = get_user_time_instruction()

            mock_get_time.assert_called_once()
            assert result == "user"


class TestPrepareHistoryContext:
    """Tests for prepare_history_context function."""

    def test_prepare_history_context_excludes_last_user_message(self):
        """Test prepare_history_context excludes last user message if present."""
        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
        ]

        result = prepare_history_context(history)

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
        assert "Second question" not in [msg["content"] for msg in result]

    def test_prepare_history_context_keeps_all_if_last_not_user(self):
        """Test prepare_history_context keeps all messages if last is not user."""
        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
        ]

        result = prepare_history_context(history)

        assert len(result) == 2
        assert result == history

    def test_prepare_history_context_empty_list(self):
        """Test prepare_history_context handles empty list."""
        result = prepare_history_context([])

        assert result == []

    def test_prepare_history_context_single_user_message(self):
        """Test prepare_history_context handles single user message."""
        history = [{"role": "user", "content": "Question"}]

        result = prepare_history_context(history)

        assert result == []


class TestBuildMessageChain:
    """Tests for build_message_chain function."""

    def test_build_message_chain_basic(self):
        """Test build_message_chain creates basic message chain."""
        system_prompt = "You are helpful."
        history = []
        user_query = "What is Python?"

        result = build_message_chain(system_prompt, history, user_query)

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == system_prompt
        assert result[1]["role"] == "user"
        assert result[1]["content"] == user_query

    def test_build_message_chain_with_history(self):
        """Test build_message_chain includes history."""
        system_prompt = "You are helpful."
        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
        ]
        user_query = "What is Python?"

        result = build_message_chain(system_prompt, history, user_query)

        assert len(result) == 4
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"
        assert result[3]["role"] == "user"
        assert result[3]["content"] == user_query

    def test_build_message_chain_excludes_last_user_from_history(self):
        """Test build_message_chain excludes last user message from history."""
        system_prompt = "You are helpful."
        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
        ]
        user_query = "What is Python?"

        result = build_message_chain(system_prompt, history, user_query)

        # Should exclude last user message from history
        assert len(result) == 4  # system + 2 history messages + user_query
        assert result[1]["content"] == "First question"
        assert result[2]["content"] == "First answer"
        assert result[3]["content"] == user_query
        assert "Second question" not in [msg["content"] for msg in result]


class TestBuildRankingPrompt:
    """Tests for build_ranking_prompt function."""

    def test_build_ranking_prompt_basic(self):
        """Test basic prompt construction."""
        user_query = "What is Python?"
        responses_text = "Response A: ...\nResponse B: ..."
        template = "Rank {user_query}. {responses_text}. {peer_text}"

        result = build_ranking_prompt(user_query, responses_text, prompt_template=template)

        assert user_query in result
        assert responses_text in result
        assert "different models (anonymized)" in result

    def test_build_ranking_prompt_exclude_self(self):
        """Test with exclude_self=True."""
        user_query = "What is Python?"
        responses_text = "Response A: Answer"
        template = "Rank {user_query}. {peer_text}"

        result = build_ranking_prompt(
            user_query, responses_text, exclude_self=True, prompt_template=template
        )

        assert "your peers" in result.lower()

    def test_build_ranking_prompt_custom_template(self):
        """Test build_ranking_prompt uses custom template when provided."""
        user_query = "What is Python?"
        responses_text = "Response A: Answer 1"
        custom_template = "Custom ranking instructions: {user_query}"

        result = build_ranking_prompt(user_query, responses_text, prompt_template=custom_template)

        assert "Custom ranking instructions" in result
        assert user_query in result


class TestBuildLlmHistory:
    """Tests for build_llm_history function."""

    def test_build_llm_history_basic(self):
        """Test build_llm_history converts messages to LLM format."""
        messages = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "stage3": {"response": "Answer 1"}},
        ]

        result = build_llm_history(messages)

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Question 1"
        assert result[1]["role"] == "assistant"
        assert result[1]["content"] == "Answer 1"

    def test_build_llm_history_sliding_window(self):
        """Test build_llm_history applies sliding window."""
        # Create more than max_turns * 2 messages
        messages = []
        for i in range(25):  # 25 messages = 12.5 turns, more than default max_turns=10
            if i % 2 == 0:
                messages.append({"role": "user", "content": f"Question {i // 2 + 1}"})
            else:
                messages.append(
                    {"role": "assistant", "stage3": {"response": f"Answer {i // 2 + 1}"}}
                )

        result = build_llm_history(messages, max_turns=10)

        # Should keep last 10 turns = 20 messages
        assert len(result) == 20

    def test_build_llm_history_filters_non_relevant_messages(self):
        """Test build_llm_history filters out non-user/assistant messages."""
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "system", "content": "System message"},  # Should be filtered
            {"role": "assistant", "stage3": {"response": "Answer"}},
        ]

        result = build_llm_history(messages)

        assert len(result) == 2
        assert all(msg["role"] in ("user", "assistant") for msg in result)

    def test_build_llm_history_extracts_part2_final_answer(self):
        """Test build_llm_history extracts PART 2: FINAL ANSWER section."""
        messages = [
            {"role": "user", "content": "Question"},
            {
                "role": "assistant",
                "stage3": {
                    "response": "PART 1: Analysis\n\nPART 2: FINAL ANSWER: This is the final answer"
                },
            },
        ]

        result = build_llm_history(messages)

        assert result[1]["content"] == "This is the final answer"

    def test_build_llm_history_handles_missing_stage3(self):
        """Test build_llm_history handles missing stage3 in assistant message."""
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer without stage3"},
        ]

        result = build_llm_history(messages)

        assert len(result) == 2
        assert result[1]["content"] == ""  # get("stage3", {}).get("response", "") returns ""

    def test_build_llm_history_empty_messages(self):
        """Test build_llm_history handles empty messages list."""
        result = build_llm_history([])

        assert result == []
