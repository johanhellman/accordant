"""Additional edge case tests for council_helpers.py functions.

These tests cover edge cases and code paths that may not be fully covered
by existing tests to improve overall coverage.
"""

import pytest

from backend.council_helpers import (
    FINAL_RANKING_MARKER,
    RESPONSE_LABEL_PREFIX,
    build_llm_history,
    build_message_chain,
    build_ranking_prompt,
    calculate_aggregate_rankings,
    parse_ranking_from_text,
    prepare_history_context,
)


class TestParseRankingFromTextEdgeCases:
    """Additional edge case tests for parse_ranking_from_text."""

    def test_parse_ranking_final_marker_no_content_after(self):
        """Test parsing when FINAL_RANKING_MARKER exists but no content after."""
        ranking_text = f"Some text\n{FINAL_RANKING_MARKER}"

        result = parse_ranking_from_text(ranking_text)

        # Should fall back to finding Response X patterns in entire text
        assert isinstance(result, list)

    def test_parse_ranking_final_marker_single_part(self):
        """Test parsing when split results in only one part (edge case)."""
        # This shouldn't happen in practice, but test the code path
        ranking_text = FINAL_RANKING_MARKER

        result = parse_ranking_from_text(ranking_text)

        # Should fall back to finding Response X patterns
        assert isinstance(result, list)

    def test_parse_ranking_numbered_matches_with_spaces(self):
        """Test parsing numbered matches with various spacing."""
        ranking_text = f"""{FINAL_RANKING_MARKER}
1.{RESPONSE_LABEL_PREFIX}A
2.  {RESPONSE_LABEL_PREFIX}B
3.   {RESPONSE_LABEL_PREFIX}C"""

        result = parse_ranking_from_text(ranking_text)

        assert len(result) == 3
        assert result[0] == f"{RESPONSE_LABEL_PREFIX}A"
        assert result[1] == f"{RESPONSE_LABEL_PREFIX}B"
        assert result[2] == f"{RESPONSE_LABEL_PREFIX}C"

    def test_parse_ranking_numbered_matches_no_space_after_number(self):
        """Test parsing numbered matches without space after number."""
        ranking_text = f"""{FINAL_RANKING_MARKER}
1.{RESPONSE_LABEL_PREFIX}A
2.{RESPONSE_LABEL_PREFIX}B"""

        result = parse_ranking_from_text(ranking_text)

        assert len(result) == 2
        assert result[0] == f"{RESPONSE_LABEL_PREFIX}A"

    def test_parse_ranking_fallback_to_label_pattern(self):
        """Test fallback when numbered pattern doesn't match but labels exist."""
        ranking_text = f"""{FINAL_RANKING_MARKER}
{RESPONSE_LABEL_PREFIX}A is best
{RESPONSE_LABEL_PREFIX}B is second
{RESPONSE_LABEL_PREFIX}C is third"""

        result = parse_ranking_from_text(ranking_text)

        # Should extract labels in order they appear
        assert len(result) == 3
        assert result[0] == f"{RESPONSE_LABEL_PREFIX}A"
        assert result[1] == f"{RESPONSE_LABEL_PREFIX}B"
        assert result[2] == f"{RESPONSE_LABEL_PREFIX}C"

    def test_parse_ranking_multiple_final_marker_occurrences(self):
        """Test parsing when FINAL_RANKING_MARKER appears multiple times."""
        ranking_text = f"""First {FINAL_RANKING_MARKER}
1. {RESPONSE_LABEL_PREFIX}A
Second {FINAL_RANKING_MARKER}
2. {RESPONSE_LABEL_PREFIX}B"""

        result = parse_ranking_from_text(ranking_text)

        # Should use first occurrence and extract from there
        assert len(result) >= 1
        assert f"{RESPONSE_LABEL_PREFIX}A" in result or f"{RESPONSE_LABEL_PREFIX}B" in result

    def test_parse_ranking_response_labels_outside_marker(self):
        """Test parsing when Response labels exist outside FINAL_RANKING_MARKER section."""
        ranking_text = f"""Evaluation mentions {RESPONSE_LABEL_PREFIX}A and {RESPONSE_LABEL_PREFIX}B.

{FINAL_RANKING_MARKER}
1. {RESPONSE_LABEL_PREFIX}C
2. {RESPONSE_LABEL_PREFIX}D"""

        result = parse_ranking_from_text(ranking_text)

        # Should only extract labels from after the marker
        assert len(result) == 2
        assert result[0] == f"{RESPONSE_LABEL_PREFIX}C"
        assert result[1] == f"{RESPONSE_LABEL_PREFIX}D"
        # Labels before marker should not be included
        assert f"{RESPONSE_LABEL_PREFIX}A" not in result
        assert f"{RESPONSE_LABEL_PREFIX}B" not in result

    def test_parse_ranking_no_marker_fallback(self):
        """Test fallback parsing when no FINAL_RANKING_MARKER exists."""
        ranking_text = f"""Evaluation text.
1. {RESPONSE_LABEL_PREFIX}A
2. {RESPONSE_LABEL_PREFIX}B
3. {RESPONSE_LABEL_PREFIX}C"""

        result = parse_ranking_from_text(ranking_text)

        # Should extract all Response X patterns in order
        assert len(result) == 3
        assert result[0] == f"{RESPONSE_LABEL_PREFIX}A"
        assert result[1] == f"{RESPONSE_LABEL_PREFIX}B"
        assert result[2] == f"{RESPONSE_LABEL_PREFIX}C"

    def test_parse_ranking_whitespace_only(self):
        """Test parsing whitespace-only input."""
        result = parse_ranking_from_text("   \n\t  ")

        assert result == []

    def test_parse_ranking_mixed_case_labels(self):
        """Test parsing handles only uppercase Response labels (A-Z)."""
        ranking_text = f"""{FINAL_RANKING_MARKER}
1. Response a
2. Response B
3. Response C"""

        result = parse_ranking_from_text(ranking_text)

        # Should only match uppercase Response B and C
        assert f"{RESPONSE_LABEL_PREFIX}B" in result
        assert f"{RESPONSE_LABEL_PREFIX}C" in result
        # Lowercase 'a' should not match
        assert "Response a" not in result


