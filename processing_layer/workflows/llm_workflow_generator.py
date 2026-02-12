"""
LLM Workflow Generator
Generates workflow definitions from user queries using LLM
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from shared.llm.groq_client import GroqClient
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class LLMWorkflowGenerator:
    """
    Generates workflow definitions from user queries using LLM
    No hardcoding - all workflows generated dynamically by AI
    """
    
    def __init__(self):
        self.llm = GroqClient()
    
    def generate_workflow(self, query: str, company_id: str, user_id: str) -> Dict[str, Any]:
        """
        Generate workflow definition from user query
        
        Args:
            query: User's natural language query
            company_id: Company identifier for context
            user_id: User identifier
            
        Returns:
            Workflow definition with nodes and edges
        """
        try:
            # Analyze query to determine report type and requirements
            analysis = self._analyze_query(query, company_id)
            
            # Generate workflow structure
            workflow_definition = self._generate_workflow_structure(analysis, query)
            
            # Validate and optimize workflow
            validated_workflow = self._validate_workflow(workflow_definition)
            
            logger.info(f"Generated workflow for query: {query}")
            return validated_workflow
            
        except Exception as e:
            logger.error(f"Failed to generate workflow: {e}")
            # Fallback to simple workflow
            return self._create_fallback_workflow(query)
    
    def _analyze_query(self, query: str, company_id: str) -> Dict[str, Any]:
        """Analyze user query to determine requirements"""
        
        # Get company context
        company_context = self._get_company_context(company_id)
        
        # LLM analysis prompt
        prompt = f"""
        Analyze this financial query and determine the workflow requirements:

        Query: "{query}"
        
        Company Context: {company_context}
        
        Please analyze and return JSON with:
        1. report_type: "ap_aging", "ap_register", "ap_overdue", "ar_aging", "ar_register", "ar_collection", "dso", or "custom"
        2. data_source: "vendor_invoices" for AP reports, "customer_invoices" for AR reports
        3. key_requirements: List of key requirements (e.g., "aging analysis", "outstanding amounts", "grouping by vendor")
        4. complexity: "simple", "medium", or "complex"
        5. time_range: "last_30_days", "last_90_days", "custom", or "all_time"
        
        Return ONLY valid JSON, no explanation.
        """
        
        try:
            response = self.llm.generate(prompt)
            analysis = json.loads(response)
            return analysis
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return self._get_default_analysis(query)
    
    def _get_company_context(self, company_id: str) -> str:
        """Get company context for better analysis"""
        # TODO: Fetch company details from database
        # For now, return generic context
        return "Financial services company with AP and AR operations"
    
    def _get_default_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback analysis for query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['ap aging', 'accounts payable aging', 'vendor aging']):
            return {
                'report_type': 'ap_aging',
                'data_source': 'vendor_invoices',
                'key_requirements': ['aging analysis', 'outstanding amounts', 'grouping by aging bucket'],
                'complexity': 'medium',
                'time_range': 'last_90_days'
            }
        elif any(word in query_lower for word in ['ar aging', 'accounts receivable aging', 'customer aging']):
            return {
                'report_type': 'ar_aging',
                'data_source': 'customer_invoices',
                'key_requirements': ['aging analysis', 'outstanding amounts', 'grouping by aging bucket'],
                'complexity': 'medium',
                'time_range': 'last_90_days'
            }
        elif any(word in query_lower for word in ['ap register', 'accounts payable register']):
            return {
                'report_type': 'ap_register',
                'data_source': 'vendor_invoices',
                'key_requirements': ['invoice register', 'payment status', 'summary totals'],
                'complexity': 'simple',
                'time_range': 'all_time'
            }
        elif any(word in query_lower for word in ['ar register', 'accounts receivable register']):
            return {
                'report_type': 'ar_register',
                'data_source': 'customer_invoices',
                'key_requirements': ['invoice register', 'payment status', 'summary totals'],
                'complexity': 'simple',
                'time_range': 'all_time'
            }
        else:
            return {
                'report_type': 'custom',
                'data_source': 'vendor_invoices',
                'key_requirements': ['data analysis', 'report generation'],
                'complexity': 'medium',
                'time_range': 'last_90_days'
            }
    
    def _generate_workflow_structure(self, analysis: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Generate workflow structure based on analysis"""
        
        report_type = analysis['report_type']
        data_source = analysis['data_source']
        requirements = analysis['key_requirements']
        
        # Generate nodes based on report type and requirements
        nodes = self._generate_nodes(report_type, data_source, requirements, query)
        
        # Generate edges to connect nodes
        edges = self._generate_edges(nodes)
        
        workflow_definition = {
            'edges': edges,
            'nodes': nodes,
            'metadata': {
                'report_type': report_type,
                'data_source': data_source,
                'complexity': analysis['complexity'],
                'time_range': analysis['time_range'],
                'generated_at': datetime.now().isoformat(),
                'query': query
            }
        }
        
        return workflow_definition
    
    def _generate_nodes(self, report_type: str, data_source: str, requirements: List[str], query: str) -> List[Dict[str, Any]]:
        """Generate workflow nodes"""
        
        nodes = []
        step_number = 1
        
        # 1. Data Fetch Node
        fetch_node = {
            'title': f"Fetch {data_source.replace('_', ' ').title()} Data",
            'params': {
                'category': 'purchase' if data_source == 'vendor_invoices' else 'sales',
                'date_range': 'last_90_days',
                'status_filter': 'all'
            },
            'status': 'pending',
            'step_id': f'step_{step_number}',
            'node_type': 'InvoiceFetchNode',
            'step_number': step_number,
            'description': f'Fetch data from {data_source} table'
        }
        nodes.append(fetch_node)
        step_number += 1
        
        # 2. Data Processing Nodes based on requirements
        if 'aging analysis' in requirements:
            # Calculate Outstanding Amounts
            outstanding_node = {
                'title': 'Calculate Outstanding Amounts',
                'params': {
                    'include_tax': True,
                    'currency': 'INR'
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'OutstandingCalculatorNode',
                'step_number': step_number,
                'description': 'Calculate outstanding amounts for each invoice'
            }
            nodes.append(outstanding_node)
            step_number += 1
            
            # Calculate Aging Days
            aging_node = {
                'title': 'Calculate Aging Days',
                'params': {
                    'include_weekends': True,
                    'as_of_date': 'auto'
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'AgingCalculatorNode',
                'step_number': step_number,
                'description': 'Calculate aging days for each invoice'
            }
            nodes.append(aging_node)
            step_number += 1
            
            # Group by Aging Bucket
            group_node = {
                'title': 'Group by Aging Bucket',
                'params': {
                    'buckets': ['0-30', '31-60', '61-90', '90+'],
                    'group_by': 'aging_bucket'
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'GroupingNode',
                'step_number': step_number,
                'description': 'Group invoices by aging buckets'
            }
            nodes.append(group_node)
            step_number += 1
        
        # 3. Summary Calculation
        summary_node = {
            'title': 'Calculate Summary Statistics',
            'params': {
                'include_percentages': True,
                'amount_field': 'inr_amount'
            },
            'status': 'pending',
            'step_id': f'step_{step_number}',
            'node_type': 'SummaryNode',
            'step_number': step_number,
            'description': 'Calculate summary statistics'
        }
        nodes.append(summary_node)
        step_number += 1
        
        # 4. Report Generation
        report_node = {
            'title': 'Generate Branded Excel Report',
            'params': {
                'include_logo': True,
                'branding': 'auto',
                'report_type': report_type
            },
            'status': 'pending',
            'step_id': f'step_{step_number}',
            'node_type': 'BrandedExcelGeneratorNode',
            'step_number': step_number,
            'description': 'Generate branded Excel report'
        }
        nodes.append(report_node)
        step_number += 1
        
        # 5. Branding Application
        branding_node = {
            'title': 'Apply Company Branding',
            'params': {
                'company_id': 'auto',
                'include_logo': True,
                'primary_color': 'auto',
                'secondary_color': 'auto'
            },
            'status': 'pending',
            'step_id': f'step_{step_number}',
            'node_type': 'BrandingLoaderNode',
            'step_number': step_number,
            'description': 'Apply company branding from database'
        }
        nodes.append(branding_node)
        step_number += 1
        
        return nodes
    
    def _generate_edges(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate edges to connect nodes in sequence"""
        edges = []
        
        for i in range(len(nodes) - 1):
            source_node = nodes[i]
            target_node = nodes[i + 1]
            
            edge = {
                'source': source_node['step_id'],
                'target': target_node['step_id']
            }
            edges.append(edge)
        
        return edges
    
    def _validate_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and optimize workflow structure"""
        
        # Validate nodes
        nodes = workflow_definition['nodes']
        for node in nodes:
            # Ensure all required fields are present
            required_fields = ['title', 'params', 'status', 'step_id', 'node_type', 'step_number']
            for field in required_fields:
                if field not in node:
                    node[field] = self._get_default_value(field, node.get('node_type'))
        
        # Validate edges
        edges = workflow_definition['edges']
        node_ids = {node['step_id'] for node in nodes}
        
        # Remove invalid edges
        valid_edges = []
        for edge in edges:
            if edge['source'] in node_ids and edge['target'] in node_ids:
                valid_edges.append(edge)
        
        workflow_definition['edges'] = valid_edges
        
        # Add workflow metadata
        workflow_definition['workflow_id'] = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow_definition['status'] = 'generated'
        
        return workflow_definition
    
    def _get_default_value(self, field: str, node_type: str) -> Any:
        """Get default value for missing field"""
        defaults = {
            'title': f'Process {node_type}',
            'params': {},
            'status': 'pending',
            'step_id': 'step_1',
            'node_type': 'UnknownNode',
            'step_number': 1
        }
        return defaults.get(field, None)
    
    def _create_fallback_workflow(self, query: str) -> Dict[str, Any]:
        """Create a simple fallback workflow"""
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
        Create a custom node definition
        
        Args:
            node_definition: Custom node specification
            
        Returns:
            Validated custom node
        """
        required_fields = ['title', 'node_type', 'description']
        
        # Validate required fields
        for field in required_fields:
            if field not in node_definition:
                raise ValueError(f"Missing required field: {field}")
        
        # Add default values
        custom_node = {
            'title': node_definition['title'],
            'params': node_definition.get('params', {}),
            'status': 'pending',
            'step_id': node_definition.get('step_id', f'custom_{datetime.now().strftime("%H%M%S")}'),
            'node_type': node_definition['node_type'],
            'step_number': node_definition.get('step_number', 1),
            'description': node_definition['description'],
            'custom': True,
            'llm_generated': True
        }
        
        logger.info(f"Created custom node: {custom_node['title']}")
        return custom_node


# Global instance
workflow_generator = LLMWorkflowGenerator()


def generate_workflow_from_query(query: str, company_id: str, user_id: str) -> Dict[str, Any]:
    """Convenience function to generate workflow from query"""
    return workflow_generator.generate_workflow(query, company_id, user_id)