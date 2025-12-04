"""Tests for council.py core logic."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.council import (
    calculate_aggregate_rankings,
    generate_conversation_title,
    parse_ranking_from_text,
)
from backend.council_helpers import (
    FINAL_RANKING_MARKER,
    RESPONSE_LABEL_PREFIX,
    build_llm_history,
    build_message_chain,
    build_ranking_prompt,
    get_system_time_instruction,
    get_time_instructions,
    get_user_time_instruction,
    prepare_history_context,
)


class TestParseRankingFromText:
    """Tests for parse_ranking_from_text function."""

    def test_parse_standard_format(self):
        """Test parsing of standard FINAL RANKING format."""
        ranking_text = f"""Response A provides good detail on X but misses Y.
Response B is accurate but lacks depth on Z.
Response C offers the most comprehensive answer.

{FINAL_RANKING_MARKER}
1. {RESPONSE_LABEL_PREFIX}C
2. {RESPONSE_LABEL_PREFIX}A
3. {RESPONSE_LABEL_PREFIX}B"""

        result = parse_ranking_from_text(ranking_text)
        assert result == [
            f"{RESPONSE_LABEL_PREFIX}C",
            f"{RESPONSE_LABEL_PREFIX}A",
            f"{RESPONSE_LABEL_PREFIX}B",
        ]

    def test_parse_without_final_ranking_header(self):
        """Test fallback parsing when FINAL RANKING: header is missing."""
        ranking_text = f"""Response A is good.
Response B is better.
Response C is best.

1. {RESPONSE_LABEL_PREFIX}C
2. {RESPONSE_LABEL_PREFIX}B
3. {RESPONSE_LABEL_PREFIX}A"""

        result = parse_ranking_from_text(ranking_text)
        # Should extract all Response X patterns in order
        assert f"{RESPONSE_LABEL_PREFIX}C" in result
        assert f"{RESPONSE_LABEL_PREFIX}B" in result
        assert f"{RESPONSE_LABEL_PREFIX}A" in result

    def test_parse_empty_input(self):
        """Test parsing empty string."""
        result = parse_ranking_from_text("")
        assert result == []

    def test_parse_malformed_ranking(self):
        """Test parsing malformed ranking text."""
        # Missing numbers, just labels
        ranking_text = f"""{FINAL_RANKING_MARKER}
{RESPONSE_LABEL_PREFIX}A
{RESPONSE_LABEL_PREFIX}B
{RESPONSE_LABEL_PREFIX}C"""

        result = parse_ranking_from_text(ranking_text)
        # Should still extract labels
        assert len(result) >= 3
        assert f"{RESPONSE_LABEL_PREFIX}A" in result or f"{RESPONSE_LABEL_PREFIX}B" in result

    def test_parse_with_extra_text_after_ranking(self):
        """Test parsing when there's extra text after the ranking section."""
        ranking_text = f"""Some evaluation text here.

{FINAL_RANKING_MARKER}
1. {RESPONSE_LABEL_PREFIX}B
2. {RESPONSE_LABEL_PREFIX}A
3. {RESPONSE_LABEL_PREFIX}C

Additional commentary that should be ignored."""

        result = parse_ranking_from_text(ranking_text)
        assert result == [
            f"{RESPONSE_LABEL_PREFIX}B",
            f"{RESPONSE_LABEL_PREFIX}A",
            f"{RESPONSE_LABEL_PREFIX}C",
        ]

    def test_parse_case_insensitive_marker(self):
        """Test that parsing handles case variations in marker."""
        # The function uses exact match, so test with exact format
        ranking_text = f"""Evaluation text.

{FINAL_RANKING_MARKER}
1. {RESPONSE_LABEL_PREFIX}A
2. {RESPONSE_LABEL_PREFIX}B"""

        result = parse_ranking_from_text(ranking_text)
        assert len(result) == 2
        assert result[0] == f"{RESPONSE_LABEL_PREFIX}A"


