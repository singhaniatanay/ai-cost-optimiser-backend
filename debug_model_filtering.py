#!/usr/bin/env python3
"""
Debug script to understand why only 4 models are returned from the API.
This will show the filtering logic step by step.
"""

def debug_model_filtering():
    # Cost catalog from cost_engine.py
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

    # Example workload parameters (typical from demo)
    workload_params = {
        "calls_per_day": 500,
        "avg_input_tokens": 300,
        "avg_output_tokens": 150,
        "latency_sla_ms": 450  # 450ms - very strict latency requirement
    }

    print("🔍 MODEL FILTERING DEBUG")
    print("=" * 60)
    print(f"📊 Workload Parameters:")
    print(f"   • calls_per_day: {workload_params['calls_per_day']}")
    print(f"   • avg_input_tokens: {workload_params['avg_input_tokens']}")
    print(f"   • avg_output_tokens: {workload_params['avg_output_tokens']}")
    print(f"   • latency_sla_ms: {workload_params['latency_sla_ms']} ({workload_params['latency_sla_ms']/1000} seconds)")
    
    total_tokens_needed = workload_params["avg_input_tokens"] + workload_params["avg_output_tokens"]
    print(f"   • total_tokens_needed: {total_tokens_needed}")
    
    print(f"\n🔧 Filtering Criteria:")
    print(f"   1. Context window must be >= {total_tokens_needed} tokens")
    print(f"   2. Latency must be <= {workload_params['latency_sla_ms']} ms")
    
    print(f"\n📋 ANALYSIS RESULTS:")
    print(f"{'Model':<20} {'Context':<12} {'Latency':<10} {'Context OK':<12} {'Latency OK':<12} {'PASS':<8}")
    print("-" * 80)
    
    viable_models = []
    
    for model in cost_catalog:
        context_ok = model["context_window_tokens"] >= total_tokens_needed
        latency_ok = model["latency_ms"] <= workload_params["latency_sla_ms"]
        passes = context_ok and latency_ok
        
        if passes:
            viable_models.append(model)
        
        print(f"{model['model_name']:<20} {model['context_window_tokens']:<12} {model['latency_ms']:<10} {'✅' if context_ok else '❌':<12} {'✅' if latency_ok else '❌':<12} {'✅' if passes else '❌':<8}")
    
    print(f"\n🎯 SUMMARY:")
    print(f"   • Total models in catalog: {len(cost_catalog)}")
    print(f"   • Models passing filters: {len(viable_models)}")
    print(f"   • Filtered out: {len(cost_catalog) - len(viable_models)}")
    
    print(f"\n✅ VIABLE MODELS:")
    for i, model in enumerate(viable_models, 1):
        print(f"   {i}. {model['model_name']} (context: {model['context_window_tokens']:,}, latency: {model['latency_ms']}ms)")
    
    print(f"\n❌ FILTERED OUT MODELS:")
    filtered_out = [m for m in cost_catalog if m not in viable_models]
    for model in filtered_out:
        reasons = []
        if model["context_window_tokens"] < total_tokens_needed:
            reasons.append(f"context too small ({model['context_window_tokens']} < {total_tokens_needed})")
        if model["latency_ms"] > workload_params["latency_sla_ms"]:
            reasons.append(f"latency too high ({model['latency_ms']} > {workload_params['latency_sla_ms']})")
        print(f"   • {model['model_name']}: {', '.join(reasons)}")

    return len(viable_models)

if __name__ == "__main__":
    result = debug_model_filtering()
    print(f"\n🏁 Result: {result} models would be returned by the API") 