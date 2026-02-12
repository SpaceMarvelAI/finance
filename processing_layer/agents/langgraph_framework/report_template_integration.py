"""
Report Template Integration
LangGraph integration for existing report template nodes
Provides dynamic report generation using the fixed report nodes
"""

from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
import asyncio
from pathlib import Path

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from processing_layer.workflows.nodes.output_nodes.report_templates.ap_aging_node_fixed import APAgingReportNode
from processing_layer.workflows.nodes.output_nodes.report_templates.ap_register_node_fixed import APRegisterReportNode
from processing_layer.workflows.nodes.output_nodes.report_templates.ar_aging_node_fixed import ARAgingReportNode
from processing_layer.workflows.nodes.output_nodes.report_templates.ar_register_node import ARRegisterReportNode
from processing_layer.workflows.nodes.output_nodes.report_templates.ar_collection_node import ARCollectionReportNode
from processing_layer.workflows.nodes.output_nodes.report_templates.dso_node import DSOReportNode
from processing_layer.workflows.nodes.output_nodes.report_templates.ap_overdue_node import APOverdueReportNode

from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class ReportTemplateIntegration:
    """
    LangGraph integration for existing report template nodes
    
    Provides:
    - Dynamic report template selection
    - Integration with LangGraph workflows
    - State management for report generation
    - Error handling and validation
    """
    
    def __init__(self):
        self.report_nodes = {
            'ap_aging': APAgingReportNode(),
            'ap_register': APRegisterReportNode(),
            'ar_aging': ARAgingReportNode(),
            'ar_register': ARRegisterReportNode(),
            'ar_collection': ARCollectionReportNode(),
            'dso': DSOReportNode(),
            'ap_overdue': APOverdueReportNode()
        }
        
        self.checkpointer = MemorySaver()
        
    def get_available_templates(self) -> List[str]:
        """Get list of available report templates"""
        return list(self.report_nodes.keys())
    
    def get_template_info(self, template_type: str) -> Dict[str, Any]:
        """Get information about a specific template"""
        if template_type not in self.report_nodes:
            raise ValueError(f"Unknown template type: {template_type}")
        
        node = self.report_nodes[template_type]
        return {
            'name': node.name,
            'category': node.category,
            'description': node.description,
            'input_schema': node.input_schema,
            'output_schema': node.output_schema,
            'allowed_params': node.ALLOWED_PARAMS
        }
    
    def validate_report_data(self, template_type: str, report_data: Dict[str, Any]) -> bool:
        """Validate report data for a specific template"""
        if template_type not in self.report_nodes:
            raise ValueError(f"Unknown template type: {template_type}")
        
        node = self.report_nodes[template_type]
        return node.validate_data(report_data)
    
    def generate_report(
        self, 
        template_type: str, 
        report_data: Dict[str, Any], 
        company_id: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate report using the specified template
        
        Args:
            template_type: Type of report template to use
            report_data: Data for the report
            company_id: Company identifier for branding
            params: Additional parameters
            
        Returns:
            Report generation result
        """
        if template_type not in self.report_nodes:
            raise ValueError(f"Unknown template type: {template_type}")
        
        node = self.report_nodes[template_type]
        node_params = params or {}
        node_params['company_id'] = company_id
        
        try:
            # Validate data
            if not node.validate_data(report_data):
                raise ValueError("Invalid report data")
            
            # Generate report
            result = node.run(report_data, node_params)
            
            logger.info(f"Generated {template_type} report: {result['file_path']}")
            
            return {
                'status': 'success',
                'template_type': template_type,
                'file_path': result['file_path'],
                'branding_applied': result['branding_applied'],
                'metadata': result.get('metadata', {}),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate {template_type} report: {str(e)}")
            return {
                'status': 'error',
                'template_type': template_type,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def generate_report_async(
        self, 
        template_type: str, 
        report_data: Dict[str, Any], 
        company_id: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Async version of report generation"""
        return self.generate_report(template_type, report_data, company_id, params)
    
    def create_report_workflow(self, template_type: str) -> StateGraph:
        """
        Create a LangGraph workflow for report generation
        
        Args:
            template_type: Type of report to generate
            
        Returns:
            Compiled StateGraph
        """
        if template_type not in self.report_nodes:
            raise ValueError(f"Unknown template type: {template_type}")
        
        # Create workflow builder
        builder = StateGraph(self._get_state_schema())
        
        # Add report generation node
        def report_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Report generation node function"""
            try:
                template_type = state.get('template_type')
                report_data = state.get('report_data')
                company_id = state.get('company_id')
                params = state.get('params', {})
                
                result = self.generate_report(template_type, report_data, company_id, params)
                
                return {
                    'report_result': result,
                    'status': 'completed',
                    'error': None
                }
                
            except Exception as e:
                return {
                    'report_result': None,
                    'status': 'failed',
                    'error': str(e)
                }
        
        builder.add_node('generate_report', report_generation_node)
        
        # Add edges
        builder.set_entry_point('generate_report')
        builder.add_edge('generate_report', END)
        
        # Compile workflow
        workflow = builder.compile(checkpointer=self.checkpointer)
        return workflow
    
    def _get_state_schema(self) -> Dict[str, Any]:
        """Define the state schema for report generation workflows"""
        return {
            'template_type': str,
            'report_data': Dict[str, Any],
            'company_id': str,
            'params': Dict[str, Any],
            'report_result': Optional[Dict[str, Any]],
            'status': str,
            'error': Optional[str],
            'execution_history': List[Dict[str, Any]]
        }
    
    def execute_report_workflow(
        self, 
        template_type: str, 
        report_data: Dict[str, Any], 
        company_id: str,
        params: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a report generation workflow
        
        Args:
            template_type: Type of report to generate
            report_data: Data for the report
            company_id: Company identifier
            params: Additional parameters
            session_id: Optional session ID for state persistence
            
        Returns:
            Workflow execution result
        """
        try:
            # Create workflow
            workflow = self.create_report_workflow(template_type)
            
            # Prepare input state
            input_state = {
                'template_type': template_type,
                'report_data': report_data,
                'company_id': company_id,
                'params': params or {},
                'report_result': None,
                'status': 'pending',
                'error': None,
                'execution_history': []
            }
            
            # Prepare configuration
            config = {}
            if session_id:
                config['configurable'] = {'thread_id': session_id}
            
            # Execute workflow
            result = workflow.invoke(input_state, config=config)
            
            logger.info(f"Report workflow executed: {template_type}")
            
            return {
                'status': 'success',
                'template_type': template_type,
                'result': result,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Report workflow execution failed: {str(e)}")
            return {
                'status': 'error',
                'template_type': template_type,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def execute_report_workflow_async(
        self, 
        template_type: str, 
        report_data: Dict[str, Any], 
        company_id: str,
        params: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Async version of workflow execution"""
        return self.execute_report_workflow(template_type, report_data, company_id, params, session_id)
    
    def get_template_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get capabilities of all available templates"""
        capabilities = {}
        
        for template_type, node in self.report_nodes.items():
            capabilities[template_type] = {
                'name': node.name,
                'description': node.description,
                'input_schema': node.input_schema,
                'output_schema': node.output_schema,
                'allowed_params': node.ALLOWED_PARAMS,
                'category': node.category
            }
        
        return capabilities
    
    def validate_template_config(self, template_type: str, config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration for a specific template
        
        Args:
            template_type: Type of template
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if template_type not in self.report_nodes:
            errors.append(f"Unknown template type: {template_type}")
            return errors
        
        node = self.report_nodes[template_type]
        
        # Check required parameters
        required_params = ['report_data', 'company_id']
        for param in required_params:
            if param not in config:
                errors.append(f"Missing required parameter: {param}")
        
        # Check allowed parameters
        allowed_params = node.ALLOWED_PARAMS
        for param in config.keys():
            if param not in allowed_params and param not in required_params:
                errors.append(f"Unknown parameter: {param}")
        
        return errors
    
    def create_multi_report_workflow(self, report_configs: List[Dict[str, Any]]) -> StateGraph:
        """
        Create a workflow for generating multiple reports
        
        Args:
            report_configs: List of report configurations
            
        Returns:
            Compiled StateGraph
        """
        builder = StateGraph(self._get_multi_report_state_schema())
        
        # Add nodes for each report
        for i, config in enumerate(report_configs):
            template_type = config['template_type']
            
            def create_report_node(index: int, tpl_type: str):
                def report_node(state: Dict[str, Any]) -> Dict[str, Any]:
                    try:
                        report_data = state['report_configs'][index]['report_data']
                        company_id = state['report_configs'][index]['company_id']
                        params = state['report_configs'][index].get('params', {})
                        
                        result = self.generate_report(tpl_type, report_data, company_id, params)
                        
                        return {
                            f'report_{index}_result': result,
                            f'report_{index}_status': 'completed'
                        }
                    except Exception as e:
                        return {
                            f'report_{index}_result': None,
                            f'report_{index}_status': 'failed',
                            f'report_{index}_error': str(e)
                        }
                
                return report_node
            
            node_func = create_report_node(i, template_type)
            builder.add_node(f'report_{i}', node_func)
        
        # Add edges
        builder.set_entry_point('report_0')
        
        for i in range(len(report_configs) - 1):
            builder.add_edge(f'report_{i}', f'report_{i+1}')
        
        builder.add_edge(f'report_{len(report_configs)-1}', END)
        
        # Compile workflow
        workflow = builder.compile(checkpointer=self.checkpointer)
        return workflow
    
    def _get_multi_report_state_schema(self) -> Dict[str, Any]:
        """Define state schema for multi-report workflows"""
        return {
            'report_configs': List[Dict[str, Any]],
            'results': List[Dict[str, Any]],
            'status': str,
            'error': Optional[str]
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.report_nodes.clear()
        logger.info("Report template integration cleaned up")