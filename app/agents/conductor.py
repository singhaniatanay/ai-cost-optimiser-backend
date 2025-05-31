import json
import logging
import re
from typing import Any, List, Dict
from app.agents.base import BaseAgent, InvalidInputError
from app.agents.configs import ENTERPRISE_AI_COST_ARCHITECT
from app.agents.solution_arch import SolutionArchitectAgent
from app.agents.intake import IntakeAgent
from app.agents.model_scorer import ModelScorerAgent
from app.agents.recommender import RecommenderAgent
from app.agents import cost_engine, roi_calc

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> dict:
    """Extract JSON object from text that might contain extra content."""
    try:
        # First, try parsing the entire text as JSON
        result = json.loads(text.strip())
        logger.info(f"Successfully parsed JSON directly from response")
        return result
    except json.JSONDecodeError:
        logger.info("Direct JSON parsing failed, attempting to extract JSON from text")
        # If that fails, try to find JSON block within the text
        try:
            # Look for JSON object starting with { and ending with }
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                logger.info(f"Found JSON object: {json_str[:200]}...")
                return json.loads(json_str)
            
            # Also try to find JSON array starting with [ and ending with ]
            array_match = re.search(r'\[.*\]', text, re.DOTALL)
            if array_match:
                json_str = array_match.group()
                logger.info(f"Found JSON array: {json_str[:200]}...")
                return json.loads(json_str)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to extract JSON from text: {e}")
            
        # If still no luck, raise the original error
        logger.error(f"No valid JSON found in text: '{text[:200]}...'")
        raise json.JSONDecodeError(f"No valid JSON found in text", text, 0)

