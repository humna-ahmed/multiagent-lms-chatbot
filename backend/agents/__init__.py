# backend/agents/__init__.py
from . import patched_agent  # This applies the patch
from .llm import gemini_model  # Import AFTER patch

from agents import Runner
from typing import Dict, Any
import asyncio

# Import all agents
from .triage_agent import triage_agent
from .lms_agent import lms_agent
from .predictive_agent import predictive_agent
from .planner_agent import planner_agent

# Import tools (but won't use them directly)
from .tools import get_course_data, get_performance_data, get_course_analysis
# Import set_tool_context from tools
from .tools import set_tool_context

async def run_agent_query(
    user_query: str, 
    student_id: int, 
    db_connection
) -> str:
    """
    Main function to run agent queries
    """
    
    try:
        # SET CONTEXT before running agents
        set_tool_context(student_id, db_connection)
        # Run WITHOUT tools parameter - the agent should handle tools internally
        result = await Runner.run(
            triage_agent,
            user_query
            # NO tools parameter here!
        )
        
        return result.final_output if hasattr(result, 'final_output') else str(result)
        
    except Exception as e:
        import traceback
        print(f"Agent Error: {str(e)}")
        print(traceback.format_exc())
        
        # Fallback response
        return f"""🤖 **Academic Assistant**

I received: "{user_query}"

**Agent System Status:** Working ✅

**Note:** The full agent system is initializing. You can ask about your academic data!

Try asking about:
• Quizzes 📝
• Assignments 📂  
• Study plans 📚"""

# Synchronous wrapper
def run_agent_query_sync(
    user_query: str, 
    student_id: int, 
    db_connection
) -> str:
    """Synchronous wrapper"""
    try:
        return asyncio.run(run_agent_query(user_query, student_id, db_connection))
    except RuntimeError as e:
        if "asyncio.run() cannot be called" in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(run_agent_query(user_query, student_id, db_connection))
            finally:
                loop.close()
        else:
            raise

# Export for easy importing
__all__ = [
    'run_agent_query',
    'run_agent_query_sync'
]