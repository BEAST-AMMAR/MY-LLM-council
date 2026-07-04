import asyncio
from adapter import hybrid_adapter

async def main():
    print('Testing sage...')
    res = await hybrid_adapter.get_full_response('sage', 'hello')
    print('Sage:', res)
    print('Testing archivist (skeptic)...')
    res2 = await hybrid_adapter.get_full_response('skeptic', 'hello')
    print('Skeptic:', res2)

if __name__ == '__main__':
    asyncio.run(main())
