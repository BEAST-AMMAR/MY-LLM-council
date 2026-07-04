import asyncio
from debate_graph import archivist_node
from langchain_core.messages import HumanMessage
import os

async def main():
    state = {
        'messages': [HumanMessage(content='What is the capital of France?', name='user')],
        'session_id': 'test'
    }
    print('Testing archivist node...')
    result = await archivist_node(state)
    print('\n--- Result ---')
    print(result['messages'][0].content)

if __name__ == '__main__':
    asyncio.run(main())
