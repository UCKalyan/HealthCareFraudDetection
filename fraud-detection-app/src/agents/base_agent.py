import json
from urllib import request, error
import httpx
import asyncio

class BaseAgent:
    def __init__(self, config):
        self.config = config
        self.llm_config = config['llm']
        self.provider = self.llm_config.get("provider", "gemini")  # gemini, ollama, or mlx
        
        # Gemini config
        self.api_key = self.llm_config.get("api_key")
        self.api_url = self.llm_config.get("api_url")
        
        # Ollama config
        self.ollama_config = self.llm_config.get("ollama", {})
        self.ollama_url = self.ollama_config.get("base_url", "http://localhost:11434")
        self.ollama_model = self.ollama_config.get("model", "llama3")
        
        # MLX config (Apple Silicon optimized)
        self.mlx_config = self.llm_config.get("mlx", {})
        self.mlx_model = self.mlx_config.get("model", "llama3")
        self.mlx_model_mappings = self.mlx_config.get("model_mappings", {
            "llama3": "mlx-community/Meta-Llama-3-8B-Instruct-4bit",
            "mistral": "mlx-community/Mistral-7B-Instruct-v0.2-4bit",
            "gemma": "mlx-community/gemma-7b-it-4bit",
            "phi": "mlx-community/phi-2-4bit"
        })
        self.mlx_max_tokens = self.mlx_config.get("max_tokens", 2048)
        self.mlx_temperature = self.mlx_config.get("temperature", 0.7)
        
        # MLX model cache (lazy loading)
        self._mlx_model = None
        self._mlx_tokenizer = None

    def _call_llm(self, prompt, system_instruction=None):
        """
        Call LLM based on configured provider.
        Supports: gemini (cloud), ollama (local), mlx (Apple Silicon optimized)
        """
        if self.provider == "mlx":
            return self._call_mlx(prompt, system_instruction)
        elif self.provider == "ollama":
            return self._call_ollama(prompt, system_instruction)
        else:
            return self._call_gemini(prompt, system_instruction)

    def _call_gemini(self, prompt, system_instruction=None):
        """Call Gemini API."""
        print(self.api_key)
        if not self.api_key or self.api_key == "PASTE_YOUR_API_KEY_HERE":
            return "ERROR: Gemini API key not found or not set in config.yaml."

        final_url = f"{self.api_url}?key={self.api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        import time
        
        max_retries = 1
        retry_delay = 1

        for attempt in range(max_retries + 1):
            print(final_url)
            try:
                req = request.Request(
                    final_url, 
                    method="POST", 
                    headers={"Content-Type": "application/json"}, 
                    data=json.dumps(payload).encode("utf-8")
                )
                with request.urlopen(req) as response:
                    if response.status == 200:
                        result = json.loads(response.read().decode())
                        print(result)
                        return result['candidates'][0]['content']['parts'][0]['text']
                    else:
                        return f"Error from Gemini API: {response.status} - {response.read().decode()}"
            
            except error.HTTPError as e:
                if e.code == 429:
                    if attempt < max_retries:
                        #wait_time = retry_delay * (2 ** attempt)
                        wait_time = retry_delay 
                        print(f"⚠️ Rate limit hit (429). Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Fallback to Ollama if configured
                        if self.ollama_config:
                            print("❌ Gemini rate limit exceeded. Falling back to Ollama...")
                            return self._call_ollama(prompt, system_instruction)
                        
                        error_msg = f"Error: Rate limit exceeded after {max_retries} retries. Please wait a few minutes and try again."
                        print(f"❌ {error_msg}")
                        return error_msg
                else:
                    error_msg = f"HTTP Error during LLM call: {e.code} - {e.reason}"
                    print(f"❌ {error_msg}")
                    return error_msg
            except Exception as e:
                error_msg = f"An unexpected error occurred during the LLM call: {e}"
                print(f"❌ {error_msg}")
                return error_msg

    def _call_ollama(self, prompt, system_instruction=None):
        """Call Ollama API (local LLM)."""
        url = f"{self.ollama_url}/api/generate"
        
        # Combine system instruction with prompt
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"
        
        payload = {
            "model": self.ollama_model,
            "prompt": full_prompt,
            "stream": False
        }
        
        try:
            # Use httpx for sync call (agents are sync)
            import httpx
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload)
                
            if response.status_code != 200:
                return f"Ollama Error: {response.text}. Is Ollama running? Start with: ollama serve"
            
            data = response.json()
            return data.get('response', '')
            
        except Exception as e:
            error_msg = f"Error connecting to Ollama: {e}. Make sure Ollama is running: ollama serve"
            print(f"❌ {error_msg}")
            return error_msg
    
    def _call_mlx(self, prompt, system_instruction=None):
        """
        Call MLX-LM directly (optimized for Apple Silicon M2/M3).
        Uses Apple's MLX framework for best performance on Mac.
        """
        try:
            # Lazy import and model loading
            if self._mlx_model is None:
                try:
                    from mlx_lm import load, generate
                    
                    # Get model path from mappings
                    model_path = self.mlx_model_mappings.get(
                        self.mlx_model, 
                        self.mlx_model_mappings["llama3"]
                    )
                    
                    print(f"🚀 Loading MLX model: {model_path} (first run may take a moment)...")
                    self._mlx_model, self._mlx_tokenizer = load(model_path)
                    print(f"✅ MLX model loaded successfully on Apple Silicon")
                    
                except ImportError:
                    error_msg = (
                        "MLX not installed. Install with: pip install mlx-lm\n"
                        "MLX requires Apple Silicon (M1/M2/M3) and macOS 13.3+\n"
                        "Falling back to Ollama if available..."
                    )
                    print(f"❌ {error_msg}")
                    if self.ollama_config:
                        return self._call_ollama(prompt, system_instruction)
                    return error_msg
            
            # Import generate function
            from mlx_lm import generate
            
            # Format prompt with system instruction
            full_prompt = prompt
            if system_instruction:
                # Use Llama 3 chat format
                full_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_instruction}<|eot_id|><|start_header_id|>user<|end_header_id|>

{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
            else:
                full_prompt = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>

{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
            
            # Generate response using MLX (runs on Apple Neural Engine + GPU)
            response = generate(
                self._mlx_model,
                self._mlx_tokenizer,
                prompt=full_prompt,
                max_tokens=self.mlx_max_tokens,
                temp=self.mlx_temperature,
                verbose=False
            )
            
            return response
            
        except Exception as e:
            error_msg = f"MLX Error: {e}"
            print(f"❌ {error_msg}")
            # Fallback to Ollama if available
            if self.ollama_config:
                print("📡 Falling back to Ollama...")
                return self._call_ollama(prompt, system_instruction)
            return error_msg

    def run(self, *args, **kwargs):
        """Main entry point for the agent. Must be implemented by subclasses."""
        raise NotImplementedError
