#!/usr/bin/env python3
"""
Simple test with direct JSON workload to verify constraint flags
"""

import asyncio
import json
from app.agents.conductor import EnterpriseAICostArchitect

async def test_constraint_flags():
    conductor = EnterpriseAICostArchitect()
    
    # Direct JSON workload with strict latency that should show constraint violations
    workload_json = {
        "calls_per_day": 500,
        "avg_input_tokens": 300,
        "avg_output_tokens": 150,
        "latency_sla_ms": 450,  # Strict latency
        "region": "US",
        "compliance_constraints": [],
        "current_model": ""
    }
    
    print("🧪 TESTING CONSTRAINT FLAGS")
    print("=" * 50)
    print(f"📊 Workload Parameters:")
    print(f"   • calls_per_day: {workload_json['calls_per_day']}")
    print(f"   • avg_input_tokens: {workload_json['avg_input_tokens']}")
    print(f"   • avg_output_tokens: {workload_json['avg_output_tokens']}")
    print(f"   • latency_sla_ms: {workload_json['latency_sla_ms']}ms")
    
    try:
        # Use interactive mode to get structured response
        result = await conductor.run_interactive(json.dumps(workload_json))
        
        if result.ranked_models:
            print(f"\n✅ SUCCESS! Got {len(result.ranked_models)} models with constraint flags:")
            print("-" * 60)
            
            for i, model in enumerate(result.ranked_models, 1):
                status = "✅ SUITABLE" if model.suitable else "❌ NOT SUITABLE"
                violations = ", ".join(model.constraint_violations) if model.constraint_violations else "None"
                
                print(f"{i}. {model.model_name}")
                print(f"   • Cost: ₹{model.monthly_cost:,.2f}/month")
                print(f"   • Latency: {model.p90_latency_ms}ms")
                print(f"   • Context OK: {'✅' if model.context_adequate else '❌'}")
                print(f"   • Latency OK: {'✅' if model.latency_adequate else '❌'}")
                print(f"   • Status: {status}")
                print(f"   • Violations: {violations}")
                print(f"   • Score: {model.composite_score:.2f}")
                print()
            
            # Show summary
            suitable_count = sum(1 for m in result.ranked_models if m.suitable)
            print(f"📊 SUMMARY:")
            print(f"   • Total models: {len(result.ranked_models)}")
            print(f"   • Suitable models: {suitable_count}")
            print(f"   • Models with violations: {len(result.ranked_models) - suitable_count}")
            
        else:
            print(f"❌ No ranked models in response")
            print(f"Final recommendation: {result.final_recommendation}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_constraint_flags()) 