# backend/agents/llm.py

import os
from typing import AsyncIterator, Dict, Any
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import ModelSettings

load_dotenv()

class GeminiModelSettings(ModelSettings):
    """Gemini model settings for OpenAI Agent SDK"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY missing")
        
        self.model = "gemini-2.5-flash"
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
    
    async def create_chat_completion(
        self, 
        messages, 
        stream: bool = False, 
        **kwargs
    ) -> AsyncIterator:
        """Create chat completion with Gemini"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=stream,
            **kwargs
        )
        
        if stream:
            async for chunk in response:
                yield chunk
        else:
            yield response
    
    def __str__(self):
        return self.model

# Create a global instance
gemini_model = GeminiModelSettings()

# ============================================
# PATCH: Monkey patch the Agent SDK to accept custom models
# ============================================
import agents.agent

# Save the original __post_init__ method
original_post_init = agents.agent.Agent.__post_init__

def patched_post_init(self):
    """Patched version that accepts custom ModelSettings"""
    # Check if model is a ModelSettings instance
    if hasattr(self.model, 'create_chat_completion'):
        # It's a custom model, accept it
        pass
    else:
        # Use original validation
        original_post_init(self)

# Apply the patch
agents.agent.Agent.__post_init__ = patched_post_init
print("✅ Patched Agent SDK to accept custom models")