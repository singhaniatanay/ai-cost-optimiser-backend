import logging
from app.agents.base import InvalidInputError

logger = logging.getLogger(__name__)

async def run(payload: dict) -> dict:
    logger.info(f"ROI Calculator started with payload keys: {list(payload.keys())}")
    
    # Validate input
    if not isinstance(payload, dict):
        raise InvalidInputError("INVALID INPUT – payload must be a dict")
    for key in ("workload", "ranked_models", "current_model"):
        if key not in payload:
            raise InvalidInputError(f"INVALID INPUT – missing {key}")
    ranked_models = payload["ranked_models"]
    current_model = payload["current_model"]
    
    logger.info(f"Input current_model: '{current_model}' (empty: {not current_model})")
    logger.info(f"Ranked models count: {len(ranked_models)}")
    
    if not isinstance(ranked_models, list) or not ranked_models:
        raise InvalidInputError("INVALID INPUT – ranked_models must be a non-empty list")
    if not isinstance(current_model, str):
        raise InvalidInputError("INVALID INPUT – current_model must be a string")

    # Handle empty current_model by using the most expensive model as baseline
    if not current_model:
        # Find the most expensive model to use as baseline
        most_expensive = max(ranked_models, key=lambda m: m.get("monthly_cost", 0))
        current_model = most_expensive.get("model_name", "baseline")
        current = most_expensive
        logger.info(f"No current model specified, using most expensive as baseline: {current_model}")
    else:
        # Find current_model in ranked_models
        current = next((m for m in ranked_models if m.get("model_name") == current_model), None)
        if not current:
            raise InvalidInputError("INVALID INPUT – current_model not in list")
        logger.info(f"Found current model in ranked list: {current_model}")
    
    best = ranked_models[0]  # First item is best (lowest cost)
    current_cost = current.get("monthly_cost")
    best_cost = best.get("monthly_cost")
    
    logger.info(f"Current cost: {current_cost}, Best cost: {best_cost}")
    
    if current_cost is None or best_cost is None:
        raise InvalidInputError("INVALID INPUT – missing monthly_cost in models")
    savings_per_month = current_cost - best_cost
    roi_percent = (savings_per_month / current_cost) * 100 if current_cost else 0
    payback_weeks = 0 if savings_per_month <= 0 else 4
    
    result = {
        "current_model": current_model,
        "best_model": best.get("model_name"),
        "savings_per_month": round(savings_per_month, 2),
        "roi_percent": round(roi_percent, 2),
        "payback_weeks": payback_weeks,
    }
    
    logger.info(f"ROI result: {result}")
    return result 