from app.agents.base import InvalidInputError

async def run(workload: dict) -> list[dict]:
    # Validate input
    required_keys = ["calls_per_day", "avg_input_tokens", "avg_output_tokens"]
    for key in required_keys:
        if key not in workload or not isinstance(workload[key], int) or workload[key] < 1:
            raise InvalidInputError(f"INVALID INPUT – missing or invalid {key}")

    # Example static cost_catalog (should be loaded from CSV in real app)
    cost_catalog = [
        {
            "model_name": "gpt-4o",
            "price_per_1k_tokens": 10.0,
            "latency_ms": 500,
            "context_window_tokens": 128000,
        },
        {
            "model_name": "gpt-3.5-turbo",
            "price_per_1k_tokens": 2.0,
            "latency_ms": 350,
            "context_window_tokens": 16000,
        },
    ]

    calls_per_day = workload["calls_per_day"]
    avg_input_tokens = workload["avg_input_tokens"]
    avg_output_tokens = workload["avg_output_tokens"]

    results = []
    for row in cost_catalog:
        monthly_cost = (
            calls_per_day * 30 * (avg_input_tokens + avg_output_tokens) * row["price_per_1k_tokens"] / 1000
        )
        results.append({
            "model_name": row["model_name"],
            "monthly_cost": round(monthly_cost, 2),
            "p90_latency_ms": row["latency_ms"],
            "context_window_tokens": row["context_window_tokens"],
        })
    results.sort(key=lambda x: x["monthly_cost"])
    return results 