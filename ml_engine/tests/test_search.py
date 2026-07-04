import asyncio
try:
    from ddgs import AsyncDDGS
except ImportError:
    from duckduckgo_search import AsyncDDGS

async def main():
    try:
        async with AsyncDDGS() as ddgs:
            results = await ddgs.text('python', max_results=2)
            print('Results:', results)
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    asyncio.run(main())
