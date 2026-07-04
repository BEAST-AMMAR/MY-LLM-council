import asyncio
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

def do_search(query):
    try:
        # Some older versions don't support context manager for DDGS
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=2)
            return list(results) if results else []
    except AttributeError:
        ddgs = DDGS()
        results = ddgs.text(query, max_results=2)
        return list(results) if results else []

async def main():
    results = await asyncio.to_thread(do_search, 'python')
    print('Results:', results)

if __name__ == '__main__':
    asyncio.run(main())