class TestBuildLLMHistoryEdgeCases:
    """Additional edge case tests for build_llm_history."""

    def test_build_llm_history_part2_without_colon(self):
        """Test parsing PART 2: FINAL ANSWER without colon separator."""
        messages = [
            {"role": "user", "content": "Question"},
            {
                "role": "assistant",
                "stage3": {
                    "model": "model1",
                    "response": "PART 1: REPORT\n\nTable\n\nPART 2 FINAL ANSWER\n\nThis is the answer.",
                },
            },
        ]

        result = build_llm_history(messages)

        assert len(result) == 2
        assert result[1]["content"] == "PART 1: REPORT\n\nTable\n\nPART 2 FINAL ANSWER\n\nThis is the answer."

    def test_build_llm_history_part2_multiple_colons(self):
        """Test parsing PART 2: FINAL ANSWER with multiple colons."""
        messages = [
            {"role": "user", "content": "Question"},
            {
                "role": "assistant",
                "stage3": {
                    "model": "model1",
                    "response": "PART 1: REPORT\n\nPART 2: FINAL ANSWER:\n\nAnswer: This is it.",
                },
            },
        ]

        result = build_llm_history(messages)

        assert len(result) == 2
        # Should extract content after "PART 2: FINAL ANSWER:"
        assert "Answer: This is it." in result[1]["content"]

    def test_build_llm_history_part2_empty_after_split(self):
        """Test handling when PART 2: FINAL ANSWER splits but second part is empty."""
        messages = [
            {"role": "user", "content": "Question"},
            {
                "role": "assistant",
                "stage3": {
                    "model": "model1",
                    "response": "PART 1: REPORT\n\nPART 2: FINAL ANSWER:",
                },
            },
        ]

        result = build_llm_history(messages)

        assert len(result) == 2
        # Should handle gracefully
        assert isinstance(result[1]["content"], str)

    def test_build_llm_history_missing_stage3(self):
        """Test handling when stage3 key is missing."""
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "stage1": [{"model": "m1", "response": "r1"}]},
        ]

        result = build_llm_history(messages)

        assert len(result) == 2
        assert result[1]["content"] == ""  # Empty when stage3 missing

    def test_build_llm_history_stage3_empty_dict(self):
        """Test handling when stage3 is empty dict."""
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "stage3": {}},
        ]

        result = build_llm_history(messages)

        assert len(result) == 2
        assert result[1]["content"] == ""  # Empty when stage3 has no response

    def test_build_llm_history_stage3_missing_response_key(self):
        """Test handling when stage3 exists but response key is missing."""
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "stage3": {"model": "model1"}},
        ]

        result = build_llm_history(messages)

        assert len(result) == 2
        assert result[1]["content"] == ""  # Empty when response key missing

    def test_build_llm_history_max_turns_zero(self):
        """Test build_llm_history with max_turns=0."""
        messages = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "stage3": {"model": "m1", "response": "A1"}},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "stage3": {"model": "m1", "response": "A2"}},
        ]

        result = build_llm_history(messages, max_turns=0)

        # Should return empty list when max_turns is 0
        assert result == []

    def test_build_llm_history_max_turns_one(self):
        """Test build_llm_history with max_turns=1."""
        messages = []
        for i in range(5):
            messages.append({"role": "user", "content": f"Q{i}"})
            messages.append({"role": "assistant", "stage3": {"model": "m1", "response": f"A{i}"}})

        result = build_llm_history(messages, max_turns=1)

        # Should only keep last 1 turn (2 messages)
        assert len(result) == 2
        assert result[0]["content"] == "Q4"
        assert result[1]["content"] == "A4"

    def test_build_llm_history_mixed_roles(self):
        """Test build_llm_history filters out non-user/assistant roles."""
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User question"},
            {"role": "assistant", "stage3": {"model": "m1", "response": "Answer"}},
            {"role": "unknown", "content": "Unknown role"},
        ]

        result = build_llm_history(messages)

        # Should only include user and assistant
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"


