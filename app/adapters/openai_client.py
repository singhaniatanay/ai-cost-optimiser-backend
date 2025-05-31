import openai
import logging
from app.config import settings

logger = logging.getLogger(__name__)

async def chat(prompt: str, model: str, temperature: float, top_p: float, timeout_s: int) -> str:
    logger.info(f"OpenAI Chat Request - Model: {model}, Temperature: {temperature}, Top_p: {top_p}")
    logger.debug(f"OpenAI Chat Prompt: {prompt[:200]}...")  # Log first 200 chars
    
    try:
        client = openai.AsyncClient(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            top_p=top_p,
            timeout=timeout_s,
        )
        
        content = response.choices[0].message.content
        logger.info(f"OpenAI Chat Response received - Length: {len(content) if content else 0} chars")
        logger.debug(f"OpenAI Chat Response: {content[:500]}...")  # Log first 500 chars
        
        return content
        
    except Exception as e:
        logger.error(f"OpenAI Chat Error: {str(e)}")
        raise 