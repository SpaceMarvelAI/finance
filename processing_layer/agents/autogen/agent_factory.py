"""
Agent Factory
Factory pattern implementation for creating specialized AutoGen agents
"""

from typing import Dict, Any, Optional, Union, List
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class AgentFactory:
    """
    Agent Factory
    
    Creates specialized agents based on configuration and requirements.
    Implements factory pattern for agent creation.
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        self.llm_config = llm_config
        self.agent_types = {}
        
        # Register agent types
        self._register_agent_types()
    
    def _register_agent_types(self):
        """Register available agent types and their configurations"""
        self.agent_types = {
            'financial_analyst': {
                'class': 'FinancialAnalystAgent',
                'description': 'Analyzes financial queries and plans workflows',
                'capabilities': ['query_analysis', 'workflow_planning', 'financial_reasoning'],
                'tools': ['analysis_tools', 'planning_tools']
            },
            'data_retrieval': {
                'class': 'DataRetrievalAgent',
                'description': 'Retrieves and processes financial data',
                'capabilities': ['database_query', 'data_processing', 'file_operations'],
                'tools': ['database_tools', 'file_tools']
            },
            'calculation': {
                'class': 'CalculationAgent',
                'description': 'Performs financial calculations and analysis',
                'capabilities': ['financial_calculations', 'statistical_analysis', 'data_aggregation'],
                'tools': ['calculation_tools', 'mathematical_tools']
            },
            'report_generation': {
                'class': 'ReportGenerationAgent',
                'description': 'Generates financial reports and visualizations',
                'capabilities': ['report_generation', 'data_visualization', 'template_processing'],
                'tools': ['report_tools', 'visualization_tools']
            },
            'data_analysis': {
                'class': 'DataAnalysisAgent',
                'description': 'Performs advanced data analysis and insights',
                'capabilities': ['data_analysis', 'trend_analysis', 'predictive_modeling'],
                'tools': ['analysis_tools', 'statistical_tools']
            }
        }
    
    def create_agent(self, agent_type: str, agent_name: str, 
                    agent_params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create an agent of the specified type
        
        Args:
            agent_type: Type of agent to create
            agent_name: Name for the agent
            agent_params: Additional parameters for the agent
            
        Returns:
            Created agent instance
        """
        try:
            # Check if agent type is registered
            if agent_type not in self.agent_types:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            agent_config = self.agent_types[agent_type]
            
            # Import the agent class
            agent_class = self._import_agent_class(agent_config['class'])
            
            # Create proper LLM config for Groq
            import os
            llm_config = {
                'config_list': [{
                    'model': self.llm_config.get('model', 'llama3-8b-8192'),
                    'api_key': os.getenv('GROQ_API_KEY', self.llm_config.get('api_key', '')),
                    'api_type': 'groq'
                }],
                'max_tokens': 1000
            }
            
            # Create agent instance
            agent = agent_class(
                name=agent_name,
                llm_config=llm_config,
                agent_type=agent_type,
                capabilities=agent_config['capabilities'],
                tools=agent_config['tools'],
                **(agent_params or {})
            )
            
            logger.info(f"Created agent: {agent_name} ({agent_type})")
            
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent {agent_name} ({agent_type}): {str(e)}")
            raise
    
    def create_team(self, team_config: List[Dict[str, Any]]) -> List[Any]:
        """
        Create a team of agents based on configuration
        
        Args:
            team_config: List of agent configurations
            
        Returns:
            List of created agent instances
        """
        try:
            agents = []
            
            for agent_config in team_config:
                agent_type = agent_config.get('type', 'generic')
                agent_name = agent_config.get('name', f'{agent_type}_agent')
                agent_params = agent_config.get('config', {})
                
                agent = self.create_agent(agent_type, agent_name, agent_params)
                agents.append(agent)
            
            logger.info(f"Created team with {len(agents)} agents")
            
            return agents
            
        except Exception as e:
            logger.error(f"Error creating agent team: {str(e)}")
            raise
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all available agent types"""
        try:
            capabilities = {}
            
            for agent_type, config in self.agent_types.items():
                capabilities[agent_type] = {
                    'description': config['description'],
                    'capabilities': config['capabilities'],
                    'tools': config['tools']
                }
            
            return capabilities
            
        except Exception as e:
            logger.error(f"Error getting agent capabilities: {str(e)}")
            return {}
    
    def validate_agent_config(self, agent_type: str, agent_params: Dict[str, Any]) -> bool:
        """
        Validate agent configuration
        
        Args:
            agent_type: Type of agent
            agent_params: Agent parameters to validate
            
        Returns:
            Validation result
        """
        try:
            if agent_type not in self.agent_types:
                return False
            
            # Basic validation - check if required parameters are present
            required_params = self._get_required_params(agent_type)
            
            for param in required_params:
                if param not in agent_params:
                    logger.warning(f"Missing required parameter: {param} for agent type: {agent_type}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating agent config: {str(e)}")
            return False
    
    def _import_agent_class(self, class_name: str) -> Any:
        """Import agent class dynamically"""
        try:
            # Import from the current module
            module_name = f"processing_layer.agents.autogen.{class_name.lower()}"
            
            # Try importing the class
            if class_name == 'FinancialAnalystAgent':
                from .financial_analyst_agent import FinancialAnalystAgent
                return FinancialAnalystAgent
            elif class_name == 'DataRetrievalAgent':
                from .data_retrieval_agent import DataRetrievalAgent
                return DataRetrievalAgent
            elif class_name == 'CalculationAgent':
                from .calculation_agent import CalculationAgent
                return CalculationAgent
            elif class_name == 'ReportGenerationAgent':
                from .report_generation_agent import ReportGenerationAgent
                return ReportGenerationAgent
            else:
                raise ImportError(f"Unknown agent class: {class_name}")
                
        except ImportError as e:
            logger.error(f"Failed to import agent class {class_name}: {str(e)}")
            raise
    
    def _get_required_params(self, agent_type: str) -> List[str]:
        """Get required parameters for agent type"""
        required_params_map = {
            'financial_analyst': ['name', 'llm_config'],
            'data_retrieval': ['name', 'llm_config'],
            'calculation': ['name', 'llm_config'],
            'report_generation': ['name', 'llm_config'],
            'data_analysis': ['name', 'llm_config']
        }
        
        return required_params_map.get(agent_type, ['name', 'llm_config'])
    
    def update_agent_type(self, agent_type: str, config: Dict[str, Any]):
        """
        Update agent type configuration
        
        Args:
            agent_type: Type of agent to update
            config: New configuration
        """
        try:
            if agent_type in self.agent_types:
                self.agent_types[agent_type].update(config)
                logger.info(f"Updated agent type configuration: {agent_type}")
            else:
                logger.warning(f"Agent type not found: {agent_type}")
                
        except Exception as e:
            logger.error(f"Error updating agent type {agent_type}: {str(e)}")
    
    def register_agent_type(self, agent_type: str, config: Dict[str, Any]):
        """
        Register a new agent type
        
        Args:
            agent_type: Type of agent
            config: Agent configuration
        """
        try:
            self.agent_types[agent_type] = config
            logger.info(f"Registered new agent type: {agent_type}")
            
        except Exception as e:
            logger.error(f"Error registering agent type {agent_type}: {str(e)}")
    
    def get_available_agent_types(self) -> List[str]:
        """Get list of available agent types"""
        return list(self.agent_types.keys())