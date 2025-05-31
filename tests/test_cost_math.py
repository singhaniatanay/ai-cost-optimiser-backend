import pytest
import asyncio
from app.agents import cost_engine, roi_calc
from app.agents.base import InvalidInputError

@pytest.mark.asyncio
async def test_cost_engine_run_formula():
    workload = {
        "calls_per_day": 1000,
        "avg_input_tokens": 100,
        "avg_output_tokens": 50,
    }
    results = await cost_engine.run(workload)
    # gpt-3.5-turbo: price_per_1k_tokens=2.0, context_window=16000, latency=350
    # monthly_cost = 1000*30*(100+50)*2/1000 = 9000
    gpt35 = next(r for r in results if r["model_name"] == "gpt-3.5-turbo")
    assert gpt35["monthly_cost"] == 9000.0
    assert gpt35["p90_latency_ms"] == 350
    assert gpt35["context_window_tokens"] == 16000
    # gpt-4o: price_per_1k_tokens=10.0
    gpt4o = next(r for r in results if r["model_name"] == "gpt-4o")
    assert gpt4o["monthly_cost"] == 45000.0
    assert gpt4o["p90_latency_ms"] == 500
    assert gpt4o["context_window_tokens"] == 128000
    # Sorted by cost
    assert results[0]["model_name"] == "gpt-3.5-turbo"
    assert results[1]["model_name"] == "gpt-4o"

@pytest.mark.asyncio
async def test_cost_engine_run_invalid():
    with pytest.raises(InvalidInputError):
        await cost_engine.run({})
    with pytest.raises(InvalidInputError):
        await cost_engine.run({"calls_per_day": 0, "avg_input_tokens": 1, "avg_output_tokens": 1})
    with pytest.raises(InvalidInputError):
        await cost_engine.run({"calls_per_day": 1, "avg_input_tokens": "bad", "avg_output_tokens": 1})

@pytest.mark.asyncio
async def test_roi_calc_run_formula():
    payload = {
        "workload": {},
        "ranked_models": [
            {"model_name": "gpt-3.5-turbo", "monthly_cost": 9000.0},
            {"model_name": "gpt-4o", "monthly_cost": 45000.0},
        ],
        "current_model": "gpt-4o",
    }
    result = await roi_calc.run(payload)
    assert result["current_model"] == "gpt-4o"
    assert result["best_model"] == "gpt-3.5-turbo"
    assert result["savings_per_month"] == 36000.0
    assert result["roi_percent"] == 80.0
    assert result["payback_weeks"] == 4
    # If savings_per_month <= 0, payback_weeks == 0
    payload2 = {
        "workload": {},
        "ranked_models": [
            {"model_name": "gpt-4o", "monthly_cost": 45000.0},
            {"model_name": "gpt-3.5-turbo", "monthly_cost": 9000.0},
        ],
        "current_model": "gpt-4o",
    }
    result2 = await roi_calc.run(payload2)
    assert result2["payback_weeks"] == 4
    payload3 = {
        "workload": {},
        "ranked_models": [
            {"model_name": "gpt-3.5-turbo", "monthly_cost": 9000.0},
            {"model_name": "gpt-4o", "monthly_cost": 45000.0},
        ],
        "current_model": "gpt-3.5-turbo",
    }
    result3 = await roi_calc.run(payload3)
    assert result3["payback_weeks"] == 0

@pytest.mark.asyncio
async def test_roi_calc_run_invalid():
    with pytest.raises(InvalidInputError):
        await roi_calc.run({})
    with pytest.raises(InvalidInputError):
        await roi_calc.run({"workload": {}, "ranked_models": [], "current_model": "gpt-4o"})
    with pytest.raises(InvalidInputError):
        await roi_calc.run({"workload": {}, "ranked_models": [{"model_name": "gpt-3.5-turbo", "monthly_cost": 9000.0}], "current_model": "gpt-4o"})
    with pytest.raises(InvalidInputError):
        await roi_calc.run({"workload": {}, "ranked_models": [{"model_name": "gpt-3.5-turbo"}], "current_model": "gpt-3.5-turbo"}) 