class EnterpriseAICostArchitect(BaseAgent):
    def __init__(self):
        self.config = ENTERPRISE_AI_COST_ARCHITECT
        self.solution_architect = SolutionArchitectAgent()
        self.intake_agent = IntakeAgent()
        self.model_scorer = ModelScorerAgent()
        self.recommender = RecommenderAgent()
    
    def _is_valid_workload_json(self, message: str) -> bool:
        """Check if message is valid workload JSON with required keys."""
        try:
            data = json.loads(message)
            is_valid = all(key in data for key in ["calls_per_day", "avg_input_tokens", "avg_output_tokens"])
            logger.info(f"Workload JSON validation: {is_valid}")
            if is_valid:
                logger.debug(f"Valid workload JSON: {data}")
            return is_valid
        except (json.JSONDecodeError, TypeError) as e:
            logger.info(f"Message is not valid JSON: {e}")
            return False
    
    async def run(self, message: Any) -> Any:
        """Execute the full STEP 0-5 workflow per ENTERPRISE_AI_COST_ARCHITECT instructions."""
        logger.info(f"=== EnterpriseAICostArchitect START ===")
        logger.info(f"Input message: {str(message)[:200]}...")
        
        # STEP 0: Check if user's first message is valid workload JSON
        logger.info("=== STEP 0: Checking workload JSON validity ===")
        if not self._is_valid_workload_json(str(message)):
            logger.info("Message is NOT valid workload JSON - calling Solution Architect")
            
            # Pass raw message to Solution Architect – OPT Extractor
            arch_response = await self.solution_architect.run(message)
            logger.info(f"Solution Architect response type: {type(arch_response)}")
            logger.info(f"Solution Architect response: {str(arch_response)[:300]}...")
            
            # Check for INVALID INPUT error
            if isinstance(arch_response, str) and arch_response.startswith("INVALID INPUT –"):
                logger.error(f"Solution Architect returned error: {arch_response}")
                return arch_response
            
            # Check if response is empty or None
            if not arch_response:
                logger.error("Solution Architect returned empty response")
                return "INVALID INPUT – Solution Architect returned empty response"
            
            try:
                # Extract opt_task, architecture, workload from response
                logger.info("Attempting to parse Solution Architect JSON response")
                arch_data = extract_json_from_text(str(arch_response))
                logger.info(f"Parsed architecture data: {arch_data}")
                
                opt_task = arch_data.get("opt_task", "")
                architecture = arch_data.get("architecture", [])
                workload = arch_data.get("workload", {})
                
                logger.info(f"Extracted - opt_task: {opt_task}")
                logger.info(f"Extracted - architecture: {architecture}")
                logger.info(f"Extracted - workload: {workload}")
                
                # Echo architecture back to user (this would be logged/shown in a real app)
                architecture_summary = " → ".join(architecture) if architecture else "No architecture provided"
                echo_message = f"AI Solution drafted: {opt_task} → {architecture_summary}"
                logger.info(f"Architecture echo: {echo_message}")
                
                # Continue to STEP 1 with workload JSON
                workload_json = workload
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Failed to parse Solution Architect response: {e}")
                logger.error(f"Raw response: '{arch_response}'")
                return f"INVALID INPUT – Solution Architect response not parseable: {e}"
        else:
            # Message is already valid workload JSON
            logger.info("Message is valid workload JSON - skipping Solution Architect")
            try:
                workload_json = json.loads(str(message))
                logger.info(f"Parsed workload JSON: {workload_json}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse workload JSON: {e}")
                return "INVALID INPUT – Invalid JSON format"
        
        # STEP 1: Send workload JSON to Intake & Clarifier
        logger.info("=== STEP 1: Intake & Clarifier ===")
        intake_input = json.dumps(workload_json)
        logger.info(f"Intake input: {intake_input}")
        
        intake_response = await self.intake_agent.run(intake_input)
        logger.info(f"Intake response: {str(intake_response)[:300]}...")
        
        # Check for INVALID INPUT error
        if isinstance(intake_response, str) and intake_response.startswith("INVALID INPUT –"):
            logger.error(f"Intake returned error: {intake_response}")
            return intake_response
        
        try:
            validated_workload = extract_json_from_text(intake_response)
            logger.info(f"Validated workload: {validated_workload}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Intake response: {e}")
            return "INVALID INPUT – Intake response not valid JSON"
        
        # STEP 2: Pass workload JSON to CostEngine
        logger.info("=== STEP 2: Cost Engine ===")
        try:
            cost_table = await cost_engine.run(validated_workload)
            logger.info(f"Cost table generated: {len(cost_table)} models")
            logger.debug(f"Cost table: {cost_table}")
        except InvalidInputError as e:
            logger.error(f"CostEngine error: {e}")
            return str(e)
        
        # STEP 3: Send { "workload":…, "cost_table":… } to Model Scorer
        logger.info("=== STEP 3: Model Scorer ===")
        scorer_payload = {
            "workload": validated_workload,
            "cost_table": cost_table
        }
        scorer_input = json.dumps(scorer_payload)
        logger.info(f"Scorer input payload size: {len(scorer_input)} chars")
        
        scorer_response = await self.model_scorer.run(scorer_input)
        logger.info(f"Scorer response: {str(scorer_response)[:300]}...")
        
        # Check for INVALID INPUT error
        if isinstance(scorer_response, str) and scorer_response.startswith("INVALID INPUT –"):
            logger.error(f"Model Scorer returned error: {scorer_response}")
            return scorer_response
        
        try:
            ranked_models = extract_json_from_text(scorer_response)
            logger.info(f"Ranked models: {len(ranked_models)} models")
            logger.debug(f"Ranked models: {ranked_models}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Model Scorer response: {e}")
            return "INVALID INPUT – Model Scorer response not valid JSON"
        
        # STEP 4: Send to ROI & Payback Calculator
        logger.info("=== STEP 4: ROI & Payback Calculator ===")
        roi_payload = {
            "workload": validated_workload,
            "ranked_models": ranked_models,
            "current_model": validated_workload.get("current_model", "")
        }
        logger.info(f"ROI payload current_model: {roi_payload['current_model']}")
        
        try:
            roi_report = await roi_calc.run(roi_payload)
            logger.info(f"ROI report: {roi_report}")
        except InvalidInputError as e:
            logger.error(f"ROI Calculator error: {e}")
            return str(e)
        
        # STEP 5: Send to Recommendation Synthesizer
        logger.info("=== STEP 5: Recommendation Synthesizer ===")
        final_payload = {
            "workload": validated_workload,
            "current_model": roi_report.get("current_model", ""),
            "ranked_models": ranked_models,
            "roi": roi_report
        }
        final_input = json.dumps(final_payload)
        logger.info(f"Final payload size: {len(final_input)} chars")
        logger.info(f"Final payload current_model: {final_payload['current_model']}")
        
        final_response = await self.recommender.run(final_input)
        logger.info(f"Final response: {str(final_response)[:300]}...")
        
        # Check for INVALID INPUT error
        if isinstance(final_response, str) and final_response.startswith("INVALID INPUT –"):
            logger.error(f"Recommendation Synthesizer returned error: {final_response}")
            return final_response
        
        logger.info("=== EnterpriseAICostArchitect COMPLETE ===")
        # Return ONLY the message produced by Recommendation Synthesizer
        return final_response 