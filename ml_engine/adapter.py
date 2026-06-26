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
            for index, client in enumerate(clients):
                try:
                    # Notify UI if we are using a fallback
                    if index > 0:
                        yield f" [Falling back to {self.cloud_models[agent_id][index]}] "
                        
                    async for chunk in client.astream(messages):
                        if chunk.content:
                            yield chunk.content
                    
                    success = True
                    break # Break out of fallback loop if successful
                    
                except Exception as e:
                    print(f"[ADAPTER] Error with model {self.cloud_models[agent_id][index]} for agent {agent_id}: {e}")
                    last_error = e
                    continue # Try next model
            
            if not success:
                yield f"\n[System Error: All API models failed for {agent_id}. Reason: {last_error}]"
                    
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

# Singleton instance
hybrid_adapter = HybridLLMAdapter()