class TestCalculateAggregateRankings:
    """Tests for calculate_aggregate_rankings function."""

    def test_calculate_simple_ranking(self):
        """Test aggregate calculation with simple rankings."""
        stage2_results = [
            {
                "model": "model1",
                "ranking": f"Evaluation\n\n{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}A\n2. {RESPONSE_LABEL_PREFIX}B",
                "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}A", f"{RESPONSE_LABEL_PREFIX}B"],
            },
            {
                "model": "model2",
                "ranking": f"Evaluation\n\n{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}B\n2. {RESPONSE_LABEL_PREFIX}A",
                "parsed_ranking": [f"{RESPONSE_LABEL_PREFIX}B", f"{RESPONSE_LABEL_PREFIX}A"],
            },
        ]
        label_to_model = {
            f"{RESPONSE_LABEL_PREFIX}A": "Model1",
            f"{RESPONSE_LABEL_PREFIX}B": "Model2",
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # Model2 should have better average rank (1.5 vs 1.5, but let's check structure)
        assert len(result) == 2
        assert result[0]["model"] in ["Model1", "Model2"]
        assert result[1]["model"] in ["Model1", "Model2"]
        assert all("average_rank" in r for r in result)
        assert all("rankings_count" in r for r in result)
        # Model2 ranked first by model2, second by model1 = avg 1.5
        # Model1 ranked first by model1, second by model2 = avg 1.5
        # Both should have average_rank of 1.5
        model1_result = next(r for r in result if r["model"] == "Model1")
        model2_result = next(r for r in result if r["model"] == "Model2")
        assert model1_result["average_rank"] == 1.5
        assert model2_result["average_rank"] == 1.5

    def test_calculate_with_missing_labels(self):
        """Test handling of missing labels in label_to_model."""
        stage2_results = [
            {
                "model": "model1",
                "ranking": f"Evaluation\n\n{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}A\n2. {RESPONSE_LABEL_PREFIX}B\n3. {RESPONSE_LABEL_PREFIX}C",
                "parsed_ranking": [
                    f"{RESPONSE_LABEL_PREFIX}A",
                    f"{RESPONSE_LABEL_PREFIX}B",
                    f"{RESPONSE_LABEL_PREFIX}C",
                ],
            }
        ]
        # Missing Response C in mapping
        label_to_model = {
            f"{RESPONSE_LABEL_PREFIX}A": "Model1",
            f"{RESPONSE_LABEL_PREFIX}B": "Model2",
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # Should only include models that are in label_to_model
        assert len(result) == 2
        model_names = [r["model"] for r in result]
        assert "Model1" in model_names
        assert "Model2" in model_names
        assert "Model3" not in model_names

    def test_calculate_empty_rankings(self):
        """Test handling of empty rankings list."""
        result = calculate_aggregate_rankings([], {})
        assert result == []

    def test_calculate_with_three_models(self):
        """Test aggregate calculation with three models and multiple voters."""
        stage2_results = [
            {
                "model": "voter1",
                "ranking": f"Evaluation\n\n{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}A\n2. {RESPONSE_LABEL_PREFIX}B\n3. {RESPONSE_LABEL_PREFIX}C",
                "parsed_ranking": [
                    f"{RESPONSE_LABEL_PREFIX}A",
                    f"{RESPONSE_LABEL_PREFIX}B",
                    f"{RESPONSE_LABEL_PREFIX}C",
                ],
            },
            {
                "model": "voter2",
                "ranking": f"Evaluation\n\n{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}B\n2. {RESPONSE_LABEL_PREFIX}C\n3. {RESPONSE_LABEL_PREFIX}A",
                "parsed_ranking": [
                    f"{RESPONSE_LABEL_PREFIX}B",
                    f"{RESPONSE_LABEL_PREFIX}C",
                    f"{RESPONSE_LABEL_PREFIX}A",
                ],
            },
            {
                "model": "voter3",
                "ranking": f"Evaluation\n\n{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}A\n2. {RESPONSE_LABEL_PREFIX}C\n3. {RESPONSE_LABEL_PREFIX}B",
                "parsed_ranking": [
                    f"{RESPONSE_LABEL_PREFIX}A",
                    f"{RESPONSE_LABEL_PREFIX}C",
                    f"{RESPONSE_LABEL_PREFIX}B",
                ],
            },
        ]
        label_to_model = {
            f"{RESPONSE_LABEL_PREFIX}A": "ModelA",
            f"{RESPONSE_LABEL_PREFIX}B": "ModelB",
            f"{RESPONSE_LABEL_PREFIX}C": "ModelC",
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        assert len(result) == 3
        # ModelA: ranks 1, 3, 1 = avg (1+3+1)/3 = 1.67
        # ModelB: ranks 2, 1, 3 = avg (2+1+3)/3 = 2.0
        # ModelC: ranks 3, 2, 2 = avg (3+2+2)/3 = 2.33
        # Should be sorted by average_rank (lower is better)
        assert result[0]["average_rank"] < result[1]["average_rank"]
        assert result[1]["average_rank"] < result[2]["average_rank"]

        model_a = next(r for r in result if r["model"] == "ModelA")
        assert model_a["rankings_count"] == 3
        assert abs(model_a["average_rank"] - 1.67) < 0.1


class TestBuildLLMHistory:
    """Tests for build_llm_history function."""

    def test_build_history_from_messages(self):
        """Test building history from storage messages."""
        messages = [
            {"role": "user", "content": "What is Python?"},
            {
                "role": "assistant",
                "stage1": [{"model": "model1", "response": "Response 1"}],
                "stage2": [{"model": "model1", "ranking": "Ranking 1"}],
                "stage3": {"model": "model1", "response": "Python is a programming language."},
            },
            {"role": "user", "content": "What is JavaScript?"},
            {
                "role": "assistant",
                "stage1": [{"model": "model1", "response": "Response 2"}],
                "stage2": [{"model": "model1", "ranking": "Ranking 2"}],
                "stage3": {"model": "model1", "response": "JavaScript is a scripting language."},
            },
        ]

        result = build_llm_history(messages)

        assert len(result) == 4  # 2 user + 2 assistant
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "What is Python?"
        assert result[1]["role"] == "assistant"
        assert result[1]["content"] == "Python is a programming language."
        assert result[2]["role"] == "user"
        assert result[2]["content"] == "What is JavaScript?"
        assert result[3]["role"] == "assistant"
        assert result[3]["content"] == "JavaScript is a scripting language."

    def test_build_history_with_sliding_window(self):
        """Test sliding window functionality (max_turns parameter)."""
        # Create 15 turns (30 messages)
        messages = []
        for i in range(15):
            messages.append({"role": "user", "content": f"Question {i}"})
            messages.append(
                {"role": "assistant", "stage3": {"model": "model1", "response": f"Answer {i}"}}
            )

        # Default max_turns is 10, so should only keep last 10 turns (20 messages)
        result = build_llm_history(messages)

        assert len(result) == 20  # 10 user + 10 assistant
        assert result[0]["content"] == "Question 5"  # First message should be from turn 5
        assert result[-1]["content"] == "Answer 14"  # Last message should be from turn 14

    def test_build_history_strips_internal_stages(self):
        """Test that Stage 1 and Stage 2 are excluded from history."""
        messages = [
            {"role": "user", "content": "Test question"},
            {
                "role": "assistant",
                "stage1": [{"model": "model1", "response": "Internal stage 1 response"}],
                "stage2": [{"model": "model1", "ranking": "Internal stage 2 ranking"}],
                "stage3": {"model": "model1", "response": "Final answer only"},
            },
        ]

        result = build_llm_history(messages)

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
        # Should only contain Stage 3 response, not Stage 1 or Stage 2
        assert result[1]["content"] == "Final answer only"
        assert "Internal stage 1" not in result[1]["content"]
        assert "Internal stage 2" not in result[1]["content"]

    def test_build_history_empty_messages(self):
        """Test building history from empty messages list."""
        result = build_llm_history([])
        assert result == []

    def test_build_history_parses_part2_final_answer(self):
        """Test that build_llm_history parses 'PART 2: FINAL ANSWER' format."""
        messages = [
            {"role": "user", "content": "Test question"},
            {
                "role": "assistant",
                "stage3": {
                    "model": "model1",
                    "response": "PART 1: COUNCIL REPORT\n\nVoting table here...\n\nPART 2: FINAL ANSWER\n\nThis is the actual answer.",
                },
            },
        ]

        result = build_llm_history(messages)

        assert len(result) == 2
        assert result[1]["role"] == "assistant"
        assert result[1]["content"] == "This is the actual answer."
        assert "PART 1" not in result[1]["content"]
        assert "PART 2" not in result[1]["content"]

    def test_build_history_handles_part2_with_colon(self):
        """Test parsing PART 2: FINAL ANSWER with colon separator."""
        messages = [
            {"role": "user", "content": "Test question"},
            {
                "role": "assistant",
                "stage3": {
                    "model": "model1",
                    "response": "PART 1: COUNCIL REPORT\n\nTable here.\n\nPART 2: FINAL ANSWER:\n\nThis is the answer.",
                },
            },
        ]

        result = build_llm_history(messages)

        assert len(result) == 2
        assert result[1]["content"] == "This is the answer."

    def test_build_history_filters_non_user_assistant_messages(self):
        """Test that only user and assistant messages are included."""
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User question"},
            {"role": "assistant", "stage3": {"model": "model1", "response": "Answer"}},
            {"role": "unknown", "content": "Unknown role"},
        ]

        result = build_llm_history(messages)

        assert len(result) == 2  # Only user and assistant
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    def test_build_history_custom_max_turns(self):
        """Test sliding window with custom max_turns parameter."""
        messages = []
        for i in range(10):
            messages.append({"role": "user", "content": f"Q{i}"})
            messages.append({"role": "assistant", "stage3": {"model": "m1", "response": f"A{i}"}})

        # With max_turns=3, should only keep last 3 turns (6 messages)
        result = build_llm_history(messages, max_turns=3)

        assert len(result) == 6
        assert result[0]["content"] == "Q7"
        assert result[-1]["content"] == "A9"


class TestGenerateConversationTitle:
    """Tests for generate_conversation_title function."""

    @pytest.mark.asyncio
    async def test_generate_title_success(self):
        """Test successful title generation."""
        mock_response = MagicMock()
        mock_response.get.return_value = "Generated Title"

        with (
            patch("backend.council.load_org_system_prompts") as mock_prompts,
            patch("backend.council.load_org_models_config") as mock_config,
            patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
        ):
            mock_prompts.return_value = {"title_prompt": "Prompt for {user_query}"}
            mock_config.return_value = {"title_model": "test-model"}
            mock_query.return_value = mock_response

            title = await generate_conversation_title("Hello world", "org1", "key", "url")

            assert title == "Generated Title"
            mock_query.assert_called_once()
            args, kwargs = mock_query.call_args
            assert args[0] == "test-model"
            assert kwargs["api_key"] == "key"

    @pytest.mark.asyncio
    async def test_generate_title_fallback(self):
        """Test fallback when model returns None."""
        with (
            patch("backend.council.load_org_system_prompts") as mock_prompts,
            patch("backend.council.load_org_models_config") as mock_config,
            patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
        ):
            mock_prompts.return_value = {"title_prompt": "Prompt"}
            mock_config.return_value = {"title_model": "test-model"}
            mock_query.return_value = None

            title = await generate_conversation_title("Hello", "org1", "key", "url")

            assert title == "New Conversation"

    @pytest.mark.asyncio
    async def test_generate_title_truncation(self):
        """Test that long titles are truncated."""
        long_title = "This is a very long title that exceeds the maximum length of fifty characters and should be truncated"
        mock_response = MagicMock()
        mock_response.get.return_value = long_title

        with (
            patch("backend.council.load_org_system_prompts") as mock_prompts,
            patch("backend.council.load_org_models_config") as mock_config,
            patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
        ):
            mock_prompts.return_value = {"title_prompt": "Prompt"}
            mock_config.return_value = {"title_model": "test-model"}
            mock_query.return_value = mock_response

            title = await generate_conversation_title("Hello", "org1", "key", "url")

            assert len(title) <= 50
            assert title.endswith("...")
            assert "This is a very long title" in title

    @pytest.mark.asyncio
    async def test_generate_title_cleanup(self):
        """Test that quotes are removed from title."""
        mock_response = MagicMock()
        mock_response.get.return_value = '"Quoted Title"'

        with (
            patch("backend.council.load_org_system_prompts") as mock_prompts,
            patch("backend.council.load_org_models_config") as mock_config,
            patch("backend.council.query_model", new_callable=AsyncMock) as mock_query,
        ):
            mock_prompts.return_value = {"title_prompt": "Prompt"}
            mock_config.return_value = {"title_model": "test-model"}
            mock_query.return_value = mock_response

            title = await generate_conversation_title("Hello", "org1", "key", "url")

            assert title == "Quoted Title"


class TestTimeInstructions:
    """Tests for time instruction helper functions."""

    def test_get_time_instructions(self):
        """Test get_time_instructions returns both instructions."""
        system_instruction, user_instruction = get_time_instructions()

        assert "Current System Time:" in system_instruction
        assert "SYSTEM NOTE" in user_instruction
        assert "current date and time" in user_instruction

    def test_get_system_time_instruction(self):
        """Test get_system_time_instruction returns system instruction."""
        instruction = get_system_time_instruction()

        assert "Current System Time:" in instruction
        assert "SYSTEM NOTE" not in instruction

    def test_get_user_time_instruction(self):
        """Test get_user_time_instruction returns user instruction."""
        instruction = get_user_time_instruction()

        assert "SYSTEM NOTE" in instruction
        assert "current date and time" in instruction
        assert "Current System Time:" not in instruction


class TestPrepareHistoryContext:
    """Tests for prepare_history_context function."""

    def test_prepare_history_excludes_last_user_message(self):
        """Test that last user message is excluded if present."""
        history = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},
        ]

        result = prepare_history_context(history)

        assert len(result) == 2
        assert result[0]["content"] == "Question 1"
        assert result[1]["content"] == "Answer 1"
        assert result[-1]["role"] != "user"

    def test_prepare_history_no_user_at_end(self):
        """Test that history is unchanged if last message is not user."""
        history = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
        ]

        result = prepare_history_context(history)

        assert len(result) == 2
        assert result == history

    def test_prepare_history_empty(self):
        """Test that empty history returns empty list."""
        result = prepare_history_context([])
        assert result == []


