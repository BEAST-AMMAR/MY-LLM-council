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

# Global callback variable to pass tokens back to server websocket
stream_callback = None

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
        media_text += "\n[LIVE AUDIO FEED]: " + " ".join(ctx["audio"][-3:]) # Last 3 transcriptions
    if ctx.get("video"):
        media_text += "\n[LIVE CAMERA STATUS]: User is on camera. (Vision processing active)"
    if ctx.get("files"):
        media_text += "\n[UPLOADED DOCUMENTS]:\n"
        for fname, fcontent in ctx["files"]:
            # Truncate content if it's base64 to avoid huge prompts, or just note it's there
            display_content = fcontent[:500] + "..." if len(fcontent) > 500 else fcontent
            media_text += f"--- {fname} ---\n{display_content}\n"
    return media_text
    
async def sage_node(state: DebateState):
    history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"]])
    media = get_media_prompt(state.get("session_id", ""))
    
    personality = state.get("personality", {"aggression": 50, "creativity": 50})
    agg_str = "highly aggressive and assertive" if personality["aggression"] > 70 else "calm and measured" if personality["aggression"] < 30 else "balanced"
    cre_str = "extremely creative and lateral-thinking" if personality["creativity"] > 70 else "highly analytical and literal" if personality["creativity"] < 30 else "focused"
    
    prompt = f"Topic: {state['current_topic']}\nHistory:\n{history}{media}\n\nProvide your philosophical insight. Your tone should be {agg_str} and {cre_str}."
    if stream_callback: await stream_callback("sage", "thinking", None)
    full_text = ""
    async for token in hybrid_adapter.ainvoke_stream("sage", prompt):
        if stream_callback: await stream_callback("sage", "token", token)
        full_text += token
    if stream_callback: await stream_callback("sage", "done", None)
    return {"messages": [AIMessage(content=full_text, name="sage")]}

async def archivist_node(state: DebateState):
    history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"][-2:]])
    query_prompt = f"Based on the following recent debate context, extract the most factual or contested 3-5 word search query to verify:\n{history}\n\nSearch Query:"
    if stream_callback: await stream_callback("archivist", "thinking", None)
    
    # Use the fastest/cheapest model to extract the query
    query = await hybrid_adapter.get_full_response("skeptic", query_prompt) # reuse skeptic model for query extraction
    query = query.strip(' "\'')[:40] # sanitize
    
    search_results = "No results found."
    try:
        ddgs = DDGS()
        results = ddgs.text(query, max_results=2)
        if results:
            search_results = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except Exception as e:
        search_results = f"Search failed: {e}"
        
    full_text = f"[ARCHIVIST FACT CHECK] Query: '{query}'\nResults:\n{search_results}"
    if stream_callback: await stream_callback("archivist", "token", full_text)
    if stream_callback: await stream_callback("archivist", "done", None)
    
    return {"messages": [AIMessage(content=full_text, name="archivist")]}

async def analyst_node(state: DebateState):
    history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"]])
    media = get_media_prompt(state.get("session_id", ""))
    
    personality = state.get("personality", {"aggression": 50, "creativity": 50})
    agg_str = "highly aggressive and assertive" if personality["aggression"] > 70 else "calm and measured" if personality["aggression"] < 30 else "balanced"
    cre_str = "extremely creative and lateral-thinking" if personality["creativity"] > 70 else "highly analytical and literal" if personality["creativity"] < 30 else "focused"
    
    prompt = f"Topic: {state['current_topic']}\nHistory:\n{history}{media}\n\nProvide your logical analysis. Your tone should be {agg_str} and {cre_str}."
    if stream_callback: await stream_callback("analyst", "thinking", None)
    full_text = ""
    async for token in hybrid_adapter.ainvoke_stream("analyst", prompt):
        if stream_callback: await stream_callback("analyst", "token", token)
        full_text += token
    if stream_callback: await stream_callback("analyst", "done", None)
    return {"messages": [AIMessage(content=full_text, name="analyst")]}