class TestPrepareHistoryContextEdgeCases:
    """Additional edge case tests for prepare_history_context."""

    def test_prepare_history_context_single_user_message(self):
        """Test prepare_history_context with single user message."""
        history = [{"role": "user", "content": "Question"}]

        result = prepare_history_context(history)

        # Should exclude the last user message
        assert result == []

    def test_prepare_history_context_multiple_user_messages(self):
        """Test prepare_history_context with multiple consecutive user messages."""
        history = [
            {"role": "user", "content": "Q1"},
            {"role": "user", "content": "Q2"},
            {"role": "user", "content": "Q3"},
        ]

        result = prepare_history_context(history)

        # Should exclude only the last user message
        assert len(result) == 2
        assert result[0]["content"] == "Q1"
        assert result[1]["content"] == "Q2"

    def test_prepare_history_context_empty_list(self):
        """Test prepare_history_context with empty list."""
        result = prepare_history_context([])

        assert result == []

    def test_prepare_history_context_last_not_user(self):
        """Test prepare_history_context when last message is not user."""
        history = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
        ]

        result = prepare_history_context(history)

        # Should return unchanged
        assert result == history


class TestBuildMessageChainEdgeCases:
    """Additional edge case tests for build_message_chain."""

    def test_build_message_chain_empty_system_prompt(self):
        """Test build_message_chain with empty system prompt."""
        system_prompt = ""
        history = []
        user_query = "Question"

        result = build_message_chain(system_prompt, history, user_query)

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == ""
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "Question"

    def test_build_message_chain_empty_user_query(self):
        """Test build_message_chain with empty user query."""
        system_prompt = "System prompt"
        history = []
        user_query = ""

        result = build_message_chain(system_prompt, history, user_query)

        assert len(result) == 2
        assert result[1]["content"] == ""

    def test_build_message_chain_history_with_last_user(self):
        """Test build_message_chain excludes last user message from history."""
        system_prompt = "System"
        history = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},  # Should be excluded
        ]
        user_query = "Q3"

        result = build_message_chain(system_prompt, history, user_query)

        # Should have system + 2 history messages + user_query
        assert len(result) == 4
        assert result[1]["content"] == "Q1"
        assert result[2]["content"] == "A1"
        assert result[3]["content"] == "Q3"
        # Q2 should not be in result
        assert "Q2" not in [m["content"] for m in result]