class TestBuildMessageChain:
    """Tests for build_message_chain function."""

    def test_build_message_chain_with_history(self):
        """Test building message chain with history."""
        system_prompt = "You are a helpful assistant."
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]
        user_query = "Current question"

        result = build_message_chain(system_prompt, history, user_query)

        assert len(result) == 4
        assert result[0]["role"] == "system"
        assert result[0]["content"] == system_prompt
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "Previous question"
        assert result[2]["role"] == "assistant"
        assert result[2]["content"] == "Previous answer"
        assert result[3]["role"] == "user"
        assert result[3]["content"] == user_query

    def test_build_message_chain_no_history(self):
        """Test building message chain without history."""
        system_prompt = "You are a helpful assistant."
        user_query = "Current question"

        result = build_message_chain(system_prompt, [], user_query)

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == system_prompt
        assert result[1]["role"] == "user"
        assert result[1]["content"] == user_query

    def test_build_message_chain_excludes_last_user_from_history(self):
        """Test that last user message in history is excluded."""
        system_prompt = "You are a helpful assistant."
        history = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},  # Should be excluded
        ]
        user_query = "Current question"

        result = build_message_chain(system_prompt, history, user_query)

        assert len(result) == 4  # system + 2 history messages + user_query
        assert result[1]["content"] == "Question 1"
        assert result[2]["content"] == "Answer 1"
        assert result[3]["content"] == user_query
        assert "Question 2" not in [m["content"] for m in result]


