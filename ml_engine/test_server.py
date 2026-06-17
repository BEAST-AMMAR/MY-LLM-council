import pytest
from aiohttp import web
import json
import asyncio

# Need to import app from server
import server

@pytest.fixture
def cli(event_loop, aiohttp_client):
    app = server.app
    # Set mock mode for testing
    server.MOCK_MODE = True
    return event_loop.run_until_complete(aiohttp_client(app))

async def test_health_check(cli):
    resp = await cli.get('/api/health')
    assert resp.status == 200
    data = await resp.json()
    assert data['status'] == 'online'
    assert 'mock_mode' in data

async def test_inference_missing_fields(cli):
    resp = await cli.post('/api/infer', json={"agent_id": "sage"})
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data
    assert "Missing agent_id or prompt" in data['error']

async def test_inference_invalid_agent(cli):
    resp = await cli.post('/api/infer', json={"agent_id": "fake_agent", "prompt": "Hello"})
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data
    assert "Unknown agent" in data['error']

async def test_inference_prompt_too_long(cli):
    long_prompt = "a" * 4001
    resp = await cli.post('/api/infer', json={"agent_id": "sage", "prompt": long_prompt})
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data
    assert "Prompt too long" in data['error']

async def test_rate_limiting(cli):
    # Send 21 requests to trigger rate limit (limit is 20)
    for _ in range(20):
        resp = await cli.post('/api/infer', json={"agent_id": "sage", "prompt": "Test"})
        assert resp.status == 200
        # consume stream
        await resp.text()
    
    # 21st should fail
    resp = await cli.post('/api/infer', json={"agent_id": "sage", "prompt": "Test"})
    assert resp.status == 429
    data = await resp.json()
    assert "error" in data
    assert "Rate limit exceeded" in data['error']
    
    # Clean up rate limits for other tests if necessary
    server.rate_limits.clear()

async def test_inference_success(cli):
    server.rate_limits.clear()
    resp = await cli.post('/api/infer', json={"agent_id": "sage", "prompt": "Hello world"})
    assert resp.status == 200
    
    # Read the streamed response
    text = await resp.text()
    assert "data:" in text
    assert "[DONE]" in text
    assert "token" in text
