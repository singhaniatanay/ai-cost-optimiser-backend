#!/usr/bin/env python3
"""Test script for the new interactive functionality."""

import asyncio
import sys
import os
sys.path.append('.')

from app.agents.conductor import EnterpriseAICostArchitect

async def test_interactive():
    conductor = EnterpriseAICostArchitect()
    
    # Test 1: Initial analysis
    print('🔍 Testing initial analysis...')
    try:
        result = await conductor.run_interactive(
            message='We process 200 support emails daily, need AI to tag priority and draft replies'
        )
        print('✅ Initial analysis successful!')
        print(f'   Workload: {result.workload_params.calls_per_day} calls/day')
        print(f'   Best model: {result.roi_analysis.best_model}')
        print(f'   Monthly cost: ₹{result.ranked_models[0].monthly_cost:,.0f}')
        
        # Test 2: Parameter update
        print('\n🔄 Testing parameter update...')
        modified_workload = result.workload_params.dict()
        modified_workload['calls_per_day'] = 1000  # Double the volume
        
        updated_result = await conductor.run_interactive(
            modified_workload=modified_workload,
            original_data=result.dict()
        )
        print('✅ Parameter update successful!')
        print(f'   Updated workload: {updated_result.workload_params.calls_per_day} calls/day')
        print(f'   Updated monthly cost: ₹{updated_result.ranked_models[0].monthly_cost:,.0f}')
        
        # Test 3: Greeting handling
        print('\n👋 Testing greeting detection...')
        try:
            greeting_result = await conductor.run_interactive(message='Hello')
            print('❌ Greeting should raise exception for structured mode')
            return False
        except Exception as e:
            if "GREETING_DETECTED" in str(e):
                print('✅ Greeting detection works correctly!')
            else:
                print(f'❌ Unexpected greeting error: {e}')
                return False
        
        return True
        
    except Exception as e:
        print(f'❌ Test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set up environment
    os.environ.setdefault('OPENAI_API_KEY', 'test-key')
    
    print('🚀 Testing Interactive Cost Architect')
    print('=' * 50)
    
    result = asyncio.run(test_interactive())
    print(f'\n🏁 Test result: {"PASSED" if result else "FAILED"}') 