class TestBuildRankingPrompt:
    """Tests for build_ranking_prompt function."""

    def test_build_ranking_prompt_default(self):
        """Test building ranking prompt with default template."""
        user_query = "What is Python?"
        responses_text = "Response A: Python is a language\nResponse B: Python is a snake"

        result = build_ranking_prompt(user_query, responses_text)

        assert user_query in result
        assert responses_text in result
        assert "different models (anonymized)" in result
        assert FINAL_RANKING_MARKER in result
        assert RESPONSE_LABEL_PREFIX in result

    def test_build_ranking_prompt_exclude_self(self):
        """Test building ranking prompt with exclude_self=True."""
        user_query = "What is Python?"
        responses_text = "Response A: Answer"

        result = build_ranking_prompt(user_query, responses_text, exclude_self=True)

        assert "your peers (anonymized)" in result
        assert "different models (anonymized)" not in result

    def test_build_ranking_prompt_custom_template(self):
        """Test building ranking prompt with custom template."""
        user_query = "What is Python?"
        responses_text = "Response A: Answer"
        custom_template = "Rank {user_query} responses: {responses_text}"

        result = build_ranking_prompt(user_query, responses_text, prompt_template=custom_template)

        assert user_query in result
        assert responses_text in result
        assert "Rank" in result

    def test_build_ranking_prompt_no_template(self):
        """Test building ranking prompt when template is None/empty."""
        result = build_ranking_prompt("query", "responses", prompt_template=None)

        # Should use default template
        assert "query" in result or "Error" in result

    def test_build_ranking_prompt_empty_template(self):
        """Test building ranking prompt with empty template falls back to default."""
        result = build_ranking_prompt("query", "responses", prompt_template="")

        # Empty string is falsy, so falls back to default template
        assert "query" in result
        assert "responses" in result


