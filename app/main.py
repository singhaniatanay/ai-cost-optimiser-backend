import logging
from fastapi import FastAPI
from app.schemas import ChatRequest, ChatResponse
from app.agents.conductor import EnterpriseAICostArchitect

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
        return ChatResponse(answer=f"Internal error: {str(e)}")

@app.get("/healthz")
async def healthcheck():
    """Health check endpoint."""
    return {"status": "ok"} 