"""
Variable Extractor
Extracts all variables from natural language queries into structured JSON
"""

from typing import Dict, Any, Optional, List
import json
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class VariableExtractor:
    """
    Variable Extractor using LLM
    
    Extracts all variables from query:
    - Time variables (dates, periods)
    - Entity variables (vendors, customers, departments)
    - Filter variables (amounts, aging, status)
    - Output variables (format, grouping, sorting)
    - Analysis variables (metrics, comparisons, thresholds)
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize variable extractor
        
        Args:
            llm_client: LLM client for extraction
        """
        self.llm = llm_client
        
        if self.llm is None:
            try:
                from groq_client import get_groq_client
                self.llm = get_groq_client("accurate")
            except:
                pass
    
    def extract(self, query: str) -> Dict[str, Any]:
        """
        Extract all variables from query
        
        Args:
            query: User query string
            
        Returns:
            {
                "time": {...},
                "entities": {...},
                "filters": {...},
                "output": {...},
                "analysis": {...},
                "raw_query": "..."
            }
        """
        
        if self.llm:
            try:
                return self._extract_with_llm(query)
            except Exception as e:
                print(f"LLM extraction failed: {e}, using fallback")
        
        return self._extract_with_keywords(query)
    
    def _extract_with_llm(self, query: str) -> Dict[str, Any]:
        """
        Extract variables using LLM
        
        Args:
            query: User query
            
        Returns:
            Extracted variables
        """
        prompt = self._build_extraction_prompt(query)
        
        response = self.llm.generate(prompt)
        
        result = self._extract_json_from_response(response)
        result['raw_query'] = query
        result['extraction_method'] = 'llm'
        
        return result
    
    def _build_extraction_prompt(self, query: str) -> str:
        """Build LLM prompt for variable extraction"""
        
        return f"""
Extract ALL variables from this financial query.

Query: "{query}"

Extract these variable categories:

1. TIME VARIABLES:
   - time_period: "last_month" | "this_month" | "last_quarter" | "this_year" | "last_year" | "ytd" | "custom"
   - date_from: "YYYY-MM-DD" (start date)
   - date_to: "YYYY-MM-DD" (end date)
   - fiscal_year: "FY2024" | "2024"
   - relative_time: "last_30_days" | "last_90_days"

2. ENTITY VARIABLES:
   - vendor: Vendor name (e.g., "AWS", "Google", "Microsoft")
   - customer: Customer name
   - department: Department name
   - cost_center: Cost center code
   - project: Project name
   - category: Category name

3. FILTER VARIABLES:
   - aging_days: Number of days (e.g., 60, 90)
   - aging_operator: ">", "<", ">=", "<=", "="
   - amount_min: Minimum amount
   - amount_max: Maximum amount
   - status: ["paid", "unpaid", "overdue", "partially_paid"]
   - currency: "USD" | "EUR" | "INR" | "GBP"
   - invoice_type: "sales" | "purchase" | "credit_note"

4. OUTPUT VARIABLES:
   - output_format: "excel" | "pdf" | "json" | "csv" | "word"
   - grouping: "by_vendor" | "by_customer" | "by_date" | "by_category"
   - sort_by: "amount" | "date" | "aging" | "name"
   - sort_order: "asc" | "desc"
   - include_charts: true | false

5. ANALYSIS VARIABLES:
   - metric: "revenue" | "profit" | "dso" | "dpo" | "cash_flow"
   - comparison: "yoy" | "mom" | "qoq" | "wow"
   - threshold: Numeric threshold value
   - aggregation: "sum" | "avg" | "count" | "max" | "min"
   - breakdown: ["region", "product", "channel"]

Respond with ONLY this JSON structure:
{{
    "time": {{
        "time_period": "...",
        "date_from": "...",
        "date_to": "..."
    }},
    "entities": {{
        "vendor": "...",
        "customer": "..."
    }},
    "filters": {{
        "aging_days": 60,
        "status": ["unpaid"]
    }},
    "output": {{
        "output_format": "excel",
        "sort_by": "amount"
    }},
    "analysis": {{
        "metric": "...",
        "comparison": "..."
    }}
}}

Rules:
1. Only include variables that are EXPLICITLY mentioned in the query
2. Remove any empty or null values
3. Infer dates from relative time periods (e.g., "last month" → actual dates)
4. Be precise with entity names - extract exact names mentioned
5. If no output format specified, default to "excel"
"""
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
            
            cleaned_result = self._remove_null_values(result)
            
            return cleaned_result
        
        raise ValueError("No valid JSON found in LLM response")
    
    def _remove_null_values(self, data: Dict) -> Dict:
        """Remove null/empty values from dictionary"""
        
        if isinstance(data, dict):
            return {
                k: self._remove_null_values(v)
                for k, v in data.items()
                if v is not None and v != {} and v != []
            }
        elif isinstance(data, list):
            return [self._remove_null_values(item) for item in data if item is not None]
        else:
            return data
    
    def _extract_with_keywords(self, query: str) -> Dict[str, Any]:
        """
        Fallback keyword-based extraction
        
        Args:
            query: User query
            
        Returns:
            Extracted variables
        """
        query_lower = query.lower()
        
        variables = {
            'time': self._extract_time_variables(query_lower),
            'entities': self._extract_entity_variables(query_lower),
            'filters': self._extract_filter_variables(query_lower),
            'output': self._extract_output_variables(query_lower),
            'analysis': self._extract_analysis_variables(query_lower),
            'raw_query': query,
            'extraction_method': 'keyword'
        }
        
        variables = self._remove_null_values(variables)
        
        return variables
    
    def _extract_time_variables(self, query: str) -> Dict[str, Any]:
        """Extract time-related variables"""
        
        time_vars = {}
        today = datetime.now()
        
        if "last month" in query:
            first_of_month = today.replace(day=1)
            last_month_end = first_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            
            time_vars['time_period'] = 'last_month'
            time_vars['date_from'] = last_month_start.strftime('%Y-%m-%d')
            time_vars['date_to'] = last_month_end.strftime('%Y-%m-%d')
        
        elif "this month" in query:
            time_vars['time_period'] = 'this_month'
            time_vars['date_from'] = today.replace(day=1).strftime('%Y-%m-%d')
            time_vars['date_to'] = today.strftime('%Y-%m-%d')
        
        elif "last quarter" in query or "q4" in query or "q3" in query:
            time_vars['time_period'] = 'last_quarter'
        
        elif "this year" in query or "ytd" in query:
            time_vars['time_period'] = 'this_year'
            time_vars['date_from'] = f"{today.year}-01-01"
            time_vars['date_to'] = today.strftime('%Y-%m-%d')
        
        elif "last year" in query:
            time_vars['time_period'] = 'last_year'
            time_vars['date_from'] = f"{today.year - 1}-01-01"
            time_vars['date_to'] = f"{today.year - 1}-12-31"
        
        fiscal_year_match = re.search(r'fy\s*(\d{4})', query)
        if fiscal_year_match:
            time_vars['fiscal_year'] = f"FY{fiscal_year_match.group(1)}"
        
        days_match = re.search(r'last\s+(\d+)\s+days?', query)
        if days_match:
            days = int(days_match.group(1))
            time_vars['relative_time'] = f'last_{days}_days'
            time_vars['date_from'] = (today - timedelta(days=days)).strftime('%Y-%m-%d')
            time_vars['date_to'] = today.strftime('%Y-%m-%d')
        
        return time_vars
    
    def _extract_entity_variables(self, query: str) -> Dict[str, Any]:
        """Extract entity-related variables"""
        
        entities = {}
        
        vendors = ['aws', 'amazon', 'google', 'microsoft', 'oracle', 'salesforce', 'azure']
        for vendor in vendors:
            if vendor in query:
                entities['vendor'] = vendor.upper() if vendor != 'amazon' else 'AWS'
                break
        
        if 'customer' in query or 'client' in query:
            customer_match = re.search(r'customer\s+([A-Z][a-zA-Z\s]+)', query)
            if customer_match:
                entities['customer'] = customer_match.group(1).strip()
        
        departments = ['engineering', 'sales', 'marketing', 'hr', 'finance', 'operations']
        for dept in departments:
            if dept in query:
                entities['department'] = dept.capitalize()
                break
        
        return entities
    
    def _extract_filter_variables(self, query: str) -> Dict[str, Any]:
        """Extract filter-related variables"""
        
        filters = {}
        
        aging_match = re.search(r'(?:older than|more than|over|above)\s+(\d+)\s*days?', query)
        if aging_match:
            filters['aging_days'] = int(aging_match.group(1))
            filters['aging_operator'] = '>'
        
        aging_match_less = re.search(r'(?:less than|under|below)\s+(\d+)\s*days?', query)
        if aging_match_less:
            filters['aging_days'] = int(aging_match_less.group(1))
            filters['aging_operator'] = '<'
        
        amount_match = re.search(r'(?:\$|amount|value)\s*([\d,]+)', query)
        if amount_match:
            amount = float(amount_match.group(1).replace(',', ''))
            if "over" in query or "above" in query or "more than" in query:
                filters['amount_min'] = amount
            elif "under" in query or "below" in query or "less than" in query:
                filters['amount_max'] = amount
            else:
                filters['amount'] = amount
        
        if "unpaid" in query:
            filters['status'] = ["unpaid", "partially_paid"]
        elif "paid" in query and "unpaid" not in query:
            filters['status'] = ["paid"]
        elif "overdue" in query:
            filters['status'] = ["overdue"]
        
        currencies = ['usd', 'eur', 'inr', 'gbp', 'jpy']
        for currency in currencies:
            if currency in query:
                filters['currency'] = currency.upper()
                break
        
        return filters
    
    def _extract_output_variables(self, query: str) -> Dict[str, Any]:
        """Extract output-related variables"""
        
        output = {}
        
        if "excel" in query or "xlsx" in query or "spreadsheet" in query:
            output['output_format'] = "excel"
        elif "pdf" in query:
            output['output_format'] = "pdf"
        elif "word" in query or "docx" in query:
            output['output_format'] = "word"
        elif "json" in query or "api" in query:
            output['output_format'] = "json"
        elif "csv" in query:
            output['output_format'] = "csv"
        else:
            output['output_format'] = "excel"
        
        if "group by vendor" in query or "by vendor" in query:
            output['grouping'] = "by_vendor"
        elif "group by customer" in query or "by customer" in query:
            output['grouping'] = "by_customer"
        elif "group by date" in query or "by date" in query:
            output['grouping'] = "by_date"
        
        if "sort by amount" in query:
            output['sort_by'] = "amount"
        elif "sort by date" in query:
            output['sort_by'] = "date"
        elif "sort by aging" in query:
            output['sort_by'] = "aging"
        
        if "ascending" in query or "asc" in query:
            output['sort_order'] = "asc"
        elif "descending" in query or "desc" in query:
            output['sort_order'] = "desc"
        
        if "chart" in query or "graph" in query or "visualization" in query:
            output['include_charts'] = True
        
        return output
    
    def _extract_analysis_variables(self, query: str) -> Dict[str, Any]:
        """Extract analysis-related variables"""
        
        analysis = {}
        
        metrics = ['revenue', 'profit', 'loss', 'dso', 'dpo', 'cash flow', 'working capital']
        for metric in metrics:
            if metric in query:
                analysis['metric'] = metric.replace(' ', '_')
                break
        
        if "year over year" in query or "yoy" in query:
            analysis['comparison'] = "yoy"
        elif "month over month" in query or "mom" in query:
            analysis['comparison'] = "mom"
        elif "quarter over quarter" in query or "qoq" in query:
            analysis['comparison'] = "qoq"
        
        threshold_match = re.search(r'threshold\s+(?:of\s+)?(\d+)', query)
        if threshold_match:
            analysis['threshold'] = int(threshold_match.group(1))
        
        if "sum" in query or "total" in query:
            analysis['aggregation'] = "sum"
        elif "average" in query or "avg" in query:
            analysis['aggregation'] = "avg"
        elif "count" in query:
            analysis['aggregation'] = "count"
        
        return analysis


def test_variable_extractor():
    """Test the variable extractor"""
    
    extractor = VariableExtractor()
    
    test_queries = [
        "Show me Namecheap invoices from last month older than 60 days in Excel",
        "Analyze revenue trends for Q4 year over year",
        "Generate AP aging report for unpaid invoices over $1000",
        "Customer invoices for December sorted by amount descending",
        "Show overdue invoices from Engineering department",
        "Cash flow forecast for next quarter with charts",
        "GST report for FY2024 in PDF format",
        "Budget vs actual variance analysis",
        "Show me all vendor bills from last 90 days",
        "AR aging grouped by customer in Excel"
    ]
    
    print("=" * 70)
    print("VARIABLE EXTRACTOR TEST")
    print("=" * 70)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = extractor.extract(query)
        print(f"Variables: {json.dumps(result, indent=2)}")
        print("-" * 70)


if __name__ == "__main__":
    test_variable_extractor()