async def strategist_node(state: DebateState):
    history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"]])
    media = get_media_prompt(state.get("session_id", ""))
    
    personality = state.get("personality", {"aggression": 50, "creativity": 50})
    agg_str = "highly aggressive and assertive" if personality["aggression"] > 70 else "calm and measured" if personality["aggression"] < 30 else "balanced"
    cre_str = "extremely creative and lateral-thinking" if personality["creativity"] > 70 else "highly analytical and literal" if personality["creativity"] < 30 else "focused"
    
    prompt = f"Topic: {state['current_topic']}\nHistory:\n{history}{media}\n\nProvide your strategic vision. Your tone should be {agg_str} and {cre_str}."
    if stream_callback: await stream_callback("strategist", "thinking", None)
    full_text = ""
    async for token in hybrid_adapter.ainvoke_stream("strategist", prompt):
        if stream_callback: await stream_callback("strategist", "token", token)
        full_text += token
    if stream_callback: await stream_callback("strategist", "done", None)
    return {"messages": [AIMessage(content=full_text, name="strategist")]}

async def skeptic_node(state: DebateState):
    history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"]])
    media = get_media_prompt(state.get("session_id", ""))
    
    personality = state.get("personality", {"aggression": 50, "creativity": 50})
    agg_str = "highly aggressive and assertive" if personality["aggression"] > 70 else "calm and measured" if personality["aggression"] < 30 else "balanced"
    cre_str = "extremely creative and lateral-thinking" if personality["creativity"] > 70 else "highly analytical and literal" if personality["creativity"] < 30 else "focused"
    
    prompt = f"Topic: {state['current_topic']}\nHistory:\n{history}{media}\n\nChallenge the previous points. Your tone should be {agg_str} and {cre_str}."
    if stream_callback: await stream_callback("skeptic", "thinking", None)
    full_text = ""
    async for token in hybrid_adapter.ainvoke_stream("skeptic", prompt):
        if stream_callback: await stream_callback("skeptic", "token", token)
        full_text += token
    if stream_callback: await stream_callback("skeptic", "done", None)
    return {"messages": [AIMessage(content=full_text, name="skeptic")]}

async def judge_node(state: DebateState):
    history = "\n".join([f"{m.name if hasattr(m, 'name') else 'User'}: {m.content}" for m in state["messages"]])
    media = get_media_prompt(state.get("session_id", ""))
    prompt = f"Topic: {state['current_topic']}\nHistory:\n{history}{media}\n\nDeliver your final verdict based on the debate."
    if stream_callback: await stream_callback("judge", "thinking", None)
    full_text = ""
    async for token in hybrid_adapter.ainvoke_stream("judge", prompt):
        if stream_callback: await stream_callback("judge", "token", token)
        full_text += token
    if stream_callback: await stream_callback("judge", "done", None)
    return {"messages": [AIMessage(content=full_text, name="judge")]}

def should_continue(state: DebateState):
    if state["round_count"] >= state["max_rounds"]:
        return "judge"
    return "crossfire"

# Build the Graph
workflow = StateGraph(DebateState)

# Add nodes
workflow.add_node("archivist", archivist_node)
workflow.add_node("sage", sage_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("strategist", strategist_node)
workflow.add_node("skeptic", skeptic_node)
workflow.add_node("judge", judge_node)

# We define a dummy node for crossfire to increment round and loop
async def increment_round(state: DebateState):
    return {"round_count": state["round_count"] + 1}
workflow.add_node("crossfire", increment_round)

# Edges
# After user prompt, all 4 agents speak, plus archivist
workflow.set_entry_point("archivist")
workflow.add_edge("archivist", "sage")
workflow.add_edge("sage", "analyst")
workflow.add_edge("analyst", "strategist")
workflow.add_edge("strategist", "skeptic")

# After skeptic, we check if we should continue crossfire or go to judge
workflow.add_conditional_edges("skeptic", should_continue, {
    "crossfire": "crossfire",
    "judge": "judge"
})

# Crossfire loops back to sage
workflow.add_edge("crossfire", "sage")

# Judge ends it
workflow.add_edge("judge", END)

debate_app = workflow.compile()
