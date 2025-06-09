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
      "price_per_1k_tokens": 0.005,
      "latency_ms": 360,
      "context_window_tokens": 128000
    },
    {
      "model_name": "gpt-4o-mini",
      "price_per_1k_tokens": 0.00015,
      "latency_ms": 470,
      "context_window_tokens": 128000
    },
    {
      "model_name": "gpt-4.1",
      "price_per_1k_tokens": 0.002,
      "latency_ms": 480,
      "context_window_tokens": 1000000
    },
    {
      "model_name": "gpt-4.1-mini",
      "price_per_1k_tokens": 0.0004,
      "latency_ms": 650,
      "context_window_tokens": 1000000
    },
    {
      "model_name": "gpt-4.1-nano",
      "price_per_1k_tokens": 0.0001,
      "latency_ms": 370,
      "context_window_tokens": 1000000
    },
    {
      "model_name": "claude-4-opus",
      "price_per_1k_tokens": 0.015,
      "latency_ms": 2750,
      "context_window_tokens": 200000
    },
    {
      "model_name": "claude-4-sonnet",
      "price_per_1k_tokens": 0.003,
      "latency_ms": 1330,
      "context_window_tokens": 200000
    },
    {
      "model_name": "claude-3.5-haiku",
      "price_per_1k_tokens": 0.0008,
      "latency_ms": 630,
      "context_window_tokens": 200000
    },
    {
      "model_name": "gemini-1.5-pro",
      "price_per_1k_tokens": 0.00125,
      "latency_ms": 430,
      "context_window_tokens": 2000000
    },
    {
      "model_name": "gemini-1.5-flash",
      "price_per_1k_tokens": 0.000075,
      "latency_ms": 200,
      "context_window_tokens": 1000000
    }
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