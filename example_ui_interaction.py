#!/usr/bin/env python3
"""
Example script showing how a UI would interact with the interactive Cost Architect API.
This demonstrates the flow for real-time parameter updates with sliders.
"""

import requests
import json
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"

def initial_analysis(user_message: str) -> Dict[str, Any]:
    """Step 1: Get initial analysis with structured data."""
    print(f"🔍 Getting initial analysis for: {user_message[:50]}...")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/interactive",
        json={
            "messages": [{"role": "user", "content": user_message}]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("structured_data"):
            print("✅ Received structured data!")
            return data["structured_data"]
        else:
            print(f"💬 Simple response: {data.get('simple_answer', 'No response')}")
            return {}
    else:
        print(f"❌ Error: {response.status_code}")
        return {}

def update_parameters(original_data: Dict[str, Any], new_params: Dict[str, Any]) -> Dict[str, Any]:
    """Step 2: Update parameters and get recalculated results."""
    print(f"🔄 Updating parameters: {new_params}")
    
    # Build the modified workload from original + changes
    current_workload = original_data["workload_params"]
    modified_workload = {**current_workload, **new_params}
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/update-params",
        json={
            "modified_workload": modified_workload,
            "original_data": original_data
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("structured_data"):
            print("✅ Received updated analysis!")
            return data["structured_data"]
        else:
            print(f"❌ Error in response: {data.get('simple_answer')}")
            return {}
    else:
        print(f"❌ Error: {response.status_code}")
        return {}

def print_analysis_summary(data: Dict[str, Any]):
    """Print a summary of the analysis results."""
    if not data:
        return
    
    workload = data["workload_params"]
    roi = data["roi_analysis"]
    models = data["ranked_models"]
    
    print("\n" + "="*60)
    print("📊 COST ANALYSIS SUMMARY")
    print("="*60)
    print(f"📈 Volume: {workload['calls_per_day']:,} calls/day")
    print(f"📝 Input tokens: {workload['avg_input_tokens']:,}")
    print(f"📤 Output tokens: {workload['avg_output_tokens']:,}")
    print(f"⏱️ Latency SLA: {workload['latency_sla_ms']:,}ms")
    print(f"🌍 Region: {workload['region']}")
    
    print(f"\n💰 ROI ANALYSIS:")
    print(f"   Current: {roi['current_model']}")
    print(f"   Best: {roi['best_model']}")
    print(f"   Monthly savings: ₹{roi['savings_per_month']:,.2f}")
    print(f"   ROI: {roi['roi_percent']:.1f}%")
    print(f"   Payback: {roi['payback_weeks']} weeks")
    
    print(f"\n🏆 TOP MODELS:")
    for i, model in enumerate(models[:3], 1):
        print(f"   {i}. {model['model_name']}: ₹{model['monthly_cost']:,.0f}/month (score: {model['composite_score']:.2f})")
    print()

def simulate_ui_interaction():
    """Simulate a complete UI interaction with parameter updates."""
    
    # Step 1: Initial analysis
    user_input = "We process 500 support emails daily, need AI to tag priority and draft replies"
    initial_data = initial_analysis(user_input)
    
    if not initial_data:
        print("❌ Failed to get initial analysis")
        return
    
    print_analysis_summary(initial_data)
    
    # Step 2: Simulate user adjusting sliders
    print("🎛️ SIMULATING UI SLIDER ADJUSTMENTS...")
    
    # Scenario 1: User increases volume
    print("\n📈 User slides 'Calls per day' from 500 to 1000...")
    updated_data = update_parameters(initial_data, {"calls_per_day": 1000})
    print_analysis_summary(updated_data)
    
    # Scenario 2: User increases output token requirement  
    print("\n📝 User slides 'Output tokens' from 150 to 300...")
    updated_data = update_parameters(updated_data, {"avg_output_tokens": 300})
    print_analysis_summary(updated_data)
    
    # Scenario 3: User tightens latency requirement
    print("\n⏱️ User slides 'Latency SLA' from 120000ms to 1000ms...")
    updated_data = update_parameters(updated_data, {"latency_sla_ms": 1000})
    print_analysis_summary(updated_data)
    
    print("🎉 Interactive simulation complete!")

if __name__ == "__main__":
    print("🚀 Cost Architect Interactive UI Simulation")
    print("=" * 50)
    
    try:
        simulate_ui_interaction()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running:")
        print("   cd cost_architect && python -m uvicorn app.main:app --reload --port 8000")
    except Exception as e:
        print(f"❌ Error: {e}") 