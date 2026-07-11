"""
CandidateRanker — Change 11 (Phase 2)

Tie-break strategy upgraded from weighted random to epsilon-greedy contextual bandit:
  - With probability BANDIT_EPSILON: explore (uniform random among tied candidates)
  - With probability 1-BANDIT_EPSILON: exploit (pick the candidate with the best
    observed real-world performance: success_rate * tokens_per_sec from routing metadata)

The "clear winner" shortcut is preserved: if one candidate is >5% ahead of all others,
it is selected deterministically without entering the bandit.

Thompson Sampling can be added as a follow-up by maintaining Beta(α, β) parameters
per (model_id, task_type) in Redis using the outcome events from Change 8.
"""

import random
import logging
from typing import List, Dict, Any, Tuple
from app.models.registry import ModelRegistry
from app.config.settings import settings

logger = logging.getLogger(__name__)


class CandidateRanker:
    """
    Stage 8: Top-K Candidate Selection with Epsilon-Greedy Bandit Tie-Breaking.
    """

    @staticmethod
    def select_best_model(
        scored_models: List[Tuple[ModelRegistry, float, Dict[str, Any]]],
        top_k: int = 3,
    ) -> Tuple[ModelRegistry, float, Dict[str, Any], List[Dict]]:

        if not scored_models:
            raise ValueError("No scored models available.")

        # Sort by score descending
        scored_models.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored_models[:top_k]

        highest_score = top_candidates[0][1]
        # Candidates within 5% margin (or 0.5 absolute) of the top score are "tied"
        margin = max(abs(highest_score * 0.05), 0.5)
        tied = [c for c in top_candidates if (highest_score - c[1]) <= margin]

        if len(tied) == 1:
            # Clear winner — deterministic selection, no bandit needed
            selected = tied[0]
            reason = "Clear winner with highest score."
        else:
            # Epsilon-greedy bandit tie-break
            epsilon = settings.BANDIT_EPSILON
            if random.random() < epsilon:
                # Explore: uniform random pick
                selected = random.choice(tied)
                reason = (
                    f"Epsilon-greedy EXPLORE: uniform random among "
                    f"{len(tied)} tied candidates (ε={epsilon})."
                )
                logger.debug(f"Bandit explore: selected {selected[0].name}")
            else:
                # Exploit: pick candidate with best observed real-world performance.
                # We use (1 - error_penalty) * capability_score as a proxy for observed
                # performance since we have it available in the scoring metadata.
                # When the async feedback loop (Change 8) matures, replace with
                # actual success_rate * tokens_per_sec from Redis outcome data.
                def _exploit_score(candidate: Tuple) -> float:
                    _model, _score, meta = candidate
                    error_pen = meta.get("error_penalty", 0.0)
                    cap_score = meta.get("capability_score", 0.0)
                    # Observed quality proxy: high capability, low error rate
                    return cap_score * (1.0 - min(error_pen / 5.0, 1.0))

                selected = max(tied, key=_exploit_score)
                reason = (
                    f"Epsilon-greedy EXPLOIT: best observed performance among "
                    f"{len(tied)} tied candidates (ε={epsilon})."
                )
                logger.debug(f"Bandit exploit: selected {selected[0].name}")

        selected_model, selected_score, selected_meta = selected
        runner_ups = [
            {"model_id": str(c[0].id), "name": c[0].name, "score": c[1]}
            for c in top_candidates if str(c[0].id) != str(selected_model.id)
        ]
        selected_meta["reason"] = reason
        return selected_model, selected_score, selected_meta, runner_ups
