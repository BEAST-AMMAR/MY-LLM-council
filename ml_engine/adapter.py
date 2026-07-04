import os
import json
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv() # Load the .env file

try:
    from llama_cpp import Llama
    HAS_LLAMA = True
except ImportError:
    HAS_LLAMA = False

# OpenRouter Config
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

class HybridLLMAdapter:
    def __init__(self):
        self.mode = "cloud" # Default to cloud if key exists
        self.local_models = {}
        
        # Cloud models mapping with FALLBACKS (List of models per role)
        # Using good free models on OpenRouter
        self.cloud_models = {
            "sage": [
                "google/gemma-4-31b-it:free",
                "nvidia/nemotron-3-super-120b-a12b:free"
            ],
            "analyst": [
                "qwen/qwen3-coder:free",
                "nvidia/nemotron-nano-12b-v2-vl:free"
            ],
            "strategist": [
                "openai/gpt-oss-120b:free",
                "google/gemma-4-26b-a4b-it:free"
            ],
            "skeptic": [
                "nvidia/nemotron-3-ultra-550b-a55b:free",
                "openai/gpt-oss-20b:free"
            ],
            "judge": [
                "meta-llama/llama-3.3-70b-instruct:free",
                "cohere/north-mini-code:free"
            ]
        }
        
        # Local models mapping
        self.local_model_files = {
            "sage": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
            "analyst": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
            "strategist": "Phi-3-mini-4k-instruct-q4.gguf",
            "skeptic": "gemma-2-2b-it-Q4_K_M.gguf",
            "judge": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        }
        
        self.cloud_clients = {}
        self._init_cloud_clients()

    def set_mode(self, mode: str):
        if mode in ["local", "cloud"]:
            self.mode = mode
            print(f"[ADAPTER] Switched to {mode.upper()} mode")

    def _init_cloud_clients(self):
        if not OPENROUTER_API_KEY:
            print("[ADAPTER] No OPENROUTER_API_KEY found. Falling back to local/mock.")
            self.mode = "local"
            return
            
        self.cloud_clients = {}
        # Pre-initialize a client for every model in the fallback chain for speed
        for agent, model_list in self.cloud_models.items():
            self.cloud_clients[agent] = []
            for model_id in model_list:
                client = ChatOpenAI(
                    model=model_id,
                    api_key=OPENROUTER_API_KEY,
                    base_url=OPENROUTER_BASE_URL,
                    max_retries=0, # Disable langchain retries to handle fallbacks manually
                    request_timeout=60,
                    streaming=True
                )
                self.cloud_clients[agent].append(client)

    def load_local_models(self, models_dir):
        if not HAS_LLAMA:
            print("[ADAPTER] llama-cpp-python not installed. Cannot load local models.")
            return
            
        for agent_id, filename in self.local_model_files.items():
            path = os.path.join(models_dir, filename)
            if os.path.exists(path):
                print(f"Loading local {agent_id} ({filename})...")
                try:
                    self.local_models[agent_id] = Llama(model_path=path, n_ctx=2048, verbose=False)
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")

    async def ainvoke_stream(self, agent_id: str, prompt: str):
        """Async generator that streams tokens back, with robust fallback logic"""
        
        if self.mode == "cloud" and OPENROUTER_API_KEY:
            clients = self.cloud_clients.get(agent_id, [])
            if not clients:
                yield f"[Error] Cloud clients for {agent_id} not found."
                return
                
            messages = [
                SystemMessage(content=f"You are the {agent_id.capitalize()} of the LLM Council. Analyze the user's prompt deeply."),
                HumanMessage(content=prompt)
            ]
            
            last_error = None
            success = False
            
            # Iterate through the fallback chain
            MAX_RETRIES_PER_MODEL = 3
            
            for index, client in enumerate(clients):
                model_success = False
                
                for attempt in range(MAX_RETRIES_PER_MODEL):
                    try:
                        # Notify UI if we are using a fallback
                        if index > 0 and attempt == 0:
                            yield f"\n\n[Falling back to {self.cloud_models[agent_id][index]}]\n\n"
                        elif attempt > 0:
                            # Silently retry or print to console instead of spamming UI
                            print(f"[ADAPTER] Retrying {self.cloud_models[agent_id][index]} (Attempt {attempt+1}/{MAX_RETRIES_PER_MODEL})...")
                            
                        async for chunk in client.astream(messages):
                            if chunk.content:
                                yield chunk.content
                        
                        model_success = True
                        break # Break out of attempt loop
                        
                    except Exception as e:
                        print(f"[ADAPTER] Error with model {self.cloud_models[agent_id][index]} for agent {agent_id} (Attempt {attempt+1}): {e}")
                        last_error = e
                        await asyncio.sleep(2 * (attempt + 1)) # Exponential backoff
                        continue # Try again
                
                if model_success:
                    success = True
                    break # Break out of fallback loop
            
            if not success:
                yield f"\n\n[System Error: All API models failed for {agent_id} after retries. Last Reason: {last_error}]\n\n"
                    
        else:
            # Local Mode or Mock Mode
            if agent_id in self.local_models:
                llm = self.local_models[agent_id]
                # Run sync generator in thread
                stream = await asyncio.to_thread(llm, prompt, max_tokens=300, stream=True)
                for chunk in stream:
                    token = chunk["choices"][0]["text"]
                    if token:
                        yield token
                        await asyncio.sleep(0.01)
            else:
                # Mock Mode fallback
                yield f"[MOCK {agent_id.upper()}] Local model not loaded. Analyzing prompt: {prompt[:30]}..."
                
    async def get_full_response(self, agent_id: str, prompt: str) -> str:
        """Helper to get a full non-streaming response"""
        full_text = ""
        async for token in self.ainvoke_stream(agent_id, prompt):
            full_text += token
        return full_text

    async def ainvoke_custom_agent_stream(self, agent_name: str, model_id: str, provider: str, system_prompt: str, prompt: str):
        """Async generator for dynamically defined custom agents"""
        if provider == "openrouter" and OPENROUTER_API_KEY:
            client = ChatOpenAI(
                model=model_id,
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                max_retries=0,
                request_timeout=60,
                streaming=True
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
            MAX_RETRIES = 3
            last_error = None
            for attempt in range(MAX_RETRIES):
                try:
                    if attempt > 0:
                        print(f"[ADAPTER] Retrying custom agent '{agent_name}' with model '{model_id}' (Attempt {attempt+1}/{MAX_RETRIES})...")
                    async for chunk in client.astream(messages):
                        if chunk.content:
                            yield chunk.content
                    return # Exit generator on success
                except Exception as e:
                    print(f"[ADAPTER] Error with custom agent {agent_name} (Attempt {attempt+1}): {e}")
                    last_error = e
                    await asyncio.sleep(2 * (attempt + 1))
            
            yield f"\n\n[System Error: Custom agent '{agent_name}' with model '{model_id}' failed after retries. Last Reason: {last_error}]\n\n"
        else:
            # Handle local or fallback mock
            yield f"[MOCK {agent_name.upper()}] Model: {model_id}. Local execution for custom agents not fully configured. Processing prompt..."

# Singleton instance
hybrid_adapter = HybridLLMAdapter()
