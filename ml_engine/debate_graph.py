import operator
from typing import Annotated, TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from adapter import hybrid_adapter
import asyncio
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from rag_utils import get_precedents, parse_base64_file

# Per-session callback dict: session_id -> callback coroutine
# This replaces the old global stream_callback to prevent race conditions
# when multiple debates run concurrently.
stream_callbacks = {}
live_media_context = {}

class DebateState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    round_count: int
    max_rounds: int
    current_topic: str
    session_id: str
    personality: dict

def get_media_prompt(session_id: str) -> str:
    ctx = live_media_context.get(session_id, {"audio": [], "video": None, "files": []})
    media_text = ""
    if ctx.get("audio"):
        media_text += "\n[LIVE AUDIO FEED]: " + " ".join(ctx["audio"][-3:])
    if ctx.get("video"):
        media_text += "\n[LIVE CAMERA STATUS]: User is on camera. (Vision processing active)"
    if ctx.get("files"):
        media_text += "\n[UPLOADED DOCUMENTS]:\n"
        for fname, fcontent in ctx["files"]:
            # Use RAG utility to parse the base64 content
            parsed_text = parse_base64_file(fname, fcontent)
            display_content = parsed_text[:2000] + "..." if len(parsed_text) > 2000 else parsed_text
            media_text += f"--- {fname} ---\n{display_content}\n"
    return media_text

def _get_callback(session_id: str):
    """Get the stream callback for a given session, or None."""
    return stream_callbacks.get(session_id)

def create_dynamic_agent_node(agent_name: str, system_prompt: str, model_id: str, provider: str):
    node_name = agent_name.lower().replace(" ", "_")
    async def dynamic_agent_node(state: DebateState):
        session_id = state.get("session_id", "")
        cb = _get_callback(session_id)
        history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"]])
        media = get_media_prompt(session_id)
        
        personality = state.get("personality", {"aggression": 50, "creativity": 50})
        agg_str = "highly aggressive and assertive" if personality["aggression"] > 70 else "calm and measured" if personality["aggression"] < 30 else "balanced"
        cre_str = "extremely creative and lateral-thinking" if personality["creativity"] > 70 else "highly analytical and literal" if personality["creativity"] < 30 else "focused"
        
        prompt = f"Topic: {state['current_topic']}\nHistory:\n{history}{media}\n\nYour tone should be {agg_str} and {cre_str}."
        if cb: await cb(node_name, "thinking", None)
        
        full_text = ""
        async for token in hybrid_adapter.ainvoke_custom_agent_stream(agent_name, model_id, provider, system_prompt, prompt):
            if cb: await cb(node_name, "token", token)
            full_text += token
        if cb: await cb(node_name, "done", None)
        return {"messages": [AIMessage(content=full_text, name=node_name)]}
    return dynamic_agent_node

# Default agents (fallback if no custom agents)
async def default_sage_node(state: DebateState):
    session_id = state.get("session_id", "")
    cb = _get_callback(session_id)
    history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"]])
    prompt = f"Topic: {state['current_topic']}\nHistory:\n{history}{get_media_prompt(session_id)}\n\nProvide your philosophical insight."
    if cb: await cb("sage", "thinking", None)
    full_text = ""
    async for token in hybrid_adapter.ainvoke_stream("sage", prompt):
        if cb: await cb("sage", "token", token)
        full_text += token
    if cb: await cb("sage", "done", None)
    return {"messages": [AIMessage(content=full_text, name="sage")]}

async def default_analyst_node(state: DebateState):
    session_id = state.get("session_id", "")
    cb = _get_callback(session_id)
    history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"]])
    prompt = f"Topic: {state['current_topic']}\nHistory:\n{history}{get_media_prompt(session_id)}\n\nProvide your logical analysis."
    if cb: await cb("analyst", "thinking", None)
    full_text = ""
    async for token in hybrid_adapter.ainvoke_stream("analyst", prompt):
        if cb: await cb("analyst", "token", token)
        full_text += token
    if cb: await cb("analyst", "done", None)
    return {"messages": [AIMessage(content=full_text, name="analyst")]}

async def default_strategist_node(state: DebateState):
    session_id = state.get("session_id", "")
    cb = _get_callback(session_id)
    history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"]])
    prompt = f"Topic: {state['current_topic']}\nHistory:\n{history}{get_media_prompt(session_id)}\n\nProvide your strategic vision."
    if cb: await cb("strategist", "thinking", None)
    full_text = ""
    async for token in hybrid_adapter.ainvoke_stream("strategist", prompt):
        if cb: await cb("strategist", "token", token)
        full_text += token
    if cb: await cb("strategist", "done", None)
    return {"messages": [AIMessage(content=full_text, name="strategist")]}

async def default_skeptic_node(state: DebateState):
    session_id = state.get("session_id", "")
    cb = _get_callback(session_id)
    history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"]])
    prompt = f"Topic: {state['current_topic']}\nHistory:\n{history}{get_media_prompt(session_id)}\n\nChallenge the previous points."
    if cb: await cb("skeptic", "thinking", None)
    full_text = ""
    async for token in hybrid_adapter.ainvoke_stream("skeptic", prompt):
        if cb: await cb("skeptic", "token", token)
        full_text += token
    if cb: await cb("skeptic", "done", None)
    return {"messages": [AIMessage(content=full_text, name="skeptic")]}

