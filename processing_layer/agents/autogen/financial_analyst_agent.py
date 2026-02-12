"""
Financial Analyst Agent
Specialized agent for analyzing financial queries and planning workflows
"""

from typing import Dict, Any, Optional, List, Union
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class FinancialAnalystAgent:
    """
    Financial Analyst Agent
    
    Analyzes user queries, understands financial context, and plans appropriate workflows.
    Acts as the reasoning component in the ReACT pattern.
    """
    
    def __init__(self, name: str, llm_config: Dict[str, Any], 
                 agent_type: str = 'financial_analyst',
                 capabilities: Optional[List[str]] = None,
                 tools: Optional[List[str]] = None,
                 **kwargs):
        self.name = name
        self.llm_config = llm_config
        self.agent_type = agent_type
        self.capabilities = capabilities or ['query_analysis', 'workflow_planning', 'financial_reasoning']
        self.tools = tools or ['analysis_tools', 'planning_tools']
        self.description = "Financial Analyst Agent for query analysis and workflow planning"
        
        # Initialize agent
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the financial analyst agent"""
        try:
            # Import AutoGen components
            from autogen import AssistantAgent
            
            # Create system message for financial analysis
            system_message = self._generate_system_message()
            
            # Create AutoGen agent
            self.agent = AssistantAgent(
                name=self.name,
                system_message=system_message,
                llm_config=self.llm_config,
                **self._get_agent_config()
            )
            
            logger.info(f"Initialized Financial Analyst Agent: {self.name}")
            
        except Exception as e:
            logger.error(f"Error initializing Financial Analyst Agent: {str(e)}")
            raise
    
    def analyze_query(self, user_query: str) -> Dict[str, Any]:
        """
        Analyze user query and extract key information
        
        Args:
            user_query: User's natural language query
            
        Returns:
            Analysis result with extracted information
        """
        try:
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(user_query)
            
            # Get analysis from LLM
            analysis_result = self.agent.generate_reply(
                messages=[{'content': analysis_prompt, 'role': 'user'}]
            )
            
            # Parse and structure the analysis
            structured_analysis = self._parse_analysis_result(analysis_result, user_query)
            
            logger.info(f"Analyzed query: {user_query[:50]}...")
            
            return structured_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            return {
                'error': str(e),
                'query': user_query,
                'analysis': 'Analysis failed'
            }
    
    def plan_workflow(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan workflow based on query analysis
        
        Args:
            analysis_result: Result from query analysis
            
        Returns:
            Workflow plan
        """
        try:
            # Create workflow planning prompt
            planning_prompt = self._create_planning_prompt(analysis_result)
            
            # Get workflow plan from LLM
            planning_result = self.agent.generate_reply(
                messages=[{'content': planning_prompt, 'role': 'user'}]
            )
            
            # Parse and structure the workflow plan
            workflow_plan = self._parse_workflow_plan(planning_result, analysis_result)
            
            logger.info(f"Planned workflow for analysis: {analysis_result.get('query_type', 'unknown')}")
            
            return workflow_plan
            
        except Exception as e:
            logger.error(f"Error planning workflow: {str(e)}")
            return {
                'error': str(e),
                'analysis': analysis_result,
                'plan': 'Planning failed'
            }
    
    def generate_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate financial insights from data
        
        Args:
            data: Data to analyze for insights
            
        Returns:
            Generated insights
        """
        try:
            # Create insights prompt
            insights_prompt = self._create_insights_prompt(data)
            
            # Get insights from LLM
            insights_result = self.agent.generate_reply(
                messages=[{'content': insights_prompt, 'role': 'user'}]
            )
            
            # Parse and structure the insights
            structured_insights = self._parse_insights_result(insights_result, data)
            
            logger.info(f"Generated insights from data")
            
            return structured_insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {
                'error': str(e),
                'data': data,
                'insights': 'Insights generation failed'
            }
    
    def _generate_system_message(self) -> str:
        """Generate system message for the financial analyst agent"""
        return """
        You are a specialized Financial Analyst Agent. Your role is to:
        
        1. Analyze user queries to understand financial context and requirements
        2. Identify the type of financial analysis or report needed
        3. Extract key parameters, timeframes, and data requirements
        4. Plan appropriate workflows for data retrieval, calculation, and reporting
        5. Generate insights and recommendations based on financial data
        
        Your capabilities include:
        - Query analysis and understanding
        - Workflow planning and orchestration
        - Financial reasoning and analysis
        - Report type identification
        - Data requirement specification
        
        When analyzing queries, focus on:
        - What type of financial analysis is requested?
        - What data sources are needed?
        - What time period is relevant?
        - What calculations or metrics are required?
        - What format should the output take?
        
        Always provide structured, actionable analysis that can guide the workflow execution.
        """
    
    def _get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration"""
        return {
            'human_input_mode': 'NEVER',
            'max_consecutive_auto_reply': 10
        }
    
    def _create_analysis_prompt(self, user_query: str) -> str:
        """Create prompt for query analysis"""
        return f"""
        Analyze the following user query and extract key information:

        User Query: "{user_query}"

        Please provide a structured analysis with the following information:

        1. Query Type: What type of financial analysis or report is being requested?
           (e.g., AP Aging, AR Aging, Collections, DSO, Overdue Analysis, etc.)

        2. Data Requirements: What data sources and information are needed?
           (e.g., vendor invoices, customer invoices, payment data, etc.)

        3. Time Period: What time period is relevant for this analysis?
           (e.g., last 30 days, last 90 days, specific date range, etc.)

        4. Key Parameters: What specific parameters or filters are mentioned?
           (e.g., specific vendors, customers, amounts, statuses, etc.)

        5. Output Format: What format should the final output take?
           (e.g., Excel report, PDF, dashboard, summary, etc.)

        6. Special Requirements: Are there any special requirements or considerations?
           (e.g., company-specific rules, industry standards, compliance requirements, etc.)

        Please provide your analysis in a structured JSON format.
        """
    
    def _parse_analysis_result(self, analysis_result: str, original_query: str) -> Dict[str, Any]:
        """Parse and structure the analysis result"""
        try:
            # Extract key information from the analysis result
            # This would typically involve parsing the LLM response
            
            return {
                'original_query': original_query,
                'query_type': self._extract_query_type(analysis_result),
                'data_requirements': self._extract_data_requirements(analysis_result),
                'time_period': self._extract_time_period(analysis_result),
                'key_parameters': self._extract_key_parameters(analysis_result),
                'output_format': self._extract_output_format(analysis_result),
                'special_requirements': self._extract_special_requirements(analysis_result),
                'analysis_timestamp': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error parsing analysis result: {str(e)}")
            return {
                'error': str(e),
                'original_query': original_query,
                'analysis_result': analysis_result
            }
    
    def _create_planning_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """Create prompt for workflow planning"""
        return f"""
        Based on the following query analysis, plan an appropriate workflow:

        Analysis Result:
        {analysis_result}

        Please create a detailed workflow plan that includes:

        1. Required Agents: Which specialized agents are needed?
           (e.g., Data Retrieval, Calculation, Report Generation, etc.)

        2. Data Flow: What is the sequence of data processing steps?

        3. Calculations: What specific calculations or analyses are required?

        4. Output Generation: How should the final output be generated and formatted?

        5. Error Handling: What potential issues should be handled?

        Please provide the workflow plan in a structured format that can be executed by the agent team.
        """
    
    def _parse_workflow_plan(self, planning_result: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure the workflow plan"""
        try:
            return {
                'analysis_result': analysis_result,
                'workflow_plan': planning_result,
                'agents_required': self._extract_agents_required(planning_result),
                'data_flow': self._extract_data_flow(planning_result),
                'calculations': self._extract_calculations(planning_result),
                'output_specification': self._extract_output_specification(planning_result),
                'error_handling': self._extract_error_handling(planning_result),
                'planning_timestamp': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error parsing workflow plan: {str(e)}")
            return {
                'error': str(e),
                'analysis_result': analysis_result,
                'planning_result': planning_result
            }
    
    def _create_insights_prompt(self, data: Dict[str, Any]) -> str:
        """Create prompt for insights generation"""
        return f"""
        Analyze the following financial data and generate insights:

        Data: {data}

        Please provide insights including:

        1. Key Trends: What trends or patterns are evident in the data?
        2. Anomalies: Are there any unusual or unexpected findings?
        3. Recommendations: What actions or improvements would you recommend?
        4. Risk Factors: Are there any potential risks or concerns?
        5. Opportunities: Are there any opportunities for optimization or improvement?

        Please provide actionable insights that can guide decision-making.
        """
    
    def _parse_insights_result(self, insights_result: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure the insights result"""
        try:
            return {
                'data': data,
                'insights': insights_result,
                'key_trends': self._extract_key_trends(insights_result),
                'anomalies': self._extract_anomalies(insights_result),
                'recommendations': self._extract_recommendations(insights_result),
                'risk_factors': self._extract_risk_factors(insights_result),
                'opportunities': self._extract_opportunities(insights_result),
                'insights_timestamp': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error parsing insights result: {str(e)}")
            return {
                'error': str(e),
                'data': data,
                'insights_result': insights_result
            }
    
    # Helper methods for extracting information
    def _extract_query_type(self, analysis_result: str) -> str:
        """Extract query type from analysis result"""
        # Implementation would parse the analysis result
        return "report_generation"
    
    def _extract_data_requirements(self, analysis_result: str) -> List[str]:
        """Extract data requirements from analysis result"""
        # Implementation would parse the analysis result
        return ["financial_data", "transaction_data"]
    
    def _extract_time_period(self, analysis_result: str) -> str:
        """Extract time period from analysis result"""
        # Implementation would parse the analysis result
        return "last_90_days"
    
    def _extract_key_parameters(self, analysis_result: str) -> Dict[str, Any]:
        """Extract key parameters from analysis result"""
        # Implementation would parse the analysis result
        return {}
    
    def _extract_output_format(self, analysis_result: str) -> str:
        """Extract output format from analysis result"""
        # Implementation would parse the analysis result
        return "excel_report"
    
    def _extract_special_requirements(self, analysis_result: str) -> List[str]:
        """Extract special requirements from analysis result"""
        # Implementation would parse the analysis result
        return []
    
    def _extract_agents_required(self, planning_result: str) -> List[str]:
        """Extract required agents from planning result"""
        # Implementation would parse the planning result
        return ["data_retrieval", "calculation", "report_generation"]
    
    def _extract_data_flow(self, planning_result: str) -> List[str]:
        """Extract data flow from planning result"""
        # Implementation would parse the planning result
        return ["data_retrieval", "processing", "calculation", "report_generation"]
    
    def _extract_calculations(self, planning_result: str) -> List[str]:
        """Extract calculations from planning result"""
        # Implementation would parse the planning result
        return ["aggregation", "averages", "percentages"]
    
    def _extract_output_specification(self, planning_result: str) -> Dict[str, Any]:
        """Extract output specification from planning result"""
        # Implementation would parse the planning result
        return {"format": "excel", "charts": True, "summary": True}
    
    def _extract_error_handling(self, planning_result: str) -> List[str]:
        """Extract error handling from planning result"""
        # Implementation would parse the planning result
        return ["data_validation", "missing_data_handling"]
    
    def _extract_key_trends(self, insights_result: str) -> List[str]:
        """Extract key trends from insights result"""
        # Implementation would parse the insights result
        return []
    
    def _extract_anomalies(self, insights_result: str) -> List[str]:
        """Extract anomalies from insights result"""
        # Implementation would parse the insights result
        return []
    
    def _extract_recommendations(self, insights_result: str) -> List[str]:
        """Extract recommendations from insights result"""
        # Implementation would parse the insights result
        return []
    
    def _extract_risk_factors(self, insights_result: str) -> List[str]:
        """Extract risk factors from insights result"""
        # Implementation would parse the insights result
        return []
    
    def _extract_opportunities(self, insights_result: str) -> List[str]:
        """Extract opportunities from insights result"""
        # Implementation would parse the insights result
        return []
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().isoformat()