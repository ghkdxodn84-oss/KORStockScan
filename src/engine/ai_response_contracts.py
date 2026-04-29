"""Shared AI response schema contracts for Gemini/OpenAI engines."""

from __future__ import annotations


AI_RESPONSE_SCHEMA_REGISTRY = {
    "entry_v1": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["BUY", "WAIT", "DROP"]},
            "score": {"type": "integer"},
            "reason": {"type": "string"},
        },
        "required": ["action", "score", "reason"],
    },
    "holding_exit_v1": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["HOLD", "TRIM", "EXIT"]},
            "score": {"type": "integer"},
            "reason": {"type": "string"},
        },
        "required": ["action", "score", "reason"],
    },
    "overnight_v1": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["SELL_TODAY", "HOLD_OVERNIGHT"]},
            "confidence": {"type": "integer"},
            "reason": {"type": "string"},
            "risk_note": {"type": "string"},
        },
        "required": ["action", "confidence", "reason", "risk_note"],
    },
    "condition_entry_v1": {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["BUY", "WAIT", "SKIP"]},
            "confidence": {"type": "integer"},
            "order_type": {"type": "string", "enum": ["MARKET", "LIMIT_TOP", "NONE"]},
            "position_size_ratio": {"type": "number"},
            "invalidation_price": {"type": "integer"},
            "reasons": {"type": "array", "items": {"type": "string"}},
            "risks": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "decision",
            "confidence",
            "order_type",
            "position_size_ratio",
            "invalidation_price",
            "reasons",
            "risks",
        ],
    },
    "condition_exit_v1": {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["HOLD", "TRIM", "EXIT"]},
            "confidence": {"type": "integer"},
            "trim_ratio": {"type": "number"},
            "new_stop_price": {"type": "integer"},
            "reason_primary": {"type": "string"},
            "warning": {"type": "string"},
        },
        "required": [
            "decision",
            "confidence",
            "trim_ratio",
            "new_stop_price",
            "reason_primary",
            "warning",
        ],
    },
    "eod_top5_v1": {
        "type": "object",
        "properties": {
            "market_summary": {"type": "string"},
            "one_point_lesson": {"type": "string"},
            "top5": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "rank": {"type": "integer"},
                        "stock_name": {"type": "string"},
                        "stock_code": {"type": "string"},
                        "close_price": {"type": "integer"},
                        "reason": {"type": "string"},
                        "entry_plan": {"type": "string"},
                        "target_price_guide": {"type": "string"},
                        "stop_price_guide": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                    "required": ["rank", "stock_name", "stock_code", "close_price", "reason"],
                },
            },
        },
        "required": ["market_summary", "one_point_lesson", "top5"],
    },
}


def resolve_ai_response_schema(schema_name):
    normalized = str(schema_name or "").strip()
    if not normalized:
        return None
    schema = AI_RESPONSE_SCHEMA_REGISTRY.get(normalized)
    if schema is None:
        raise ValueError(f"Unknown AI response schema: {normalized}")
    return schema


def build_openai_response_text_format(schema_name, *, strict=True):
    schema = resolve_ai_response_schema(schema_name)
    if schema is None:
        return {"type": "json_object"}
    return {
        "type": "json_schema",
        "name": str(schema_name),
        "schema": schema,
        "strict": bool(strict),
    }