async def archivist_node(state: DebateState):
    session_id = state.get("session_id", "")
    cb = _get_callback(session_id)
    history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"][-2:]])
    query_prompt = f"Based on the following recent debate context, extract the most factual or contested 3-5 word search query to verify:\n{history}\n\nSearch Query:"
    if cb: await cb("archivist", "thinking", None)
    
    query = await hybrid_adapter.get_full_response("skeptic", query_prompt)
    query = query.strip(' "\'')[:40]
    
    import os
    search_results = "No results found."
    ddg_success = False
    
    # Primary Search: DuckDuckGo
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        def do_ddg_search():
            try:
                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=2))
            except AttributeError:
                ddgs = DDGS()
                return list(ddgs.text(query, max_results=2))

        import asyncio
        results = await asyncio.to_thread(do_ddg_search)
        if results:
            search_results = "\n".join([f"- {r.get('title', '')}: {r.get('body', '')}" for r in results])
            ddg_success = True
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}. Falling back to Tavily...")
        
    # Fallback Search: Tavily
    if not ddg_success:
        tavily_key = os.environ.get("TAVILY_API_KEY")
        if tavily_key:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.tavily.com/search",
                        json={"api_key": tavily_key, "query": query, "search_depth": "basic", "include_answer": False},
                        timeout=10.0
                    )
                    response.raise_for_status()
                    data = response.json()
                    results = data.get("results", [])
                    if results:
                        search_results = "\n".join([f"- {r['title']}: {r.get('content', '')}" for r in results[:2]])
                    else:
                        search_results = "Tavily search returned no results."
            except Exception as e:
                search_results = f"Search failed (both DDG and Tavily): {e}"
        else:
            search_results = "Search failed: DuckDuckGo failed and TAVILY_API_KEY is not set in environment."
        
    full_text = f"[ARCHIVIST FACT CHECK] Query: '{query}'\nResults:\n{search_results}"
    if cb: await cb("archivist", "token", full_text)
    if cb: await cb("archivist", "done", None)
    return {"messages": [AIMessage(content=full_text, name="archivist")]}

async def judge_node(state: DebateState):
    session_id = state.get("session_id", "")
    cb = _get_callback(session_id)
    history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"]])
    
    # Retrieve precedents for Long-Term Memory
    precedents = get_precedents(state['current_topic'])
    
    prompt = f"Topic: {state['current_topic']}{precedents}\nHistory:\n{history}{get_media_prompt(session_id)}\n\nDeliver your final verdict based on the debate."
    if cb: await cb("judge", "thinking", None)
    full_text = ""
    async for token in hybrid_adapter.ainvoke_stream("judge", prompt):
        if cb: await cb("judge", "token", token)
        full_text += token
    if cb: await cb("judge", "done", None)
    return {"messages": [AIMessage(content=full_text, name="judge")]}

async def increment_round(state: DebateState):
    return {"round_count": state["round_count"] + 1}

def build_graph(custom_agents=None):
    workflow = StateGraph(DebateState)
    
    workflow.add_node("archivist", archivist_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("crossfire", increment_round)
    
    if custom_agents and len(custom_agents) > 0:
        agent_names = []
        for ag in custom_agents:
            node_name = ag.name.lower().replace(" ", "_")
            workflow.add_node(node_name, create_dynamic_agent_node(ag.name, ag.system_prompt, ag.model, ag.provider))
            agent_names.append(node_name)
            
        workflow.set_entry_point("archivist")
        workflow.add_edge("archivist", agent_names[0])
        for i in range(len(agent_names) - 1):
            workflow.add_edge(agent_names[i], agent_names[i+1])
            
        last_agent = agent_names[-1]
        workflow.add_conditional_edges(last_agent, should_continue, {"crossfire": "crossfire", "judge": "judge"})
        workflow.add_edge("crossfire", agent_names[0])
        workflow.add_edge("judge", END)
        
    else:
        # Default fallback
        workflow.add_node("sage", default_sage_node)
        workflow.add_node("analyst", default_analyst_node)
        workflow.add_node("strategist", default_strategist_node)
        workflow.add_node("skeptic", default_skeptic_node)
        
        workflow.set_entry_point("archivist")
        workflow.add_edge("archivist", "sage")
        workflow.add_edge("sage", "analyst")
        workflow.add_edge("analyst", "strategist")
        workflow.add_edge("strategist", "skeptic")
        
        workflow.add_conditional_edges("skeptic", should_continue, {"crossfire": "crossfire", "judge": "judge"})
        workflow.add_edge("crossfire", "sage")
        workflow.add_edge("judge", END)
        
    return workflow.compile()

def should_continue(state: DebateState):
    """Routing logic: continue debating or go to judge.
    Exposed at module level for testability."""
    if state["round_count"] >= state["max_rounds"]:
        return "judge"
    return "crossfire"

# Provide a default graph for legacy imports if needed
debate_app = build_graph()