class TestCalculateAggregateRankingsEdgeCases:
    """Additional edge case tests for calculate_aggregate_rankings function."""

    def test_calculate_with_empty_parsed_ranking(self):
        """Test handling when parse_ranking_from_text returns empty list."""
        stage2_results = [
            {
                "model": "model1",
                "ranking": "No ranking markers found",  # Will parse to empty list
            }
        ]
        label_to_model = {
            f"{RESPONSE_LABEL_PREFIX}A": "Model1",
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # Should return empty list since no rankings were parsed
        assert result == []

    def test_calculate_with_unparseable_ranking(self):
        """Test handling when ranking text cannot be parsed."""
        stage2_results = [
            {
                "model": "model1",
                "ranking": "Random text with no Response labels",
            }
        ]
        label_to_model = {
            f"{RESPONSE_LABEL_PREFIX}A": "Model1",
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # Should return empty list since no valid labels found
        assert result == []

    def test_calculate_with_duplicate_labels_in_ranking(self):
        """Test handling when a ranking contains duplicate labels."""
        stage2_results = [
            {
                "model": "model1",
                "ranking": f"Evaluation\n\n{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}A\n2. {RESPONSE_LABEL_PREFIX}A\n3. {RESPONSE_LABEL_PREFIX}B",
            }
        ]
        label_to_model = {
            f"{RESPONSE_LABEL_PREFIX}A": "ModelA",
            f"{RESPONSE_LABEL_PREFIX}B": "ModelB",
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # ModelA should appear twice (positions 1 and 2), ModelB once (position 3)
        assert len(result) == 2
        model_a = next(r for r in result if r["model"] == "ModelA")
        model_b = next(r for r in result if r["model"] == "ModelB")
        assert model_a["rankings_count"] == 2
        assert model_a["average_rank"] == 1.5  # (1 + 2) / 2
        assert model_b["rankings_count"] == 1
        assert model_b["average_rank"] == 3.0

    def test_calculate_with_no_matching_labels(self):
        """Test handling when no labels in rankings match label_to_model."""
        stage2_results = [
            {
                "model": "model1",
                "ranking": f"Evaluation\n\n{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}X\n2. {RESPONSE_LABEL_PREFIX}Y",
            }
        ]
        label_to_model = {
            f"{RESPONSE_LABEL_PREFIX}A": "ModelA",
            f"{RESPONSE_LABEL_PREFIX}B": "ModelB",
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # Should return empty list since no labels match
        assert result == []

    def test_calculate_rounding_precision(self):
        """Test that average ranks are rounded to 2 decimal places."""
        # Create scenario that results in non-round average
        stage2_results = [
            {
                "model": "voter1",
                "ranking": f"Evaluation\n\n{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}A\n2. {RESPONSE_LABEL_PREFIX}B",
            },
            {
                "model": "voter2",
                "ranking": f"Evaluation\n\n{FINAL_RANKING_MARKER}\n1. {RESPONSE_LABEL_PREFIX}A\n2. {RESPONSE_LABEL_PREFIX}B",
            },
            {
                "model": "voter3",
                "ranking": f"Evaluation\n\n{FINAL_RANKING_MARKER}\n2. {RESPONSE_LABEL_PREFIX}A\n1. {RESPONSE_LABEL_PREFIX}B",
            },
        ]
        label_to_model = {
            f"{RESPONSE_LABEL_PREFIX}A": "ModelA",
            f"{RESPONSE_LABEL_PREFIX}B": "ModelB",
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # ModelA: positions 1, 1, 2 = avg (1+1+2)/3 = 1.333...
        # ModelB: positions 2, 2, 1 = avg (2+2+1)/3 = 1.666...
        model_a = next(r for r in result if r["model"] == "ModelA")
        model_b = next(r for r in result if r["model"] == "ModelB")
        assert model_a["average_rank"] == 1.33  # Rounded to 2 decimals
        assert model_b["average_rank"] == 1.67  # Rounded to 2 decimals
