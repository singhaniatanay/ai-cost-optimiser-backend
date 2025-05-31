from typing import Any
from app.agents.base import BaseAgent
from app.agents.configs import MODEL_SCORER
from app.adapters import openai_client

class ModelScorerAgent(BaseAgent):
    def __init__(self):
        self.config = MODEL_SCORER
    
    async def run(self, message: Any) -> Any:
        prompt = f"{self.config['agent_role']}\n\n{self.config['agent_goal']}\n\n{self.config['agent_instructions']}\n\nUser message: {message}"
        
        response = await openai_client.chat(
            prompt=prompt,
            model=self.config["model"],
            temperature=float(self.config["temperature"]),
            top_p=float(self.config["top_p"]),
            timeout_s=30
        )
        
        return response 