"""
LLM Integration for Agent Orchestrator
Simple integration of LLM workflow generation with existing agent system
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from shared.llm.factory import LLMFactory
from shared.config.logging_config import get_logger

# Import LLM workflow generator
from processing_layer.workflows.llm_workflow_generator import LLMWorkflowGenerator


logger = get_logger(__name__)


class LLMWorkflowIntegration:
    """
    Simple integration layer for LLM workflow generation
    """
    
    def __init__(self):
        self.workflow_generator = LLMWorkflowGenerator()
    
    async def generate_workflow_from_query(self, query: str, company_id: str, user_id: str) -> Dict[str, Any]:
        """
        Generate workflow from user query using LLM
        
        Args:
            query: User's natural language query
            company_id: Company identifier
            user_id: User identifier
            
        Returns:
            Generated workflow definition
        """
        try:
            # Generate workflow using LLM
            workflow_definition = self.workflow_generator.generate_workflow(query, company_id, user_id)
            
            logger.info(f"Generated workflow for query: {query}")
            return workflow_definition
            
        except Exception as e:
            logger.error(f"Failed to generate workflow: {e}")
            # Return fallback workflow
            return {
                'edges': [],
                'nodes': [
                    {
                        'title': 'Fetch Data',
                        'params': {'query': query},
                        'status': 'pending',
                        'step_id': 'step_1',
                        'node_type': 'InvoiceFetchNode',
                        'step_number': 1
                    },
                    {
                        'title': 'Generate Report',
                        'params': {'query': query},
                        'status': 'pending',
                        'step_id': 'step_2',
                        'node_type': 'BrandedExcelGeneratorNode',
                        'step_number': 2
                    }
                ],
                'metadata': {
                    'report_type': 'custom',
                    'data_source': 'vendor_invoices',
                    'complexity': 'simple',
                    'time_range': 'all_time',
                    'generated_at': datetime.now().isoformat(),
                    'query': query
                }
            }
    
    def create_custom_node(self, node_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a custom node using LLM workflow generator
        
        Args:
            node_definition: Custom node specification
            
        Returns:
            Validated custom node
        """
        try:
            custom_node = self.workflow_generator.create_custom_node(node_definition)
            logger.info(f"Created custom node: {custom_node['title']}")
            return custom_node
        except Exception as e:
            logger.error(f"Failed to create custom node: {e}")
            raise


# Global instance
llm_integration = LLMWorkflowIntegration()


def generate_workflow_from_query(query: str, company_id: str, user_id: str) -> Dict[str, Any]:
    """Convenience function to generate workflow from query"""
    return llm_integration.generate_workflow_from_query(query, company_id, user_id)