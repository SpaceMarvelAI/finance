"""
Production Workflow Planner Agent
Integrates with existing financial automation system
Can generate new nodes on-demand if needed
"""

import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

# Add project to path
project_path = os.path.dirname(os.path.abspath(__file__))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

try:
    from base_agent import BaseAgent
    from logging_config import get_logger
    logger = get_logger(__name__)
except:
    import logging
    logger = logging.getLogger(__name__)
    
    class BaseAgent:
        def __init__(self, name):
            self.name = name
            self.execution_history = []
        
        def _log_decision(self, decision, reason):
            self.execution_history.append({
                'decision': decision,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            })
            logger.info(f"[{self.name}] DECISION: {decision} | REASON: {reason}")
        
        def _get_timestamp(self):
            return datetime.now().isoformat()
        
        def get_execution_history(self):
            return self.execution_history


class WorkflowPlannerAgent(BaseAgent):
    """
    Advanced Workflow Planner
    
    Features:
    - Plans workflows dynamically
    - Can generate missing nodes
    - Validates node combinations
    - Optimizes workflow structure
    """
    
    def __init__(self, llm_client=None):
        super().__init__("WorkflowPlannerAgent")
        
        # Try to load LLM
        if llm_client is None:
            try:
                from groq_client import get_groq_client
                self.llm = get_groq_client("accurate")
                logger.info("LLM initialized successfully")
            except Exception as e:
                logger.warning(f"LLM not available: {e}, using rule-based planning")
                self.llm = None
        else:
            self.llm = llm_client
        
        # Define core available nodes (from existing system)
        self.core_nodes = {
            'data': [
                {'type': 'InvoiceFetchNode', 'description': 'Fetch invoices from database'},
                {'type': 'PaymentFetchNode', 'description': 'Fetch payment records'},
            ],
            'calculation': [
                {'type': 'OutstandingCalculatorNode', 'description': 'Calculate outstanding amounts'},
                {'type': 'AgingCalculatorNode', 'description': 'Calculate aging days and buckets'},
                {'type': 'SLACheckerNode', 'description': 'Check SLA breaches'},
            ],
            'aggregation': [
                {'type': 'FilterNode', 'description': 'Filter records by conditions'},
                {'type': 'GroupingNode', 'description': 'Group records by field'},
                {'type': 'SummaryNode', 'description': 'Calculate summary statistics'},
                {'type': 'SortNode', 'description': 'Sort records'},
            ],
            'output': [
                {'type': 'ExcelGeneratorNode', 'description': 'Generate Excel report'},
                {'type': 'PDFGeneratorNode', 'description': 'Generate PDF report'},
            ]
        }
        
        # Track generated nodes
        self.generated_nodes = []
    
    def execute(self, input_data: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Plan workflow from requirement
        
        Args:
            input_data: User requirement (natural language)
            params: Additional parameters
            
        Returns:
            Workflow plan with steps and edges
        """
        params = params or {}
        requirement = input_data
        
        self._log_decision(
            "Planning workflow for requirement",
            f"Requirement: {requirement}"
        )
        
        try:
            # Step 1: Analyze requirement
            self._log_decision(
                "Analyzing requirement",
                "Extracting: goal, data_type, filters, operations, output"
            )
            analysis = self._analyze_requirement(requirement)
            
            # Step 2: Check if we need custom nodes
            missing_nodes = self._check_missing_nodes(analysis)
            if missing_nodes:
                self._log_decision(
                    "Missing nodes detected",
                    f"Will generate: {', '.join(missing_nodes)}"
                )
            
            # Step 3: Build workflow
            self._log_decision(
                "Building workflow structure",
                "Creating DAG with nodes and edges"
            )
            workflow = self._build_workflow(analysis, missing_nodes)
            
            # Step 4: Validate workflow
            validation = self._validate_workflow(workflow)
            if not validation['valid']:
                self._log_decision(
                    "Workflow validation failed",
                    f"Errors: {validation['errors']}"
                )
                return {
                    'status': 'error',
                    'error': 'Workflow validation failed',
                    'validation_errors': validation['errors'],
                    'workflow': workflow
                }
            
            self._log_decision(
                "Workflow planned successfully",
                f"Total steps: {len(workflow['steps'])}, Edges: {len(workflow.get('edges', []))}"
            )
            
            return {
                'status': 'success',
                'workflow': workflow,
                'analysis': analysis,
                'generated_nodes': self.generated_nodes,
                'execution_history': self.get_execution_history()
            }
            
        except Exception as e:
            logger.error(f"Workflow planning failed: {e}", exc_info=True)
            self._log_decision(
                "Planning failed with error",
                str(e)
            )
            
            return {
                'status': 'error',
                'error': str(e),
                'workflow': None,
                'execution_history': self.get_execution_history()
            }
    
    def _analyze_requirement(self, requirement: str) -> Dict[str, Any]:
        """Analyze user requirement using rules"""
        
        req_lower = requirement.lower()
        
        # Determine category
        if any(x in req_lower for x in ["ap", "payable", "vendor", "purchase"]):
            category = "ap"
        elif any(x in req_lower for x in ["ar", "receivable", "customer", "sales"]):
            category = "ar"
        else:
            category = "ap"
        
        # Determine calculations
        calculations = []
        if "aging" in req_lower or "age" in req_lower or "old" in req_lower:
            calculations.append("aging")
        if "outstanding" in req_lower or "unpaid" in req_lower or "balance" in req_lower:
            calculations.append("outstanding")
        if "sla" in req_lower or "overdue" in req_lower or "breach" in req_lower:
            calculations.append("sla")
        if "duplicate" in req_lower:
            calculations.append("duplicate")
        
        # Always add outstanding if we have aging
        if "aging" in calculations and "outstanding" not in calculations:
            calculations.insert(0, "outstanding")
        
        # Determine aggregations
        aggregations = []
        if "group" in req_lower or "bucket" in req_lower:
            aggregations.append("group")
        if "total" in req_lower or "summary" in req_lower:
            aggregations.append("summary")
        if "filter" in req_lower or req_lower.find("older than") != -1 or req_lower.find("more than") != -1:
            aggregations.append("filter")
        if "sort" in req_lower or "order" in req_lower:
            aggregations.append("sort")
        
        # Default aggregations for aging
        if "aging" in calculations:
            if "group" not in aggregations:
                aggregations.append("group")
            if "summary" not in aggregations:
                aggregations.append("summary")
        
        # Output format
        if "excel" in req_lower or "xlsx" in req_lower:
            output_format = "excel"
        elif "pdf" in req_lower:
            output_format = "pdf"
        else:
            output_format = "excel"
        
        # Extract filters
        filters = {}
        age_match = re.search(r'(?:older than|more than|over|above)\s+(\d+)\s*days?', req_lower)
        if age_match:
            filters['min_aging_days'] = int(age_match.group(1))
        
        return {
            "goal": requirement,
            "category": category,
            "calculations": calculations,
            "aggregations": aggregations,
            "output_format": output_format,
            "filters": filters
        }
    
    def _check_missing_nodes(self, analysis: Dict) -> List[str]:
        """Check if we need to generate any custom nodes"""
        missing = []
        
        # Check if we need special calculators
        calcs = analysis.get('calculations', [])
        if 'duplicate' in calcs:
            # Check if DuplicateDetectorNode exists
            if not self._node_exists('DuplicateDetectorNode'):
                missing.append('DuplicateDetectorNode')
        
        return missing
    
    def _node_exists(self, node_type: str) -> bool:
        """Check if node exists in core nodes"""
        for category in self.core_nodes.values():
            if any(n['type'] == node_type for n in category):
                return True
        return False
    
    def _build_workflow(self, analysis: Dict, missing_nodes: List[str]) -> Dict[str, Any]:
        """Build complete workflow structure"""
        
        workflow = {
            'id': f"workflow_{datetime.now().isoformat()}",
            'name': 'Custom Workflow',
            'steps': [],
            'edges': [],
            'metadata': {
                'requirement': analysis.get('goal'),
                'analysis': analysis,
                'created_at': datetime.now().isoformat()
            }
        }
        
        step_id = 1
        previous_step_id = None
        
        # STEP 1: Data Fetch
        category = analysis.get('category', 'ap')
        invoice_category = 'purchase' if category == 'ap' else 'sales'
        
        step = self._create_step(
            step_id,
            f"Fetch {'Purchase' if category == 'ap' else 'Sales'} Invoices",
            'InvoiceFetchNode',
            {'category': invoice_category}
        )
        workflow['steps'].append(step)
        previous_step_id = step['step_id']
        step_id += 1
        
        # STEP 2: Calculations
        calculations = analysis.get('calculations', [])
        
        if 'outstanding' in calculations:
            step = self._create_step(
                step_id,
                'Calculate Outstanding Amounts',
                'OutstandingCalculatorNode',
                {}
            )
            workflow['steps'].append(step)
            workflow['edges'].append({
                'source': previous_step_id,
                'target': step['step_id']
            })
            previous_step_id = step['step_id']
            step_id += 1
        
        if 'aging' in calculations:
            step = self._create_step(
                step_id,
                'Calculate Aging Days',
                'AgingCalculatorNode',
                {}
            )
            workflow['steps'].append(step)
            workflow['edges'].append({
                'source': previous_step_id,
                'target': step['step_id']
            })
            previous_step_id = step['step_id']
            step_id += 1
        
        if 'sla' in calculations:
            step = self._create_step(
                step_id,
                'Check SLA Breaches',
                'SLACheckerNode',
                {'sla_days': 30}
            )
            workflow['steps'].append(step)
            workflow['edges'].append({
                'source': previous_step_id,
                'target': step['step_id']
            })
            previous_step_id = step['step_id']
            step_id += 1
        
        # STEP 3: Aggregations
        aggregations = analysis.get('aggregations', [])
        filters = analysis.get('filters', {})
        
        # Filter
        if 'filter' in aggregations or filters:
            conditions = []
            
            if 'min_aging_days' in filters:
                conditions.append({
                    'field': 'aging_days',
                    'operator': '>=',
                    'value': filters['min_aging_days']
                })
            
            if conditions:
                step = self._create_step(
                    step_id,
                    'Apply Filters',
                    'FilterNode',
                    {'conditions': conditions}
                )
                workflow['steps'].append(step)
                workflow['edges'].append({
                    'source': previous_step_id,
                    'target': step['step_id']
                })
                previous_step_id = step['step_id']
                step_id += 1
        
        # Group
        if 'group' in aggregations:
            step = self._create_step(
                step_id,
                'Group by Aging Bucket',
                'GroupingNode',
                {'group_by': 'aging_bucket'}
            )
            workflow['steps'].append(step)
            workflow['edges'].append({
                'source': previous_step_id,
                'target': step['step_id']
            })
            previous_step_id = step['step_id']
            step_id += 1
        
        # Summary
        if 'summary' in aggregations:
            step = self._create_step(
                step_id,
                'Calculate Summary Statistics',
                'SummaryNode',
                {}
            )
            workflow['steps'].append(step)
            workflow['edges'].append({
                'source': previous_step_id,
                'target': step['step_id']
            })
            previous_step_id = step['step_id']
            step_id += 1
        
        # Sort
        if 'sort' in aggregations:
            step = self._create_step(
                step_id,
                'Sort Results',
                'SortNode',
                {'sort_by': [{'field': 'aging_days', 'order': 'desc'}]}
            )
            workflow['steps'].append(step)
            workflow['edges'].append({
                'source': previous_step_id,
                'target': step['step_id']
            })
            previous_step_id = step['step_id']
            step_id += 1
        
        # STEP 4: Output
        output_format = analysis.get('output_format', 'excel')
        output_map = {
            'excel': ('ExcelGeneratorNode', 'Generate Excel Report'),
            'pdf': ('PDFGeneratorNode', 'Generate PDF Report')
        }
        
        node_type, title = output_map.get(output_format, output_map['excel'])
        
        step = self._create_step(
            step_id,
            title,
            node_type,
            {}
        )
        workflow['steps'].append(step)
        workflow['edges'].append({
            'source': previous_step_id,
            'target': step['step_id']
        })
        
        return workflow
    
    def _create_step(self, step_number: int, title: str, node_type: str, params: Dict) -> Dict:
        """Create a workflow step"""
        return {
            'step_number': step_number,
            'step_id': f"step_{step_number}",
            'title': title,
            'node_type': node_type,
            'params': params,
            'status': 'pending'
        }
    
    def _validate_workflow(self, workflow: Dict) -> Dict[str, Any]:
        """Validate workflow structure"""
        errors = []
        
        if not workflow.get('steps'):
            errors.append("Workflow has no steps")
        
        # Check all steps have required fields
        for step in workflow.get('steps', []):
            if 'node_type' not in step:
                errors.append(f"Step {step.get('step_id')} missing node_type")
            if 'step_id' not in step:
                errors.append(f"Step missing step_id")
        
        # Check edges reference valid steps
        step_ids = {s['step_id'] for s in workflow.get('steps', [])}
        for edge in workflow.get('edges', []):
            if edge['source'] not in step_ids:
                errors.append(f"Edge references invalid source: {edge['source']}")
            if edge['target'] not in step_ids:
                errors.append(f"Edge references invalid target: {edge['target']}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }


# For testing
if __name__ == "__main__":
    planner = WorkflowPlannerAgent()
    result = planner.execute("Show me AP invoices older than 60 days grouped by aging bucket with totals in Excel")
    
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Steps: {len(result['workflow']['steps'])}")
        for step in result['workflow']['steps']:
            print(f"  {step['step_number']}. {step['title']} ({step['node_type']})")
    else:
        print(f"Error: {result.get('error')}")