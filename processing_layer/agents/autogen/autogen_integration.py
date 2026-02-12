"""
AutoGen Integration
Integration layer for connecting AutoGen agents with the existing system
"""

from typing import Dict, Any, List, Optional, Union
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class AutoGenIntegration:
    """
    AutoGen Integration Layer
    
    Provides integration between AutoGen agents and the existing system components.
    Handles communication, data exchange, and workflow coordination.
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        self.llm_config = llm_config
        self.orchestrator = None
        self.integrations = {}
        
        # Initialize orchestrator
        self._initialize_orchestrator()
    
    def _initialize_orchestrator(self):
        """Initialize the AutoGen orchestrator"""
        try:
            from .autogen_orchestrator import AutoGenOrchestrator
            # Create orchestrator without config to avoid circular dependency
            self.orchestrator = AutoGenOrchestrator({})
            logger.info("AutoGen Integration initialized with orchestrator")
        except ImportError as e:
            logger.error(f"Failed to initialize orchestrator: {str(e)}")
            raise
    
    def integrate_with_llm_router(self, llm_router_instance) -> bool:
        """
        Integrate with the existing LLM router
        
        Args:
            llm_router_instance: Instance of the LLM router
            
        Returns:
            Integration success status
        """
        try:
            # Store reference to LLM router
            self.integrations['llm_router'] = llm_router_instance
            
            # Register AutoGen as a handler
            llm_router_instance.register_handler('autogen', self.handle_autogen_request)
            
            logger.info("AutoGen integrated with LLM router")
            
            return True
            
        except Exception as e:
            logger.error(f"Error integrating with LLM router: {str(e)}")
            return False
    
    def integrate_with_workflow_builder(self, workflow_builder_instance) -> bool:
        """
        Integrate with the workflow builder
        
        Args:
            workflow_builder_instance: Instance of the workflow builder
            
        Returns:
            Integration success status
        """
        try:
            # Store reference to workflow builder
            self.integrations['workflow_builder'] = workflow_builder_instance
            
            logger.info("AutoGen integrated with workflow builder")
            
            return True
            
        except Exception as e:
            logger.error(f"Error integrating with workflow builder: {str(e)}")
            return False
    
    def integrate_with_database(self, database_manager_instance) -> bool:
        """
        Integrate with the database manager
        
        Args:
            database_manager_instance: Instance of the database manager
            
        Returns:
            Integration success status
        """
        try:
            # Store reference to database manager
            self.integrations['database_manager'] = database_manager_instance
            
            logger.info("AutoGen integrated with database manager")
            
            return True
            
        except Exception as e:
            logger.error(f"Error integrating with database manager: {str(e)}")
            return False
    
    def handle_autogen_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle requests routed to AutoGen
        
        Args:
            request_data: Request data from LLM router
            
        Returns:
            Response data
        """
        try:
            # Extract request information
            user_query = request_data.get('user_query', '')
            company_id = request_data.get('company_id', '')
            report_type = request_data.get('report_type', 'generic')
            
            # Create specialized workflow
            workflow_type = self._determine_workflow_type(report_type)
            
            # Execute workflow
            result = self.orchestrator.create_specialized_workflow(
                workflow_type=workflow_type,
                user_query=user_query
            )
            
            # Process result
            if result['status'] == 'success':
                return {
                    'status': 'success',
                    'data': result['result'],
                    'metadata': {
                        'workflow_id': result['workflow_id'],
                        'execution_time': result['execution_time']
                    }
                }
            else:
                return {
                    'status': 'error',
                    'error': result['error'],
                    'metadata': {
                        'workflow_type': workflow_type
                    }
                }
            
        except Exception as e:
            logger.error(f"Error handling AutoGen request: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'metadata': {}
            }
    
    def create_autogen_workflow_from_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """yt
        Create an AutoGen workflow from a template
        
        Args:
            template_data: Template data for the workflow
            
        Returns:
            Workflow creation result
        """
        try:
            # Convert template to workflow configuration
            workflow_config = self._convert_template_to_workflow_config(template_data)
            
            # Create workflow
            workflow_id = self.orchestrator.create_workflow(workflow_config)
            
            logger.info(f"Created AutoGen workflow from template: {workflow_id}")
            
            return {
                'status': 'success',
                'workflow_id': workflow_id,
                'config': workflow_config
            }
            
        except Exception as e:
            logger.error(f"Error creating AutoGen workflow from template: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'template_data': template_data
            }
    
    def execute_autogen_workflow(self, workflow_id: str, 
                                execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an AutoGen workflow
        
        Args:
            workflow_id: ID of the workflow to execute
            execution_data: Data for workflow execution
            
        Returns:
            Execution result
        """
        try:
            # Extract execution parameters
            user_query = execution_data.get('user_query', '')
            company_id = execution_data.get('company_id', '')
            
            # Execute workflow
            result = self.orchestrator.execute_workflow(
                workflow_id=workflow_id,
                user_query=user_query
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing AutoGen workflow {workflow_id}: {str(e)}")
            return {
                'status': 'error',
                'workflow_id': workflow_id,
                'error': str(e)
            }
    
    def get_autogen_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of the AutoGen system"""
        try:
            capabilities = {
                'orchestrator_status': 'active' if self.orchestrator else 'inactive',
                'integrations': list(self.integrations.keys()),
                'workflow_types': self._get_supported_workflow_types(),
                'agent_types': self.orchestrator.get_agent_capabilities() if self.orchestrator else {}
            }
            
            return {
                'status': 'success',
                'capabilities': capabilities
            }
            
        except Exception as e:
            logger.error(f"Error getting AutoGen capabilities: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def sync_with_existing_workflows(self) -> Dict[str, Any]:
        """
        Synchronize AutoGen with existing workflows
        
        Returns:
            Synchronization result
        """
        try:
            sync_results = {}
            
            # Sync with workflow builder if available
            if 'workflow_builder' in self.integrations:
                workflow_builder = self.integrations['workflow_builder']
                # Get existing workflows and convert to AutoGen format
                existing_workflows = workflow_builder.list_workflows()
                sync_results['workflow_builder'] = {
                    'status': 'synced',
                    'workflows_count': len(existing_workflows.get('workflows', {}))
                }
            
            # Sync with database if available
            if 'database_manager' in self.integrations:
                database_manager = self.integrations['database_manager']
                # Get workflow data from database
                sync_results['database_manager'] = {
                    'status': 'synced',
                    'data_access': True
                }
            
            logger.info(f"AutoGen synchronized with existing systems: {sync_results}")
            
            return {
                'status': 'success',
                'sync_results': sync_results
            }
            
        except Exception as e:
            logger.error(f"Error syncing with existing workflows: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _determine_workflow_type(self, report_type: str) -> str:
        """Determine the appropriate workflow type based on report type"""
        report_type_mapping = {
            'ap_aging': 'report_generation',
            'ar_aging': 'report_generation',
            'ap_register': 'report_generation',
            'ar_register': 'report_generation',
            'dso': 'report_generation',
            'collections': 'report_generation',
            'overdue': 'report_generation',
            'analysis': 'data_analysis',
            'default': 'report_generation'
        }
        
        return report_type_mapping.get(report_type.lower(), 'report_generation')
    
    def _convert_template_to_workflow_config(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert template data to workflow configuration"""
        try:
            # Extract template information
            template_type = template_data.get('type', 'generic')
            template_config = template_data.get('config', {})
            
            # Create workflow configuration
            workflow_config = {
                'team_config': template_config.get('team_config', []),
                'description': template_config.get('description', f'AutoGen workflow for {template_type}'),
                'template_type': template_type
            }
            
            return workflow_config
            
        except Exception as e:
            logger.error(f"Error converting template to workflow config: {str(e)}")
            raise
    
    def _get_supported_workflow_types(self) -> List[str]:
        """Get list of supported workflow types"""
        return [
            'report_generation',
            'data_analysis',
            'custom'
        ]
    
    def cleanup(self):
        """Clean up AutoGen integration"""
        try:
            if self.orchestrator:
                self.orchestrator.cleanup_workflows()
            
            self.integrations.clear()
            
            logger.info("AutoGen integration cleaned up")
            
        except Exception as e:
            logger.error(f"Error during AutoGen integration cleanup: {str(e)}")