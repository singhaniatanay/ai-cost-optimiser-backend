#!/usr/bin/env python3
"""
Test script to verify the new Model Scorer behavior with constraint flags
"""

import asyncio
import json
from app.agents.model_scorer import ModelScorerAgent

async def test_new_model_scorer():
    scorer = ModelScorerAgent()
    
    # Test payload with strict latency to show constraint violations
    test_payload = {
        "workload": {
            "calls_per_day": 500,
            "avg_input_tokens": 300,
            "avg_output_tokens": 150,
            "latency_sla_ms": 450  # Strict latency that will cause violations
        },
        "cost_table": [
            {
                "model_name": "gpt-4o",
                "monthly_cost": 1125.0,
                "p90_latency_ms": 360,
                "context_window_tokens": 128000
            },
            {
                "model_name": "gpt-4o-mini",
                "monthly_cost": 33.75,
                "p90_latency_ms": 470,
                "context_window_tokens": 128000
            },
            {
                "model_name": "claude-4-opus",
                "monthly_cost": 3375.0,
                "p90_latency_ms": 2750,
                "context_window_tokens": 200000
            },
            {
                "model_name": "gemini-1.5-flash",
                "monthly_cost": 16.88,
                "p90_latency_ms": 200,
                "context_window_tokens": 1000000
            }
        ]
    }
    
    print("🧪 TESTING NEW MODEL SCORER")
    print("=" * 50)
    print(f"📊 Test Parameters:")
    print(f"   • Latency SLA: {test_payload['workload']['latency_sla_ms']}ms")
    print(f"   • Token requirement: {test_payload['workload']['avg_input_tokens'] + test_payload['workload']['avg_output_tokens']} tokens")
    print(f"   • Models being tested: {len(test_payload['cost_table'])}")
    
    try:
        input_json = json.dumps(test_payload)
        response = await scorer.run(input_json)
        
        print(f"\n🔄 Model Scorer Response:")
        print(f"Response type: {type(response)}")
        print(f"Response length: {len(str(response))}")
        print(f"Raw response preview: {str(response)[:200]}...")
        
        # Try to parse the response
        if isinstance(response, str):
            try:
                parsed = json.loads(response)
                print(f"\n✅ Successfully parsed JSON response!")
                print(f"Number of models returned: {len(parsed)}")
                
                print(f"\n📋 DETAILED RESULTS:")
                for i, model in enumerate(parsed, 1):
                    status = "✅ SUITABLE" if model.get('suitable', False) else "❌ NOT SUITABLE"
                    violations = model.get('constraint_violations', [])
                    violations_str = f" ({', '.join(violations)})" if violations else ""
                    
                    print(f"   {i}. {model['model_name']}")
                    print(f"      • Cost: ₹{model['monthly_cost']:.2f}/month")
                    print(f"      • Latency: {model['p90_latency_ms']}ms")
                    print(f"      • Score: {model.get('composite_score', 'N/A'):.2f}")
                    print(f"      • Context OK: {'✅' if model.get('context_adequate', False) else '❌'}")
                    print(f"      • Latency OK: {'✅' if model.get('latency_adequate', False) else '❌'}")
                    print(f"      • Status: {status}{violations_str}")
                    print()
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Raw response: {response}")
        else:
            print(f"❌ Unexpected response type: {type(response)}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_new_model_scorer()) 