class TestBuildRankingPromptEdgeCases:
    """Additional edge case tests for build_ranking_prompt."""

    def test_build_ranking_prompt_empty_user_query(self):
        """Test build_ranking_prompt with empty user query."""
        user_query = ""
        responses_text = "Response A: Answer"

        result = build_ranking_prompt(user_query, responses_text)

        assert "" in result  # Empty query should be in result
        assert responses_text in result

    def test_build_ranking_prompt_empty_responses_text(self):
        """Test build_ranking_prompt with empty responses text."""
        user_query = "Question"
        responses_text = ""

        result = build_ranking_prompt(user_query, responses_text)

        assert user_query in result
        assert "" in result  # Empty responses_text should be in result

    def test_build_ranking_prompt_custom_template_with_all_tags(self):
        """Test build_ranking_prompt with custom template containing all tags."""
        user_query = "Question"
        responses_text = "Response A: Answer"
        custom_template = "Rank {user_query} {responses_text} from {peer_text}"

        result = build_ranking_prompt(user_query, responses_text, prompt_template=custom_template, exclude_self=True)

        assert user_query in result
        assert responses_text in result
        assert "your peers" in result  # exclude_self=True

    def test_build_ranking_prompt_template_formatting(self):
        """Test build_ranking_prompt formats template correctly."""
        user_query = "Test"
        responses_text = "Response A: Test"
        custom_template = "Evaluate {user_query}:\n{responses_text}"

        result = build_ranking_prompt(user_query, responses_text, prompt_template=custom_template)

        # Should format template with values
        assert "Evaluate Test:" in result
        assert "Response A: Test" in result


class TestCalculateAggregateRankingsEdgeCases:
    """Additional edge case tests for calculate_aggregate_rankings."""

    def test_calculate_aggregate_rankings_empty_stage2_results(self):
        """Test calculate_aggregate_rankings with empty stage2_results."""
        result = calculate_aggregate_rankings([], {})

        assert result == []

    def test_calculate_aggregate_rankings_empty_label_to_model(self):
        """Test calculate_aggregate_rankings with empty label_to_model."""
        stage2_results = [
            {
                "model": "model1",
                "ranking": f"{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}A",
                "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A"],
            }
        ]

        result = calculate_aggregate_rankings(stage2_results, {})

        # Should return empty list when no labels match
        assert result == []

    def test_calculate_aggregate_rankings_missing_ranking_key(self):
        """Test calculate_aggregate_rankings handles missing ranking key."""
        stage2_results = [
            {
                "model": "model1",
                # Missing "ranking" key
            }
        ]
        label_to_model = {f"{RESPONSE_LABEL_PREFIX}A": "ModelA"}

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # Should handle gracefully
        assert isinstance(result, list)

    def test_calculate_aggregate_rankings_ranking_not_string(self):
        """Test calculate_aggregate_rankings handles non-string ranking value."""
        stage2_results = [
            {
                "model": "model1",
                "ranking": 123,  # Not a string
            }
        ]
        label_to_model = {f"{RESPONSE_LABEL_PREFIX}A": "ModelA"}

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # Should handle gracefully
        assert isinstance(result, list)

    def test_calculate_aggregate_rankings_single_model_multiple_votes(self):
        """Test calculate_aggregate_rankings with single model receiving multiple votes."""
        stage2_results = [
            {
                "model": "voter1",
                "ranking": f"{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}A",
                "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A"],
            },
            {
                "model": "voter2",
                "ranking": f"{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}A",
                "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A"],
            },
            {
                "model": "voter3",
                "ranking": f"{FINAL_RANKING_MARKER}\n2. {RESPONSE_LABEL_PREFIX}A",
                "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}B", f"{RESPONSE_LABEL_PREFIX}A"],
            },
        ]
        label_to_model = {
            f"{RESPONSE_LABEL_PREFIX}A": "ModelA",
            f"{RESPONSE_LABEL_PREFIX}B": "ModelB",
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # ModelA: positions 1, 1, 2 = avg (1+1+2)/3 = 1.33
        model_a = next(r for r in result if r["model"] == "ModelA")
        assert model_a["average_rank"] == 1.33
        assert model_a["rankings_count"] == 3

    def test_calculate_aggregate_rankings_no_matching_labels_in_parsed(self):
        """Test calculate_aggregate_rankings when parsed_ranking has no matching labels."""
        stage2_results = [
            {
                "model": "model1",
                "ranking": f"{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}X",
                "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}X"],  # Not in label_to_model
            }
        ]
        label_to_model = {
            f"{RESPONSE_LABEL_PREFIX}A": "ModelA",
            f"{RESPONSE_LABEL_PREFIX}B": "ModelB",
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # Should return empty list when no labels match
        assert result == []

    def test_calculate_aggregate_rankings_single_position(self):
        """Test calculate_aggregate_rankings with single position per model."""
        stage2_results = [
            {
                "model": "voter1",
                "ranking": f"{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}A",
                "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A"],
            }
        ]
        label_to_model = {f"{RESPONSE_LABEL_PREFIX}A": "ModelA"}

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # Single position should result in average_rank = 1.0
        assert len(result) == 1
        assert result[0]["average_rank"] == 1.0
        assert result[0]["rankings_count"] == 1
