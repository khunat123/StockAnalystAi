"""
Base Agent - Foundation class for all AI agents
Handles LLM communication with Gemini or OpenAI
"""

from openai import OpenAI
import google.generativeai as genai
import traceback

from src.config import OPENAI_API_KEY, GEMINI_API_KEY, LLM_PROVIDER


class BaseAgent:
    """Base class for all AI agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.provider = LLM_PROVIDER
        
        if self.provider == "gemini":
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            if not OPENAI_API_KEY:
                print(f"[{self.name}] WARNING: OPENAI_API_KEY not found. Agent may fail.")
            self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call the LLM with system and user prompts
        
        Args:
            system_prompt: Instructions for the AI
            user_prompt: The actual query/data
            
        Returns:
            LLM response text
        """
        try:
            if self.provider == "gemini":
                full_prompt = f"System: {system_prompt}\nUser: {user_prompt}"
                response = self.model.generate_content(full_prompt)
                return response.text
            else:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7
                )
                return response.choices[0].message.content
        except Exception as e:
            self.log(f"Error calling LLM: {e}")
            self.log(f"Traceback: {traceback.format_exc()}")
            return "Error generating response."
    
    def analyze(self, ticker: str) -> dict:
        """Override in subclasses"""
        raise NotImplementedError("Subclasses must implement analyze method")
    
    def log(self, message: str):
        """Log a message with agent name prefix"""
        print(f"[{self.name}] {message}")
