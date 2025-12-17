"""
Service for handling Strategic Consensus Synthesis (Stage 3).
"""

import json
import logging
import re

from ..config.prompts import get_active_consensus_prompt
from .openrouter import query_model

logger = logging.getLogger(__name__)


class ConsensusService:
    @staticmethod
    async def synthesize_consensus(
        stage1_results: list[dict],
        stage2_results: list[dict],
        org_id: str,
        api_key: str,
        base_url: str,
        user_strategy_override: str = None,
    ) -> tuple[str, list[dict]]:
        """
        Synthesize the final answer using the active Consensus Strategy.

        Args:
            stage1_results: List of Stage 1 results (Proposals)
            stage2_results: List of Stage 2 results (Rankings/Critiques)
            org_id: Organization ID
            api_key: API Key
            base_url: Base URL
            user_strategy_override: Optional strategy name

        Returns:
            (final_answer_text, attribution_list)
        """

        # 1. Determine Strategy
        strategy_name = user_strategy_override
        prompt_template = ""

        if strategy_name:
            from ..config.prompts import load_consensus_prompt

            prompt_template = load_consensus_prompt(strategy_name)
        else:
            strategy_name, prompt_template = get_active_consensus_prompt(org_id)

        logger.info(f"Synthesizing consensus with strategy: {strategy_name}")

        # 2. Prepare Context (The "Evidence")
        # We need to link Stage 1 proposals with their identity so we can map critiques
        # But Stage 2 critiques usually refer to "Candidate A" or "Candidate B".
        # We assume the "Raw Text" of Stage 2 contains the reasoning.

        context_lines = []

        # Section A: The Proposals
        context_lines.append("### SECTION A: PROPOSALS (The Options) ###")
        for res in stage1_results:
            name = res.get("personality_name", res.get("model", "Unknown"))
            pid = res.get("personality_id", "Unknown")
            content = res.get("response", "")
            context_lines.append(f"\n--- PROPOSAL FROM {name} (ID: {pid}) ---")
            context_lines.append(content)

        # Section B: The Peer Reviews
        context_lines.append("\n### SECTION B: PEER REVIEWS (The Critique) ###")
        for res in stage2_results:
            reviewer = res.get("personality_name", "Unknown Reviewer")
            critique_text = res.get("ranking", "")  # The raw text output of Stage 2

            context_lines.append(f"\n--- REVIEW BY {reviewer} ---")
            context_lines.append(critique_text)

            # Simple heuristic for Veto flags in the raw text
            if "fatal flaw" in critique_text.lower() or "critical risk" in critique_text.lower():
                context_lines.append("    *** VETO FLAGS DETECTED IN THIS REVIEW ***")

        full_context = "\n".join(context_lines)

        # 3. Construct System Prompt
        # Replace {count}
        system_prompt = prompt_template.replace("{count}", str(len(stage1_results)))

        # 4. Call LLM (Async)
        from ..config.personalities import load_org_models_config

        models_config = load_org_models_config(org_id)
        model = models_config.get("chairman_model", "gemini/gemini-2.5-pro")

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_context},
        ]

        response = await query_model(model, messages, api_key=api_key, base_url=base_url)

        if not response:
            return "Error: Failed to generate consensus.", []

        response_text = response.get("content", "")

        # 5. Parse Attribution
        final_answer, attribution_list = ConsensusService.parse_attribution(response_text)

        # Add strategy key to attribution items for DB
        for item in attribution_list:
            item["strategy"] = strategy_name

        return final_answer, attribution_list

    @staticmethod
    def parse_attribution(response_text: str) -> tuple[str, list[dict]]:
        """
        Extract the JSON attribution block from the LLM response.
        Returns cleaned text (without JSON) and the list of contributors.
        """
        contributors = []
        cleaned_text = response_text

        # Regex to find JSON block at the end
        # Looking for ```json ... ``` or just { "contributors": ... }
        match = re.search(r"```json\s*({.*?})\s*```", response_text, re.DOTALL)
        if not match:
            # Try finding just brace-enclosed block if code block markers missing
            match = re.search(r"(\{\s*\"contributors\":\s*\[.*?\]\s*\})", response_text, re.DOTALL)

        if match:
            json_str = match.group(1)
            try:
                data = json.loads(json_str)
                contributors = data.get("contributors", [])

                # Remove the JSON from the text to show the user a clean answer
                # Only remove the match
                cleaned_text = response_text.replace(match.group(0), "").strip()
            except json.JSONDecodeError:
                logger.warning("Failed to decode attribution JSON.")

        return cleaned_text, contributors
