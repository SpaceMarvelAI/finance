"""
Calculation Agent
Specialized agent for performing financial calculations and analysis
"""

from typing import Dict, Any, Optional, List, Union
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class CalculationAgent:
    """
    Calculation Agent
    
    Performs financial calculations, statistical analysis, and data aggregations.
    Handles complex mathematical operations and financial metrics.
    """
    
    def __init__(self, name: str, llm_config: Dict[str, Any], 
                 agent_type: str = 'calculation',
                 capabilities: Optional[List[str]] = None,
                 tools: Optional[List[str]] = None,
                 **kwargs):
        self.name = name
        self.llm_config = llm_config
        self.agent_type = agent_type
        self.capabilities = capabilities or ['financial_calculations', 'statistical_analysis', 'data_aggregation']
        self.tools = tools or ['calculation_tools', 'mathematical_tools']
        
        # Initialize agent
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the calculation agent"""
        try:
            # Import AutoGen components
            from autogen import AssistantAgent
            
            # Create system message for calculations
            system_message = self._generate_system_message()
            
            # Create AutoGen agent
            self.agent = AssistantAgent(
                name=self.name,
                system_message=system_message,
                llm_config=self.llm_config,
                **self._get_agent_config()
            )
            
            logger.info(f"Initialized Calculation Agent: {self.name}")
            
        except Exception as e:
            logger.error(f"Error initializing Calculation Agent: {str(e)}")
            raise
    
    def perform_calculations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform calculations on the provided data
        
        Args:
            data: Data to perform calculations on
            
        Returns:
            Calculation results
        """
        try:
            # Create calculation prompt
            calculation_prompt = self._create_calculation_prompt(data)
            
            # Get calculation instructions from LLM
            calculation_instructions = self.agent.generate_reply(
                messages=[{'content': calculation_prompt, 'role': 'user'}]
            )
            
            # Execute calculations
            calculation_results = self._execute_calculations(data, calculation_instructions)
            
            logger.info(f"Performed calculations on {len(data.get('records', []))} records")
            
            return calculation_results
            
        except Exception as e:
            logger.error(f"Error performing calculations: {str(e)}")
            return {
                'error': str(e),
                'data': data,
                'results': None
            }
    
    def analyze_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform statistical analysis on the data
        
        Args:
            data: Data to analyze statistically
            
        Returns:
            Statistical analysis results
        """
        try:
            # Create statistical analysis prompt
            analysis_prompt = self._create_statistical_analysis_prompt(data)
            
            # Get analysis instructions from LLM
            analysis_instructions = self.agent.generate_reply(
                messages=[{'content': analysis_prompt, 'role': 'user'}]
            )
            
            # Execute statistical analysis
            statistical_results = self._execute_statistical_analysis(data, analysis_instructions)
            
            logger.info(f"Performed statistical analysis on data")
            
            return statistical_results
            
        except Exception as e:
            logger.error(f"Error performing statistical analysis: {str(e)}")
            return {
                'error': str(e),
                'data': data,
                'statistical_results': None
            }
    
    def aggregate_data(self, data: Dict[str, Any], 
                      aggregation_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate data based on configuration
        
        Args:
            data: Data to aggregate
            aggregation_config: Configuration for aggregation
            
        Returns:
            Aggregated data
        """
        try:
            # Create aggregation prompt
            aggregation_prompt = self._create_aggregation_prompt(data, aggregation_config)
            
            # Get aggregation instructions from LLM
            aggregation_instructions = self.agent.generate_reply(
                messages=[{'content': aggregation_prompt, 'role': 'user'}]
            )
            
            # Execute data aggregation
            aggregated_data = self._execute_data_aggregation(data, aggregation_instructions)
            
            logger.info(f"Aggregated data with config: {aggregation_config}")
            
            return aggregated_data
            
        except Exception as e:
            logger.error(f"Error aggregating data: {str(e)}")
            return {
                'error': str(e),
                'data': data,
                'aggregation_config': aggregation_config,
                'aggregated_data': None
            }
    
    def _generate_system_message(self) -> str:
        """Generate system message for the calculation agent"""
        return """
        You are a specialized Calculation Agent. Your role is to:
        
        1. Perform complex financial calculations and mathematical operations
        2. Conduct statistical analysis and data aggregations
        3. Calculate financial metrics and ratios
        4. Handle data transformations and mathematical modeling
        5. Validate calculation accuracy and precision
        6. Generate derived metrics and calculated fields
        
        Your capabilities include:
        - Financial calculations (aggregations, averages, percentages, ratios)
        - Statistical analysis (mean, median, standard deviation, correlations)
        - Data aggregation (grouping, summarization, pivot operations)
        - Mathematical modeling and formula calculations
        - Financial ratio calculations (liquidity, profitability, efficiency ratios)
        - Trend analysis and forecasting calculations
        
        When performing calculations, focus on:
        - What specific calculations are needed based on the data and requirements?
        - What mathematical operations should be applied?
        - How should the data be aggregated or grouped?
        - What financial metrics or ratios should be calculated?
        - Are there any validation checks needed for calculation accuracy?
        - How should the results be formatted and presented?
        
        Always ensure calculation accuracy and provide detailed information about the calculation process.
        """
    
    def _get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration"""
        return {
            'human_input_mode': 'NEVER',
            'max_consecutive_auto_reply': 10,
            'temperature': 0.2,
            'top_p': 0.85,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0
        }
    
    def _create_calculation_prompt(self, data: Dict[str, Any]) -> str:
        """Create prompt for calculation planning"""
        return f"""
        Perform calculations on the following data:

        Data:
        {data}

        Please provide calculation instructions including:

        1. Aggregation Calculations: What aggregations are needed?
           (e.g., sum, count, average, maximum, minimum, etc.)

        2. Percentage Calculations: What percentage calculations are required?
           (e.g., percentage of total, growth rates, change percentages)

        3. Ratio Calculations: What financial ratios should be calculated?
           (e.g., current ratio, quick ratio, DSO, DPO, etc.)

        4. Trend Calculations: What trend analysis is needed?
           (e.g., period-over-period changes, moving averages, growth rates)

        5. Derived Metrics: What derived metrics should be calculated?
           (e.g., aging buckets, payment terms, due date calculations)

        6. Validation: What validation checks should be performed on calculations?

        Please provide detailed calculation instructions that can be executed.
        """
    
    def _execute_calculations(self, data: Dict[str, Any], 
                             calculation_instructions: str) -> Dict[str, Any]:
        """Execute calculations based on instructions"""
        try:
            # This would implement actual calculation logic
            # For now, return a structured response
            
            return {
                'data': data,
                'calculation_instructions': calculation_instructions,
                'aggregation_calculations': self._extract_aggregation_calculations(calculation_instructions),
                'percentage_calculations': self._extract_percentage_calculations(calculation_instructions),
                'ratio_calculations': self._extract_ratio_calculations(calculation_instructions),
                'trend_calculations': self._extract_trend_calculations(calculation_instructions),
                'derived_metrics': self._extract_derived_metrics(calculation_instructions),
                'validation_checks': self._extract_validation_checks(calculation_instructions),
                'calculation_timestamp': self._get_current_timestamp(),
                'status': 'calculated',
                'results': {}  # Would contain actual calculation results
            }
            
        except Exception as e:
            logger.error(f"Error executing calculations: {str(e)}")
            return {
                'error': str(e),
                'data': data,
                'calculation_instructions': calculation_instructions
            }
    
    def _create_statistical_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create prompt for statistical analysis"""
        return f"""
        Perform statistical analysis on the following data:

        Data:
        {data}

        Please provide statistical analysis including:

        1. Descriptive Statistics: What descriptive statistics should be calculated?
           (e.g., mean, median, mode, standard deviation, variance)

        2. Distribution Analysis: What distribution characteristics should be analyzed?
           (e.g., normality, skewness, kurtosis, outliers)

        3. Correlation Analysis: What correlations should be examined?
           (e.g., relationships between variables, correlation coefficients)

        4. Trend Analysis: What trends should be identified?
           (e.g., time series analysis, seasonal patterns, cyclical trends)

        5. Variance Analysis: What variance should be analyzed?
           (e.g., variance from mean, variance between groups)

        6. Confidence Intervals: What confidence intervals should be calculated?

        Please provide detailed statistical analysis instructions.
        """
    
    def _execute_statistical_analysis(self, data: Dict[str, Any], 
                                     analysis_instructions: str) -> Dict[str, Any]:
        """Execute statistical analysis based on instructions"""
        try:
            # This would implement actual statistical analysis logic
            # For now, return a structured response
            
            return {
                'data': data,
                'analysis_instructions': analysis_instructions,
                'descriptive_statistics': self._extract_descriptive_statistics(analysis_instructions),
                'distribution_analysis': self._extract_distribution_analysis(analysis_instructions),
                'correlation_analysis': self._extract_correlation_analysis(analysis_instructions),
                'trend_analysis': self._extract_trend_analysis(analysis_instructions),
                'variance_analysis': self._extract_variance_analysis(analysis_instructions),
                'confidence_intervals': self._extract_confidence_intervals(analysis_instructions),
                'analysis_timestamp': self._get_current_timestamp(),
                'status': 'analyzed',
                'statistical_results': {}  # Would contain actual statistical results
            }
            
        except Exception as e:
            logger.error(f"Error executing statistical analysis: {str(e)}")
            return {
                'error': str(e),
                'data': data,
                'analysis_instructions': analysis_instructions
            }
    
    def _create_aggregation_prompt(self, data: Dict[str, Any], 
                                  aggregation_config: Dict[str, Any]) -> str:
        """Create prompt for data aggregation"""
        return f"""
        Aggregate the following data based on the configuration:

        Data:
        {data}

        Aggregation Configuration:
        {aggregation_config}

        Please provide aggregation instructions including:

        1. Grouping Criteria: How should the data be grouped?
           (e.g., by vendor, customer, date, category)

        2. Aggregation Functions: What aggregation functions should be applied?
           (e.g., sum, count, average, max, min)

        3. Time Periods: What time periods should be used for aggregation?
           (e.g., daily, weekly, monthly, quarterly, yearly)

        4. Hierarchical Aggregation: Should there be multiple levels of aggregation?
           (e.g., by vendor then by month, by customer then by region)

        5. Filter Conditions: What filters should be applied before aggregation?

        6. Output Format: How should the aggregated data be structured?

        Please provide detailed aggregation instructions.
        """
    
    def _execute_data_aggregation(self, data: Dict[str, Any], 
                                 aggregation_instructions: str) -> Dict[str, Any]:
        """Execute data aggregation based on instructions"""
        try:
            # This would implement actual data aggregation logic
            # For now, return a structured response
            
            return {
                'data': data,
                'aggregation_instructions': aggregation_instructions,
                'grouping_criteria': self._extract_grouping_criteria(aggregation_instructions),
                'aggregation_functions': self._extract_aggregation_functions(aggregation_instructions),
                'time_periods': self._extract_time_periods(aggregation_instructions),
                'hierarchical_aggregation': self._extract_hierarchical_aggregation(aggregation_instructions),
                'filter_conditions': self._extract_filter_conditions(aggregation_instructions),
                'output_format': self._extract_output_format(aggregation_instructions),
                'aggregation_timestamp': self._get_current_timestamp(),
                'status': 'aggregated',
                'aggregated_data': {}  # Would contain actual aggregated data
            }
            
        except Exception as e:
            logger.error(f"Error executing data aggregation: {str(e)}")
            return {
                'error': str(e),
                'data': data,
                'aggregation_instructions': aggregation_instructions
            }
    
    # Helper methods for extracting information
    def _extract_aggregation_calculations(self, calculation_instructions: str) -> Dict[str, Any]:
        """Extract aggregation calculations from instructions"""
        # Implementation would parse the calculation instructions
        return {"sum": True, "count": True, "average": True}
    
    def _extract_percentage_calculations(self, calculation_instructions: str) -> Dict[str, Any]:
        """Extract percentage calculations from instructions"""
        # Implementation would parse the calculation instructions
        return {"percentage_of_total": True, "growth_rates": False}
    
    def _extract_ratio_calculations(self, calculation_instructions: str) -> Dict[str, Any]:
        """Extract ratio calculations from instructions"""
        # Implementation would parse the calculation instructions
        return {"current_ratio": False, "quick_ratio": False, "dso": False}
    
    def _extract_trend_calculations(self, calculation_instructions: str) -> Dict[str, Any]:
        """Extract trend calculations from instructions"""
        # Implementation would parse the calculation instructions
        return {"period_over_period": False, "moving_averages": False}
    
    def _extract_derived_metrics(self, calculation_instructions: str) -> Dict[str, Any]:
        """Extract derived metrics from instructions"""
        # Implementation would parse the calculation instructions
        return {"aging_buckets": False, "payment_terms": False}
    
    def _extract_validation_checks(self, calculation_instructions: str) -> Dict[str, Any]:
        """Extract validation checks from instructions"""
        # Implementation would parse the calculation instructions
        return {"accuracy_checks": True, "precision_checks": True}
    
    def _extract_descriptive_statistics(self, analysis_instructions: str) -> Dict[str, Any]:
        """Extract descriptive statistics from instructions"""
        # Implementation would parse the analysis instructions
        return {"mean": True, "median": True, "std_dev": True}
    
    def _extract_distribution_analysis(self, analysis_instructions: str) -> Dict[str, Any]:
        """Extract distribution analysis from instructions"""
        # Implementation would parse the analysis instructions
        return {"normality": False, "skewness": False, "outliers": False}
    
    def _extract_correlation_analysis(self, analysis_instructions: str) -> Dict[str, Any]:
        """Extract correlation analysis from instructions"""
        # Implementation would parse the analysis instructions
        return {"correlation_coefficients": False, "relationships": False}
    
    def _extract_trend_analysis(self, analysis_instructions: str) -> Dict[str, Any]:
        """Extract trend analysis from instructions"""
        # Implementation would parse the analysis instructions
        return {"time_series": False, "seasonal_patterns": False}
    
    def _extract_variance_analysis(self, analysis_instructions: str) -> Dict[str, Any]:
        """Extract variance analysis from instructions"""
        # Implementation would parse the analysis instructions
        return {"variance_from_mean": False, "between_groups": False}
    
    def _extract_confidence_intervals(self, analysis_instructions: str) -> Dict[str, Any]:
        """Extract confidence intervals from instructions"""
        # Implementation would parse the analysis instructions
        return {"confidence_level": 0.95, "interval_type": "normal"}
    
    def _extract_grouping_criteria(self, aggregation_instructions: str) -> List[str]:
        """Extract grouping criteria from instructions"""
        # Implementation would parse the aggregation instructions
        return ["vendor", "customer"]
    
    def _extract_aggregation_functions(self, aggregation_instructions: str) -> List[str]:
        """Extract aggregation functions from instructions"""
        # Implementation would parse the aggregation instructions
        return ["sum", "count", "average"]
    
    def _extract_time_periods(self, aggregation_instructions: str) -> List[str]:
        """Extract time periods from instructions"""
        # Implementation would parse the aggregation instructions
        return ["monthly", "quarterly"]
    
    def _extract_hierarchical_aggregation(self, aggregation_instructions: str) -> bool:
        """Extract hierarchical aggregation from instructions"""
        # Implementation would parse the aggregation instructions
        return False
    
    def _extract_filter_conditions(self, aggregation_instructions: str) -> Dict[str, Any]:
        """Extract filter conditions from instructions"""
        # Implementation would parse the aggregation instructions
        return {"date_range": "last_90_days", "status": ["open"]}
    
    def _extract_output_format(self, aggregation_instructions: str) -> str:
        """Extract output format from instructions"""
        # Implementation would parse the aggregation instructions
        return "structured"
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().isoformat()