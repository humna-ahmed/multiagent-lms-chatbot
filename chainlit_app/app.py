import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import chainlit as cl
from backend.agents.triage_agent import triage

@cl.on_message
async def main(message):
    student_id = 1  # demo
    response = triage(message.content, student_id)
    await cl.Message(content=response).send()
