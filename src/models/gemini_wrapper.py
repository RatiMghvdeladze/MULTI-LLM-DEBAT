try:
    from google import genai
    NEW_API = True
except ImportError:
    import google.generativeai as genai
    NEW_API = False

from typing import Dict, Any, Optional
import time
from config.settings import GEMINI_API_KEY, GEMINI_MODEL


class GeminiWrapper:
    """Wrapper for Gemini API with retry logic and error handling"""
    
    def __init__(self):
        if NEW_API:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.model_name = GEMINI_MODEL
        else:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel(GEMINI_MODEL)
        
    def _wait_if_needed(self):
        """Wait if we're approaching rate limit"""
        now = datetime.now()
        
        # Remove requests older than 1 minute
        self.request_times = [
            t for t in self.request_times 
            if now - t < timedelta(minutes=1)
        ]
        
        # If we're at limit, wait until oldest request expires
        if len(self.request_times) >= self.max_requests_per_minute:
            oldest = self.request_times[0]
            wait_until = oldest + timedelta(minutes=1)
            wait_seconds = (wait_until - now).total_seconds() + 1
            
            if wait_seconds > 0:
                print(f"⏳ Rate limit protection: waiting {wait_seconds:.1f}s...")
                time.sleep(wait_seconds)
                self.request_times = []
        
        # Also enforce minimum delay between requests
        if self.request_times:
            time_since_last = (now - self.request_times[-1]).total_seconds()
            if time_since_last < self.min_delay_between_requests:
                wait = self.min_delay_between_requests - time_since_last
                print(f"⏳ Spacing requests: waiting {wait:.1f}s...")
                time.sleep(wait)
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_retries: int = 3
    ) -> str:
        """
        Generate response from Gemini with retry logic
        
        Args:
            prompt: User prompt
            system_prompt: System instruction (prepended to prompt)
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            max_retries: Number of retry attempts
            
        Returns:
            Generated text response
        """
        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        for attempt in range(max_retries):
            try:
                if NEW_API:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=full_prompt,
                        config={
                            "temperature": temperature,
                            "top_p": top_p,
                        }
                    )
                    return response.text
                else:
                    generation_config = genai.GenerationConfig(
                        temperature=temperature,
                        top_p=top_p,
                    )
                    response = self.model.generate_content(
                        full_prompt,
                        generation_config=generation_config
                    )
                    return response.text
            
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Failed after {max_retries} attempts: {e}")
    
    def generate_with_config(self, prompt: str, config: Dict[str, Any]) -> str:
        """Generate response using a configuration dictionary"""
        return self.generate(
            prompt=prompt,
            system_prompt=config.get("system_prompt"),
            temperature=config.get("temperature", 0.7),
            top_p=config.get("top_p", 0.9)
        )