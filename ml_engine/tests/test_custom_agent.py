import asyncio
from adapter import hybrid_adapter
from langchain_core.messages import AIMessage

async def main():
    print('Testing custom agent...')
    async for token in hybrid_adapter.ainvoke_custom_agent_stream('test_agent', 'google/gemma-4-31b-it:free', 'openrouter', 'You are a test agent.', 'Say hello'):
        print(token, end='', flush=True)

if __name__ == '__main__':
    asyncio.run(main())
