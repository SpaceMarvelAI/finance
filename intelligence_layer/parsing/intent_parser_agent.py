"""
Intent Parser Agent
Uses LLM to understand natural language queries
"""

from typing import Dict, Any, Optional
from processing_layer.agents.core.base_agent import BaseAgent, register_agent
from shared.config.logging_config import get_logger
import json
import re


logger = get_logger(__name__)


@register_agent
class IntentParserAgent(BaseAgent):
    """
    Intent Parser Agent
    
    Parses natural language queries into structured intents
    Uses LLM for accurate understanding
    
    Input: "Show me AP invoices older than 60 days in Excel"
    Output: {
        "report_type": "ap_aging",
        "filters": {"aging_days": ">60"},
        "output_format": "excel"
    }
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize intent parser
        
        Args:
            llm_client: LLM client (Groq/OpenAI/etc)
        """
        super().__init__("IntentParserAgent")
        
        if llm_client is None:
            try:
                from shared.llm.groq_client import get_groq_client
                self.llm = get_groq_client("accurate")
            except ImportError:
                logger.warning("LLM client not available, using fallback parsing")
                self.llm = None
        else:
            self.llm = llm_client
    
    def execute(self, input_data: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Parse user query
        
        Args:
            input_data: Natural language query
            params: Additional context (org_id, user_settings, etc)
            
        Returns:
            {
                "status": "success",
                "report_type": "...",
                "filters": {...},
                "output_format": "..."
            }
        """
        query = input_data
        params = params or {}
        
        self._log_decision(
            "Parsing user query",
            f"Query: {query}"
        )
        
        # Try LLM parsing first
        if self.llm:
            try:
                intent = self._parse_with_llm(query, params)
                
                self._log_decision(
                    f"LLM parsed: {intent.get('report_type')}",
                    f"Confidence: High"
                )
                
                return {
                    'status': 'success',
                    'method': 'llm',
                    **intent
                }
                
            except Exception as e:
                logger.warning(f"LLM parsing failed, using fallback: {e}")
        
        # Fallback to keyword parsing
        intent = self._parse_with_keywords(query)
        
        self._log_decision(
            f"Keyword parsed: {intent.get('report_type')}",
            f"Confidence: Medium"
        )
        
        return {
            'status': 'success',
            'method': 'keyword',
            **intent
        }
    
    def _parse_with_llm(self, query: str, context: Dict) -> Dict[str, Any]:
        """
        Parse query using LLM
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            Parsed intent
        """
        prompt = self._build_llm_prompt(query, context)
        
        response = self.llm.chat_completion([
            {
                "role": "system",
                "content": "You are an expert at parsing financial report requests. Respond ONLY with valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ])
        
        # Extract and parse JSON from response
        return self._extract_json_from_response(response)
    
    def _build_llm_prompt(self, query: str, context: Dict) -> str:
        """Build LLM prompt for parsing"""
        
        available_reports = [
            "ap_register", "ap_aging", "ap_overdue", "ap_duplicate",
            "ar_register", "ar_aging", "ar_collection", "dso"
        ]
        
        return f"""
Parse this financial report request.

Available report types: {', '.join(available_reports)}

Query: "{query}"

Extract:
1. report_type (one of the available types)
2. filters (date ranges, amounts, status, entity filters, etc.)
3. output_format (excel, pdf, word, json)

Respond with ONLY this JSON structure:
{{
    "report_type": "report_type_here",
    "filters": {{
        "date_from": "YYYY-MM-DD" or null,
        "date_to": "YYYY-MM-DD" or null,
        "aging_days": number or null,
        "amount_min": number or null,
        "amount_max": number or null,
        "status": ["status1", "status2"] or null,
        "entity_ids": [id1, id2] or null
    }},
    "output_format": "excel|pdf|word|json"
}}

Remove any null values. Be precise.
"""
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Find JSON object
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        
        raise ValueError("No JSON found in LLM response")
    
    def _parse_with_keywords(self, query: str) -> Dict[str, Any]:
        """
        Fallback keyword-based parsing
        
        Args:
            query: User query
            
        Returns:
            Parsed intent
        """
        query_lower = query.lower()
        
        # Determine report type
        report_type = self._detect_report_type(query_lower)
        
        # Extract filters
        filters = self._extract_filters(query_lower)
        
        # Determine output format
        output_format = self._detect_output_format(query_lower)
        
        return {
            "report_type": report_type,
            "filters": filters,
            "output_format": output_format
        }
    
    def _detect_report_type(self, query: str) -> str:
        """Detect report type from keywords"""
        
        # Priority-based matching
        if "aging" in query:
            if "ap" in query or "payable" in query or "vendor" in query:
                return "ap_aging"
            elif "ar" in query or "receivable" in query or "customer" in query:
                return "ar_aging"
            return "ap_aging"  # default
        
        if "overdue" in query or "sla" in query or "breach" in query:
            if "ar" in query or "receivable" in query:
                return "ar_collection"
            return "ap_overdue"
        
        if "duplicate" in query or "duplicates" in query:
            return "ap_duplicate"
        
        if "collection" in query or "priority" in query:
            return "ar_collection"
        
        if "dso" in query or "days sales outstanding" in query:
            return "dso"
        
        if "register" in query or "list" in query:
            if "ar" in query or "receivable" in query or "sales" in query or "customer" in query:
                return "ar_register"
            return "ap_register"
        
        # Default
        return "ap_register"
    
    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract filters from query"""
        
        filters = {}
        
        # Date ranges
        if "last month" in query:
            from datetime import datetime, timedelta
            today = datetime.now()
            first_of_month = today.replace(day=1)
            last_month_end = first_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            filters['date_from'] = last_month_start.strftime('%Y-%m-%d')
            filters['date_to'] = last_month_end.strftime('%Y-%m-%d')
        
        elif "this month" in query:
            from datetime import datetime
            today = datetime.now()
            filters['date_from'] = today.replace(day=1).strftime('%Y-%m-%d')
            filters['date_to'] = today.strftime('%Y-%m-%d')
        
        elif "this year" in query:
            from datetime import datetime
            year = datetime.now().year
            filters['date_from'] = f"{year}-01-01"
            filters['date_to'] = f"{year}-12-31"
        
        # Aging days
        age_match = re.search(r'(?:older than|more than|over|above)\s+(\d+)\s*days?', query)
        if age_match:
            filters['aging_days'] = int(age_match.group(1))
        
        # Amount
        amount_match = re.search(r'(?:\$|amount|value)\s*([\d,]+)', query)
        if amount_match:
            amount = float(amount_match.group(1).replace(',', ''))
            if "over" in query or "above" in query or "more than" in query:
                filters['amount_min'] = amount
            elif "under" in query or "below" in query or "less than" in query:
                filters['amount_max'] = amount
        
        # Status
        if "unpaid" in query:
            filters['status'] = ["unpaid", "partially_paid"]
        elif "paid" in query:
            filters['status'] = ["paid"]
        
        return filters
    
    def _detect_output_format(self, query: str) -> str:
        """Detect desired output format"""
        
        if "excel" in query or "xlsx" in query or "spreadsheet" in query:
            return "excel"
        elif "pdf" in query:
            return "pdf"
        elif "word" in query or "docx" in query or "document" in query:
            return "word"
        elif "json" in query or "api" in query or "data" in query:
            return "json"
        
        return "excel"  # default