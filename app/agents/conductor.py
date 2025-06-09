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
from app.schemas import WorkloadParams, CostModel, RankedModel, ROIAnalysis, StructuredResponse

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
        
        # Remove markdown fences if present
        cleaned_text = text
        if "```json" in text:
            # Extract content between ```json and ```
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                cleaned_text = json_match.group(1).strip()
                logger.info(f"Removed markdown fences, extracted: {cleaned_text[:200]}...")
                try:
                    result = json.loads(cleaned_text)
                    logger.info(f"Successfully parsed JSON after removing markdown fences")
                    return result
                except json.JSONDecodeError:
                    logger.info("Failed to parse JSON after removing markdown fences, continuing with regex")
        
        # If that fails, try to find JSON block within the text
        try:
            # PRIORITY 1: Look for JSON array starting with [ and ending with ]
            array_match = re.search(r'\[.*?\]', cleaned_text, re.DOTALL)
            if array_match:
                json_str = array_match.group()
                logger.info(f"Found JSON array: {json_str[:200]}...")
                return json.loads(json_str)
            
            # PRIORITY 2: Look for JSON object starting with { and ending with }
            json_match = re.search(r'\{.*?\}', cleaned_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                logger.info(f"Found JSON object: {json_str[:200]}...")
                return json.loads(json_str)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to extract JSON from text: {e}")
            
        # If still no luck, raise the original error
        logger.error(f"No valid JSON found in text: '{text[:200]}...'")
        raise json.JSONDecodeError(f"No valid JSON found in text", text, 0)

def is_greeting_or_casual_message(message: str) -> bool:
    """Check if the message is a greeting or casual message that needs a service introduction."""
    message_lower = message.lower().strip()
    
    # Common greetings and casual messages
    greeting_patterns = [
        "hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening",
        "what's up", "whats up", "sup", "yo", "hola", "howdy",
        "what is this", "what does this do", "help", "info", "about",
        "how does this work", "what can you do", "explain",
        "test", "testing", "ping", "status"
    ]
    
    # Check if message is just a greeting or very short casual message
    if len(message_lower) <= 20 and any(pattern in message_lower for pattern in greeting_patterns):
        return True
    
    # Check if message is asking about the service
    service_questions = [
        "what is this service", "what do you do", "how can you help",
        "what are your capabilities", "tell me about this"
    ]
    
    if any(question in message_lower for question in service_questions):
        return True
        
    return False

def generate_service_introduction() -> str:
    """Generate a friendly introduction to the Cost Architect service."""
    return """👋 **Hello! Welcome to Cost Architect**

I'm your AI cost optimization advisor for enterprise AI workloads. Here's what I can help you with:

## 🎯 **What I Do**
- **Analyze your AI automation needs** and design optimal solutions
- **Calculate costs** for different AI models (OpenAI, Anthropic, etc.)
- **Recommend the best model** based on your requirements and budget
- **Show ROI projections** and potential savings

## 💬 **How to Get Started**
Just describe your business process that you want to automate with AI. For example:

- *"We process 500 support emails daily, need AI to tag priority and draft replies"*
- *"Want to summarize 200 customer calls per day for our sales team"*
- *"Need AI to analyze 1000 documents weekly for compliance issues"*

## 📊 **What You'll Get**
- Custom AI solution architecture
- Cost comparison across multiple models
- ROI analysis with payback projections
- Clear recommendation for your specific use case

**Ready to optimize your AI costs?** Tell me about the business process you'd like to automate! 🚀"""

def generate_helpful_guidance() -> str:
    """Generate helpful guidance when the system can't process the user's request."""
    return """🤔 **I need more details to help you with AI cost optimization!**

Please describe your business automation need more clearly. Here are some examples:

## 📧 **Email/Support Automation**
*"We handle 500 support emails daily, want AI to tag priority and draft replies"*

## 📞 **Call/Meeting Analysis**  
*"Need to summarize 200 customer calls per day for our sales team"*

## 📄 **Document Processing**
*"Want AI to analyze 1000 contracts weekly for compliance review"*

## 💬 **Chat/Customer Service**
*"Process 300 chat messages daily, need automated responses for common questions"*

## 📊 **Data Analysis**
*"Analyze 500 survey responses monthly to extract insights and trends"*

**Include these details if possible:**
- 📈 **Volume**: How many items per day/week/month?
- ⏱️ **Speed requirement**: Real-time, within minutes, or batch processing?
- 🌍 **Region**: Where are you located? (for compliance/latency)
- 🔒 **Compliance**: Any requirements like GDPR, HIPAA, etc.?

**Try again with a clear business automation scenario!** 🚀"""

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
    
    async def run_interactive(self, message: Any = None, modified_workload: dict = None, original_data: dict = None) -> StructuredResponse:
        """Execute workflow and return structured data for interactive mode."""
        logger.info(f"=== EnterpriseAICostArchitect INTERACTIVE START ===")
        
        # If we have modified workload, restart from appropriate step
        if modified_workload and original_data:
            return await self._restart_from_modified_workload(modified_workload, original_data)
        
        # Check for greeting or casual messages first
        if is_greeting_or_casual_message(str(message)):
            logger.info("Detected greeting/casual message - returning service introduction")
            return StructuredResponse(
                solution_architect=None,
                workload_params=None,
                cost_table=None,
                ranked_models=None,
                roi_analysis=None,
                final_recommendation=generate_service_introduction()
            )
        
        # Otherwise, run full workflow with proper error handling
        try:
            return await self._run_full_workflow_structured(message)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Interactive workflow error: {error_msg}")
            
            # Return helpful guidance for various error scenarios
            if any(error_type in error_msg.lower() for error_type in ["invalid input", "failed to parse", "validation failed", "empty response"]):
                guidance_msg = generate_helpful_guidance()
            else:
                guidance_msg = generate_helpful_guidance()
            
            return StructuredResponse(
                solution_architect=None,
                workload_params=None,
                cost_table=None,
                ranked_models=None,
                roi_analysis=None,
                final_recommendation=guidance_msg
            )
    
    async def _restart_from_modified_workload(self, modified_workload: dict, original_data: dict) -> StructuredResponse:
        """Restart workflow from cost engine with modified workload parameters."""
        logger.info("=== RESTARTING WITH MODIFIED WORKLOAD ===")
        logger.info(f"Modified workload: {modified_workload}")
        
        # Start from STEP 2: Cost Engine with modified workload
        try:
            cost_table = await cost_engine.run(modified_workload)
            logger.info(f"Cost table generated: {len(cost_table)} models")
        except InvalidInputError as e:
            logger.error(f"CostEngine error: {e}")
            return StructuredResponse(
                solution_architect=None,
                workload_params=None,
                cost_table=None,
                ranked_models=None,
                roi_analysis=None,
                final_recommendation=generate_helpful_guidance()
            )
        except Exception as e:
            logger.error(f"CostEngine unexpected error: {e}")
            return StructuredResponse(
                solution_architect=None,
                workload_params=None,
                cost_table=None,
                ranked_models=None,
                roi_analysis=None,
                final_recommendation=generate_helpful_guidance()
            )
        
        # Continue with STEP 3-5 using new cost table
        try:
            return await self._run_from_model_scorer(modified_workload, cost_table, original_data.get("solution_architect"))
        except Exception as e:
            logger.error(f"Error in model scorer workflow: {e}")
            return StructuredResponse(
                solution_architect=original_data.get("solution_architect"),
                workload_params=WorkloadParams(**modified_workload) if modified_workload else None,
                cost_table=[CostModel(**model) for model in cost_table] if cost_table else None,
                ranked_models=None,
                roi_analysis=None,
                final_recommendation=generate_helpful_guidance()
            )
    
    async def _run_from_model_scorer(self, validated_workload: dict, cost_table: list, solution_architect_data: dict = None) -> StructuredResponse:
        """Run from Model Scorer step onwards."""
        
        # STEP 3: Model Scorer
        scorer_payload = {"workload": validated_workload, "cost_table": cost_table}
        scorer_input = json.dumps(scorer_payload)
        
        try:
            scorer_response = await self.model_scorer.run(scorer_input)
            ranked_models = extract_json_from_text(scorer_response)
            
            # Validate ranked_models
            if not isinstance(ranked_models, list) or not ranked_models:
                raise Exception("Model Scorer returned invalid data")
            
            if isinstance(ranked_models[0], str) and "INVALID INPUT" in ranked_models[0]:
                raise Exception(f"Model Scorer error: {ranked_models[0]}")
        except Exception as e:
            logger.error(f"Model Scorer error: {e}")
            return StructuredResponse(
                solution_architect=solution_architect_data,
                workload_params=WorkloadParams(**validated_workload),
                cost_table=[CostModel(**model) for model in cost_table],
                ranked_models=None,
                roi_analysis=None,
                final_recommendation=generate_helpful_guidance()
            )
        
        # STEP 4: ROI Calculator
        roi_payload = {
            "workload": validated_workload,
            "ranked_models": ranked_models,
            "current_model": validated_workload.get("current_model", "")
        }
        
        try:
            roi_report = await roi_calc.run(roi_payload)
        except Exception as e:
            logger.error(f"ROI Calculator error: {e}")
            return StructuredResponse(
                solution_architect=solution_architect_data,
                workload_params=WorkloadParams(**validated_workload),
                cost_table=[CostModel(**model) for model in cost_table],
                ranked_models=[RankedModel(**model) for model in ranked_models],
                roi_analysis=None,
                final_recommendation=generate_helpful_guidance()
            )
        
        # STEP 5: Recommendation Synthesizer
        final_payload = {
            "workload": validated_workload,
            "current_model": roi_report.get("current_model", ""),
            "ranked_models": ranked_models,
            "roi": roi_report
        }
        final_input = json.dumps(final_payload)
        
        try:
            final_response = await self.recommender.run(final_input)
        except Exception as e:
            logger.error(f"Recommendation Synthesizer error: {e}")
            return StructuredResponse(
                solution_architect=solution_architect_data,
                workload_params=WorkloadParams(**validated_workload),
                cost_table=[CostModel(**model) for model in cost_table],
                ranked_models=[RankedModel(**model) for model in ranked_models],
                roi_analysis=ROIAnalysis(**roi_report),
                final_recommendation=generate_helpful_guidance()
            )
        
        # Build successful structured response
        return StructuredResponse(
            solution_architect=solution_architect_data,
            workload_params=WorkloadParams(**validated_workload),
            cost_table=[CostModel(**model) for model in cost_table],
            ranked_models=[RankedModel(**model) for model in ranked_models],
            roi_analysis=ROIAnalysis(**roi_report),
            final_recommendation=final_response
        )
    
    async def _run_full_workflow_structured(self, message: Any) -> StructuredResponse:
        """Run full workflow and return structured data."""
        
        solution_architect_data = None
        
        # STEP 0: Check workload JSON or call Solution Architect
        if not self._is_valid_workload_json(str(message)):
            arch_response = await self.solution_architect.run(message)
            
            if isinstance(arch_response, str) and arch_response.startswith("INVALID INPUT –"):
                raise Exception("Invalid input from user")
            
            if not arch_response:
                raise Exception("Solution Architect returned empty response")
            
            try:
                arch_data = extract_json_from_text(str(arch_response))
                solution_architect_data = arch_data
                workload_json = arch_data.get("workload", {})
            except (json.JSONDecodeError, KeyError) as e:
                raise Exception("Failed to parse Solution Architect response")
        else:
            workload_json = json.loads(str(message))
        
        # STEP 1: Intake & Clarifier
        intake_input = json.dumps(workload_json)
        intake_response = await self.intake_agent.run(intake_input)
        
        if isinstance(intake_response, str) and intake_response.startswith("INVALID INPUT –"):
            raise Exception("Intake validation failed")
        
        try:
            validated_workload = extract_json_from_text(intake_response)
        except json.JSONDecodeError as e:
            raise Exception("Failed to parse Intake response")
        
        # STEP 2: Cost Engine
        try:
            cost_table = await cost_engine.run(validated_workload)
        except InvalidInputError as e:
            raise Exception(f"CostEngine error: {e}")
        
        # Continue from Model Scorer
        return await self._run_from_model_scorer(validated_workload, cost_table, solution_architect_data)

    # Keep the original run method for backward compatibility
    async def run(self, message: Any) -> Any:
        """Execute the full STEP 0-5 workflow per ENTERPRISE_AI_COST_ARCHITECT instructions."""
        logger.info(f"=== EnterpriseAICostArchitect START ===")
        logger.info(f"Input message: {str(message)[:200]}...")
        
        # Check for greeting or casual messages first
        if is_greeting_or_casual_message(str(message)):
            logger.info("Detected greeting/casual message - returning service introduction")
            return generate_service_introduction()
        
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
                return generate_helpful_guidance()
            
            # Check if response is empty or None
            if not arch_response:
                logger.error("Solution Architect returned empty response")
                return generate_helpful_guidance()
            
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
                return generate_helpful_guidance()
        else:
            # Message is already valid workload JSON
            logger.info("Message is valid workload JSON - skipping Solution Architect")
            try:
                workload_json = json.loads(str(message))
                logger.info(f"Parsed workload JSON: {workload_json}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse workload JSON: {e}")
                return generate_helpful_guidance()
        
        # STEP 1: Send workload JSON to Intake & Clarifier
        logger.info("=== STEP 1: Intake & Clarifier ===")
        intake_input = json.dumps(workload_json)
        logger.info(f"Intake input: {intake_input}")
        
        intake_response = await self.intake_agent.run(intake_input)
        logger.info(f"Intake response: {str(intake_response)[:300]}...")
        
        # Check for INVALID INPUT error
        if isinstance(intake_response, str) and intake_response.startswith("INVALID INPUT –"):
            logger.error(f"Intake returned error: {intake_response}")
            return generate_helpful_guidance()
        
        try:
            validated_workload = extract_json_from_text(intake_response)
            logger.info(f"Validated workload: {validated_workload}")
            logger.info(f"Validated workload keys: {list(validated_workload.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Intake response: {e}")
            return generate_helpful_guidance()
        
        # STEP 2: Pass workload JSON to CostEngine
        logger.info("=== STEP 2: Cost Engine ===")
        try:
            cost_table = await cost_engine.run(validated_workload)
            logger.info(f"Cost table generated: {len(cost_table)} models")
            logger.debug(f"Cost table: {cost_table}")
        except InvalidInputError as e:
            logger.error(f"CostEngine error: {e}")
            return generate_helpful_guidance()
        
        # STEP 3: Send { "workload":…, "cost_table":… } to Model Scorer
        logger.info("=== STEP 3: Model Scorer ===")
        scorer_payload = {
            "workload": validated_workload,
            "cost_table": cost_table
        }
        scorer_input = json.dumps(scorer_payload)
        logger.info(f"Scorer input payload size: {len(scorer_input)} chars")
        logger.debug(f"Scorer input payload: {scorer_input}")
        
        scorer_response = await self.model_scorer.run(scorer_input)
        logger.info(f"Scorer response: {str(scorer_response)[:300]}...")
        
        # Check for INVALID INPUT error
        if isinstance(scorer_response, str) and scorer_response.startswith("INVALID INPUT –"):
            logger.error(f"Model Scorer returned error: {scorer_response}")
            return generate_helpful_guidance()
        
        try:
            ranked_models = extract_json_from_text(scorer_response)
            logger.info(f"Ranked models: {len(ranked_models)} models")
            logger.debug(f"Ranked models: {ranked_models}")
            
            # Validate that ranked_models contains valid model objects, not error strings
            if not isinstance(ranked_models, list) or not ranked_models:
                logger.error("Model Scorer returned empty or invalid array")
                return generate_helpful_guidance()
            
            # Check if first element is an error string
            if isinstance(ranked_models[0], str) and "INVALID INPUT" in ranked_models[0]:
                logger.error(f"Model Scorer returned error in array: {ranked_models[0]}")
                return generate_helpful_guidance()
            
            # Validate that elements are model objects with required fields
            for i, model in enumerate(ranked_models):
                if not isinstance(model, dict) or not all(key in model for key in ["model_name", "monthly_cost"]):
                    logger.error(f"Model Scorer returned invalid model object at index {i}: {model}")
                    return generate_helpful_guidance()
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Model Scorer response: {e}")
            return generate_helpful_guidance()
        
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
            return generate_helpful_guidance()
        except Exception as e:
            logger.error(f"ROI Calculator unexpected error: {e}")
            return generate_helpful_guidance()
        
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
            return generate_helpful_guidance()
        
        logger.info("=== EnterpriseAICostArchitect COMPLETE ===")
        # Return ONLY the message produced by Recommendation Synthesizer
        return final_response 