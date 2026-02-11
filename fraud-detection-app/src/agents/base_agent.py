import json
from urllib import request, error

class BaseAgent:
    def __init__(self, config):
        self.config = config
        self.llm_config = config['llm']
        self.api_key = self.llm_config.get("api_key")
        self.api_url = self.llm_config.get("api_url")

    def _call_llm(self, prompt, system_instruction=None):
        """Helper to call the Gemini API."""
        if not self.api_key or self.api_key == "PASTE_YOUR_API_KEY_HERE":
            return "ERROR: Gemini API key not found or not set in config.yaml."

        final_url = f"{self.api_url}?key={self.api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        import time
        
        max_retries = 3
        retry_delay = 5  # Start with 5 seconds for rate limits

        for attempt in range(max_retries + 1):
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
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff: 5s, 10s, 20s
                        print(f"⚠️ Rate limit hit (429). Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
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

    def run(self, *args, **kwargs):
        """Main entry point for the agent. Must be implemented by subclasses."""
        raise NotImplementedError
