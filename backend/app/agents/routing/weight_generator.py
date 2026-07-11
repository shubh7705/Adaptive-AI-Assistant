"""
DynamicWeightGenerator — Change 10 (Phase 2)

Weights are loaded from config/routing_weights.yaml so they can be tuned
and hot-reloaded without a Docker rebuild. A short in-process TTL cache
prevents the file from being read on every routing request.

To change weights: edit routing_weights.yaml. The new values are picked up
after at most ROUTING_CACHE_TTL_SECONDS seconds (default 10).
"""

import os
import time
import yaml
import logging
from dataclasses import dataclass
from app.schemas.intent import IntentType
from app.config.settings import settings

logger = logging.getLogger(__name__)

WEIGHTS_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "routing_weights.yaml")


@dataclass
class RoutingWeights:
    coding: float = 0.1
    reasoning: float = 0.2
    math: float = 0.1
    vision: float = 0.1
    creative: float = 0.1
    latency: float = 0.2
    cost: float = 0.2


# Hardcoded fallback table (used only if routing_weights.yaml is missing/invalid)
_FALLBACK_TABLE: dict = {
    "coding":       RoutingWeights(coding=0.45, reasoning=0.25, latency=0.15, cost=0.15),
    "programming":  RoutingWeights(coding=0.45, reasoning=0.25, latency=0.15, cost=0.15),
    "sql":          RoutingWeights(coding=0.45, reasoning=0.25, latency=0.15, cost=0.15),
    "vision":       RoutingWeights(vision=0.50, reasoning=0.20, latency=0.15, cost=0.15),
    "math":         RoutingWeights(math=0.50, reasoning=0.30, latency=0.10, cost=0.10),
    "data_analysis":RoutingWeights(math=0.50, reasoning=0.30, latency=0.10, cost=0.10),
    "summarization":RoutingWeights(reasoning=0.30, creative=0.30, latency=0.20, cost=0.20),
    "extraction":   RoutingWeights(reasoning=0.30, creative=0.30, latency=0.20, cost=0.20),
    "creative":     RoutingWeights(creative=0.60, reasoning=0.10, latency=0.10, cost=0.20),
    "chat":         RoutingWeights(creative=0.20, reasoning=0.20, latency=0.40, cost=0.20),
    "reasoning":    RoutingWeights(reasoning=0.60, coding=0.10, latency=0.15, cost=0.15),
}
_FALLBACK_DEFAULT = RoutingWeights(reasoning=0.30, creative=0.10, coding=0.10, latency=0.25, cost=0.25)


class DynamicWeightGenerator:
    """
    Stage 3: Generates scoring weights dynamically based on the detected intent.
    Reads from routing_weights.yaml with a TTL cache; falls back to hardcoded table.
    """
    _yaml_cache: dict = {}
    _yaml_loaded_at: float = 0.0

    @classmethod
    def _load_yaml(cls) -> dict:
        now = time.monotonic()
        if now - cls._yaml_loaded_at < settings.ROUTING_CACHE_TTL_SECONDS and cls._yaml_cache:
            return cls._yaml_cache

        try:
            with open(WEIGHTS_FILE, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            cls._yaml_cache = data
            cls._yaml_loaded_at = now
        except Exception as e:
            logger.warning(f"Could not load routing_weights.yaml: {e}. Using hardcoded fallback.")

        return cls._yaml_cache

    @staticmethod
    def get_weights(intent_task: IntentType) -> RoutingWeights:
        table = DynamicWeightGenerator._load_yaml()

        raw = table.get(str(intent_task)) or table.get("default")
        if not raw:
            return _FALLBACK_TABLE.get(str(intent_task), _FALLBACK_DEFAULT)

        try:
            return RoutingWeights(**{k: float(v) for k, v in raw.items()})
        except Exception as e:
            logger.warning(f"Invalid weight config for '{intent_task}': {e}. Using fallback.")
            return _FALLBACK_TABLE.get(str(intent_task), _FALLBACK_DEFAULT)
