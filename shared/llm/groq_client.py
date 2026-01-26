"""
Groq LLM Client
High-performance LLM client using Groq API
"""

import os
from typing import Optional, Dict, Any
from groq import Groq
from shared.config.logging_config import get_logger
from dotenv import load_dotenv
load_dotenv()


logger = get_logger(__name__)


class GroqClient:
    """
    Groq LLM client for financial document extraction
    
    Recommended models:
    - llama-3.3-70b-versatile: Best for complex extraction (RECOMMENDED)
    - llama-3.1-70b-versatile: Good balance of speed/accuracy
    - mixtral-8x7b-32768: Fast, good for structured data
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key (or set GROQ_API_KEY env var)
            model: Model to use (default: llama-3.3-70b-versatile)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Groq API key required. Set GROQ_API_KEY env var or pass api_key parameter. "
                "Get free key at: https://console.groq.com/keys"
            )
        
        self.model = model
        self.client = Groq(api_key=self.api_key)
        
        logger.info(f"Groq client initialized with model: {model}")
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        json_mode: bool = False
    ) -> str:
        """
        Generate completion from Groq
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0, lower = more deterministic)
            max_tokens: Maximum tokens to generate
            json_mode: Force JSON output format
            
        Returns:
            Generated text
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a financial document extraction AI. Extract data accurately and return valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Groq supports JSON mode for structured outputs
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**kwargs)
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise
    
    def extract_structured(
        self,
        document_text: str,
        schema_description: str,
        temperature: float = 0.1
    ) -> str:
        """
        Extract structured data from document text
        
        Args:
            document_text: Raw document text
            schema_description: Description of expected JSON schema
            temperature: Sampling temperature
            
        Returns:
            JSON string with extracted data
        """
        prompt = f"""Extract structured financial data from this document.

Document Text:
{document_text[:8000]}

Expected Output Schema:
{schema_description}

Extract all available fields. Return ONLY valid JSON, no explanation or markdown.
If a field is not found, set it to null.
For dates, use YYYY-MM-DD format.
For amounts, use numbers without currency symbols."""

        return self.generate(
            prompt=prompt,
            temperature=temperature,
            max_tokens=4096,
            json_mode=True  # Force JSON output
        )
    
    def validate_extraction(
        self,
        document_text: str,
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate extracted data against source document
        
        Args:
            document_text: Original document text
            extracted_data: Extracted structured data
            
        Returns:
            Validation results with confidence scores
        """
        import json
        
        prompt = f"""Validate this extracted data against the source document.

Source Document:
{document_text[:4000]}

Extracted Data:
{json.dumps(extracted_data, indent=2)}

For each field, assess:
1. Is the value correct? (yes/no)
2. Confidence score (0.0-1.0)
3. Any issues found

Return JSON:
{{
  "overall_confidence": 0.95,
  "field_validations": {{
    "document_number": {{"correct": true, "confidence": 0.98}},
    "grand_total": {{"correct": true, "confidence": 0.95}}
  }},
  "issues": ["list of any issues found"]
}}"""

        response = self.generate(prompt, temperature=0.1, json_mode=True)
        
        try:
            return json.loads(response)
        except:
            return {
                "overall_confidence": 0.5,
                "field_validations": {},
                "issues": ["Validation failed"]
            }


# Recommended model configurations for different use cases
GROQ_MODELS = {
    "accurate": "llama-3.3-70b-versatile",      # Best accuracy, slightly slower
    "balanced": "llama-3.1-70b-versatile",      # Good balance
    "fast": "mixtral-8x7b-32768",               # Fastest, good quality
    "default": "llama-3.3-70b-versatile"        # Recommended default
}


def get_groq_client(model_type: str = "default") -> GroqClient:
    """
    Factory function to get Groq client with recommended model
    
    Args:
        model_type: Model type (accurate, balanced, fast, default)
        
    Returns:
        Configured GroqClient
    """
    model = GROQ_MODELS.get(model_type, GROQ_MODELS["default"])
    return GroqClient(model=model)