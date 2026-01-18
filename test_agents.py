# test_agents.py

import asyncio
from agents import Runner
from agents.triage_agent import triage_agent

async def main():
    result = await Runner.run(
        triage_agent,
        input="Predict my final exam marks for Functional English"
    )
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
