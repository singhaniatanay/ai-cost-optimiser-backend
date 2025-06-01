import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import ChatRequest, ChatResponse, InteractiveRequest, InteractiveResponse, StructuredResponse
from app.agents.conductor import EnterpriseAICostArchitect, generate_helpful_guidance, generate_service_introduction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Set specific loggers to DEBUG for detailed debugging
logging.getLogger('app.agents.conductor').setLevel(logging.DEBUG)
logging.getLogger('app.adapters.openai_client').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

app = FastAPI(title="Cost Architect API", version="1.0.0")

# Add CORS middleware to allow requests from browser/HTML demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process chat messages through the Enterprise AI Cost Architect workflow."""
    logger.info(f"Received chat request with {len(request.messages)} messages")
    
    conductor = EnterpriseAICostArchitect()
    
    # Extract the latest message content to pass to the conductor
    if request.messages:
        latest_message = request.messages[-1].content
        logger.info(f"Latest message: {latest_message[:100]}...")
    else:
        latest_message = ""
        logger.warning("No messages in request")
    
    # Run the conductor workflow
    try:
        result = await conductor.run(latest_message)
        logger.info(f"Conductor completed successfully")
        return ChatResponse(answer=result)
    except Exception as e:
        logger.error(f"Conductor failed with exception: {e}")
        return ChatResponse(answer=generate_helpful_guidance())

@app.post("/v1/chat/interactive", response_model=InteractiveResponse)
async def interactive_chat(request: InteractiveRequest) -> InteractiveResponse:
    """Interactive chat that returns structured data for UI sliders and parameter modification."""
    logger.info(f"Received interactive request")
    
    conductor = EnterpriseAICostArchitect()
    
    try:
        # Handle initial message (like regular chat)
        if request.messages:
            latest_message = request.messages[-1].content
            logger.info(f"Processing initial message: {latest_message[:100]}...")
            
            # Check if it's a greeting first
            if latest_message and any(greeting in latest_message.lower() for greeting in ["hi", "hello", "hey", "what"]):
                return InteractiveResponse(simple_answer=generate_service_introduction())
            
            # Run full workflow and return structured data
            structured_data = await conductor.run_interactive(message=latest_message)
            return InteractiveResponse(structured_data=structured_data)
        
        # Handle modified workload parameters
        elif request.modified_workload and request.original_data:
            logger.info(f"Processing modified workload parameters")
            modified_workload_dict = request.modified_workload.dict()
            
            # Restart workflow with modified parameters
            structured_data = await conductor.run_interactive(
                modified_workload=modified_workload_dict,
                original_data=request.original_data
            )
            return InteractiveResponse(structured_data=structured_data)
        
        else:
            return InteractiveResponse(simple_answer=generate_helpful_guidance())
    
    except Exception as e:
        # Special handling for greeting detection
        if "GREETING_DETECTED" in str(e):
            return InteractiveResponse(simple_answer=generate_service_introduction())
        
        logger.error(f"Interactive conductor failed: {e}")
        return InteractiveResponse(simple_answer=generate_helpful_guidance())

@app.post("/v1/chat/update-params", response_model=InteractiveResponse)
async def update_parameters(request: InteractiveRequest) -> InteractiveResponse:
    """Update specific parameters and recalculate costs in real-time."""
    logger.info(f"Received parameter update request")
    
    if not request.modified_workload or not request.original_data:
        return InteractiveResponse(simple_answer="Missing required parameters for update")
    
    conductor = EnterpriseAICostArchitect()
    
    try:
        modified_workload_dict = request.modified_workload.dict()
        logger.info(f"Updated parameters: {modified_workload_dict}")
        
        # Restart workflow with modified parameters
        structured_data = await conductor.run_interactive(
            modified_workload=modified_workload_dict,
            original_data=request.original_data
        )
        return InteractiveResponse(structured_data=structured_data)
    
    except Exception as e:
        logger.error(f"Parameter update failed: {e}")
        return InteractiveResponse(simple_answer=generate_helpful_guidance())

@app.get("/healthz")
async def healthcheck():
    """Health check endpoint."""
    return {"status": "ok"} 