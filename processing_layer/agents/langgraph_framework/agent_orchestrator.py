"""
LangGraph Agent Orchestrator
Central orchestrator for managing dynamic agent workflows using LangGraph
"""

from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
import asyncio
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from ..core.base_agent import BaseAgent
from .workflow_builder import WorkflowBuilder
from .dynamic_agent import DynamicAgent
from .agent_registry import LangGraphAgentRegistry
from shared.config.logging_config import get_logger
from shared.llm.groq_client import GroqClient


logger = get_logger(__name__)


class AgentOrchestrator:
    """
    LangGraph-based agent orchestrator
    
    Manages dynamic agent workflows with:
    - State management
    - Node orchestration
    - Error handling
    - Persistence
    - Multi-agent coordination
    """
    
    def __init__(self):
        self.registry = LangGraphAgentRegistry()
        self.workflows = {}  # Cache compiled workflows
        self.checkpointer = MemorySaver()
        self.active_sessions = {}  # Track active agent sessions
        
    def create_workflow(self, workflow_config: Dict[str, Any]) -> StateGraph:
        """
        Create a LangGraph workflow from configuration
        
        Args:
            workflow_config: Workflow definition with nodes, edges, and configuration
            
        Returns:
            Compiled StateGraph
        """
        builder = WorkflowBuilder()
        
        # Add nodes
        for node_config in workflow_config.get('nodes', []):
            node_type = node_config['type']
            node_name = node_config['name']
            node_params = node_config.get('params', {})
            # Defensive: node_name must be str
            if not isinstance(node_name, str):
                logger.error(f"Node name is not a string: {node_name} (type: {type(node_name)})")
                raise TypeError(f"Node name must be a string, got {type(node_name)}: {node_name}")
            if node_type == 'agent':
                agent_type = node_params.get('agent_type')
                try:
                    agent = self.registry.get_agent(agent_type)
                    # Check if agent has execute method (for BaseAgent) or run method (for BaseNode)
                    if hasattr(agent, 'execute'):
                        builder.add_node(node_name, agent.execute, node_type='agent', node_params=node_params)
                    elif hasattr(agent, 'run'):
                        builder.add_node(node_name, agent.run, node_type='agent', node_params=node_params)
                    else:
                        raise AttributeError(f"Agent {agent_type} has neither execute nor run method")
                except Exception as e:
                    # Fallback: instantiate node directly if not found in registry
                    if agent_type == 'InvoiceFetchAgent':
                        from processing_layer.workflows.nodes.data_nodes import InvoiceFetchNode
                        node_instance = InvoiceFetchNode()
                        builder.add_node(node_name, node_instance.run, node_type='agent', node_params=node_params)
                    elif agent_type == 'ExcelGeneratorNode':
                        # ExcelGeneratorNode is not available, use APAgingReportNode instead
                        from processing_layer.workflows.nodes.output_nodes.report_templates.ap_aging_node_fixed import APAgingReportNode
                        node_instance = APAgingReportNode()
                        builder.add_node(node_name, node_instance.run, node_type='agent', node_params=node_params)
                    else:
                        logger.error(f"Unknown agent or node type: {agent_type}")
                        raise
            elif node_type == 'tool':
                # Handle tool nodes
                tool_node = ToolNode([node_params['tool_function']])
                builder.add_node(node_name, tool_node, node_type='tool', node_params=node_params)
            elif node_type == 'function':
                # Handle custom function nodes
                func = node_params['function']
                builder.add_node(node_name, func, node_type='function', node_params=node_params)
        
        # Add edges
        for edge_config in workflow_config.get('edges', []):
            source = edge_config['source']
            target = edge_config['target']
            # Defensive: source/target must be str
            if not isinstance(source, str):
                logger.error(f"Edge source is not a string: {source} (type: {type(source)})")
                raise TypeError(f"Edge source must be a string, got {type(source)}: {source}")
            if not isinstance(target, str):
                logger.error(f"Edge target is not a string: {target} (type: {type(target)})")
                raise TypeError(f"Edge target must be a string, got {type(target)}: {target}")
            builder.add_edge(source, target)
        
        # Add conditional edges if specified
        for conditional_config in workflow_config.get('conditional_edges', []):
            source = conditional_config['source']
            condition = conditional_config['condition']
            if not isinstance(source, str):
                logger.error(f"Conditional edge source is not a string: {source} (type: {type(source)})")
                raise TypeError(f"Conditional edge source must be a string, got {type(source)}: {source}")
            builder.add_conditional_edges(source, condition)
        
        # Set entry and finish points
        entry_point = workflow_config.get('entry_point', START)
        finish_point = workflow_config.get('finish_point', END)
        
        builder.set_entry_point(entry_point)
        if finish_point != END:
            builder.add_edge(finish_point, END)
        
        # Compile workflow
        workflow = builder.compile(checkpointer=self.checkpointer)
        return workflow
    
    async def execute_workflow(
        self, 
        workflow_config: Dict[str, Any], 
        input_data: Any,
        session_id: Optional[str] = None,
        config: Optional[RunnableConfig] = None
    ) -> Dict[str, Any]:
        """
        Execute a LangGraph workflow
        
        Args:
            workflow_config: Workflow configuration
            input_data: Input data for the workflow
            session_id: Optional session ID for state persistence
            config: Optional LangGraph configuration
            
        Returns:
            Workflow execution result
        """
        try:
            # Get or create workflow
            workflow_key = self._get_workflow_key(workflow_config)
            if workflow_key not in self.workflows:
                workflow = self.create_workflow(workflow_config)
                self.workflows[workflow_key] = workflow
            else:
                workflow = self.workflows[workflow_key]
            
            # Prepare configuration
            run_config = config or {}
            if session_id:
                run_config['configurable'] = run_config.get('configurable', {})
                run_config['configurable']['thread_id'] = session_id
            
            # Execute workflow
            result = await workflow.ainvoke(input_data, config=run_config)
            
            # Log execution
            logger.info(f"Workflow executed successfully: {workflow_key}")
            
            return {
                'status': 'success',
                'workflow_key': workflow_key,
                'session_id': session_id,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'workflow_key': workflow_key if 'workflow_key' in locals() else None,
                'timestamp': datetime.now().isoformat()
            }
    
    async def execute_agent(
        self,
        agent_type: str,
        user_id: str,
        company_id: str,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a specific agent type with query and context
        
        This is the primary method called by API endpoints for:
        - Document upload processing
        - Report generation
        - Query execution
        
        Args:
            agent_type: Type of agent (ap_aging, ar_register, document_processing, etc.)
            user_id: User identifier
            company_id: Company identifier
            query: Query or instruction for the agent
            context: Additional context data
            session_id: Session ID for tracking
            params: Additional parameters for the agent
            
        Returns:
            Agent execution result with response, data, and metadata
        """
        try:
            session_id = session_id or str(asyncio.current_task().get_name() if asyncio.current_task() else '')
            context = context or {}
            params = params or {}
            
            # Track session
            self.active_sessions[session_id] = {
                'agent_type': agent_type,
                'user_id': user_id,
                'company_id': company_id,
                'start_time': datetime.now(),
                'status': 'executing'
            }
            
            # Log execution start
            logger.info(f"Executing agent: {agent_type} | Session: {session_id} | Query: {query}")
            
            # Create LLM-based dynamic workflow
            workflow_config = await self.create_dynamic_workflow(
                agent_type=agent_type,
                query=query,
                user_id=user_id,
                company_id=company_id,
                context=context,
                params=params
            )
            
            # Prepare input data for workflow
            input_data = {
                'query': query,
                'user_id': user_id,
                'company_id': company_id,
                'context': context,
                **params
            }
            
            # Execute workflow
            result = await self.execute_workflow(
                workflow_config=workflow_config,
                input_data=input_data,
                session_id=session_id
            )
            
            # Process result
            if result['status'] == 'success':
                workflow_result = result.get('result', {})
                
                # Update session status
                self.active_sessions[session_id]['status'] = 'completed'
                
                # Extract file path if present
                file_path = None
                if 'file_path' in workflow_result:
                    file_path = workflow_result['file_path']
                elif 'data' in workflow_result and isinstance(workflow_result['data'], dict) and 'file_path' in workflow_result['data']:
                    file_path = workflow_result['data']['file_path']
                elif isinstance(workflow_result, dict):
                    # Check if the result is a dict with file_path at top level
                    for key, value in workflow_result.items():
                        if isinstance(value, dict) and 'file_path' in value:
                            file_path = value['file_path']
                            break
                        elif isinstance(value, str) and key == 'file_path':
                            file_path = value
                            break
                
                return {
                    'status': 'success',
                    'agent_type': agent_type,
                    'response': workflow_result.get('response', 'Report generated successfully'),
                    'data': workflow_result.get('data', {}),
                    'file_path': file_path,
                    'document_id': workflow_result.get('document_id'),
                    'extracted_data': workflow_result.get('extracted_data', {}),
                    'suggested_actions': workflow_result.get('suggested_actions', []),
                    'processing_time': (datetime.now() - self.active_sessions[session_id]['start_time']).total_seconds(),
                    'metadata': {
                        'session_id': session_id,
                        'workflow_key': result.get('workflow_key'),
                        'agent_type': agent_type,
                        'timestamp': result.get('timestamp')
                    }
                }
            else:
                self.active_sessions[session_id]['status'] = 'failed'
                return {
                    'status': 'error',
                    'agent_type': agent_type,
                    'error': result.get('error', 'Unknown error'),
                    'processing_time': (datetime.now() - self.active_sessions[session_id]['start_time']).total_seconds(),
                    'metadata': {
                        'session_id': session_id,
                        'timestamp': result.get('timestamp')
                    }
                }
                
        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['status'] = 'failed'
            
            return {
                'status': 'error',
                'agent_type': agent_type,
                'error': str(e),
                'metadata': {
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                }
            }
    
    def create_dynamic_agent(
        self, 
        agent_config: Dict[str, Any]
    ) -> DynamicAgent:
        """
        Create a dynamic agent from configuration
        
        Args:
            agent_config: Agent configuration with capabilities and behavior
            
        Returns:
            DynamicAgent instance
        """
        agent = DynamicAgent(agent_config)
        
        # Register agent
        self.registry.register_agent(agent)
        
        return agent
    
    def get_agent_capabilities(self, agent_type: str) -> Dict[str, Any]:
        """Get capabilities of a specific agent type"""
        return self.registry.get_agent_capabilities(agent_type)
    
    def list_available_agents(self) -> List[Dict[str, Any]]:
        """List all available agents"""
        return self.registry.list_agents()
    
    async def create_dynamic_workflow(
        self,
        agent_type: str,
        query: str,
        user_id: str,
        company_id: str,
        context: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create LLM-based dynamic workflow using ReACT pattern
        
        Args:
            agent_type: Type of agent
            query: User query to analyze
            user_id: User identifier
            company_id: Company identifier
            context: Additional context
            params: Additional parameters
            
        Returns:
            Dynamic workflow configuration
        """
        try:
            # Use ReACT agent to plan and execute workflow
            workflow_config = await self._create_react_workflow(
                agent_type=agent_type,
                query=query,
                user_id=user_id,
                company_id=company_id,
                context=context,
                params=params
            )
            
            logger.info(f"Created ReACT workflow for query: {query}")
            return workflow_config
            
        except Exception as e:
            logger.error(f"Failed to create ReACT workflow: {e}")
            # Fallback to simple analysis
            required_steps = await self._analyze_query_for_steps(query, agent_type)
            return await self._build_dynamic_workflow(
                agent_type=agent_type,
                required_steps=required_steps,
                user_id=user_id,
                company_id=company_id,
                query=query,
                context=context,
                params=params
            )
    
    async def _create_react_workflow(
        self,
        agent_type: str,
        query: str,
        user_id: str,
        company_id: str,
        context: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create workflow using ReACT (Reasoning and Acting) pattern
        
        Args:
            agent_type: Type of agent
            query: User query
            user_id: User identifier
            company_id: Company identifier
            context: Additional context
            params: Additional parameters
            
        Returns:
            Dynamic workflow configuration
        """
        try:
            # Initialize Groq client
            groq_client = GroqClient()
            
            # Create ReACT prompt
            prompt = self._create_react_prompt(query, agent_type, user_id, company_id)
            
            # Execute ReACT agent using Groq
            response = groq_client.generate(prompt, temperature=0.1, json_mode=True)
            
            # Parse ReACT response to extract workflow
            workflow_config = self._parse_react_response(response)
            
            logger.info(f"ReACT agent created workflow for query: {query}")
            return workflow_config
            
        except Exception as e:
            logger.error(f"ReACT workflow creation failed: {e}")
            raise e
    
    def _create_react_prompt(self, query: str, agent_type: str, user_id: str, company_id: str) -> str:
        """
        Create ReACT prompt for workflow planning
        
        Args:
            query: User query
            agent_type: Agent type
            user_id: User identifier
            company_id: Company identifier
            
        Returns:
            ReACT prompt string
        """
        prompt = f"""
        You are an AI agent that plans and executes workflows using the ReACT (Reasoning and Acting) pattern.
        
        Your task is to analyze the user query and create an optimal workflow to fulfill the request.
        
        User Query: "{query}"
        Agent Type: {agent_type}
        User ID: {user_id}
        Company ID: {company_id}
        
        Available Actions:
        1. PLAN - Analyze the query and determine the optimal workflow steps
        2. SEARCH - Search for available nodes and their capabilities
        3. BUILD - Construct the workflow with nodes and edges
        4. VALIDATE - Validate the workflow for correctness
        
        Available Node Types:
        - BrandingLoaderNode: Load company branding configuration
        - InvoiceFetchNode: Fetch invoices from database
        - AgingCalculatorNode: Calculate aging buckets
        - APAgingReportNode: Generate AP aging Excel report
        - ARCollectionReportNode: Generate AR collection Excel report
        - BrandingNode: Apply company branding to reports
        - DocumentProcessingNode: Process uploaded documents
        - DataExtractionNode: Extract data from documents
        - ValidationNode: Validate extracted data
        - CalculationNode: Perform calculations
        - ReportGenerationNode: Generate reports
        
        Instructions:
        1. Use ReACT pattern: Think step by step
        2. PLAN: Analyze what needs to be done
        3. SEARCH: Find the best nodes for each step
        4. BUILD: Create the workflow with proper connections
        5. VALIDATE: Ensure the workflow is correct
        6. Return the final workflow configuration
        
        Example ReACT Execution:
        Thought: I need to generate an AP aging report
        Action: SEARCH
        Observation: Available nodes: InvoiceFetchNode, AgingCalculatorNode, APAgingReportNode, BrandingLoaderNode, BrandingNode
        Thought: I need to fetch invoices, calculate aging, generate report, and apply branding
        Action: BUILD
        Observation: Created workflow with nodes: [BrandingLoaderNode, InvoiceFetchNode, AgingCalculatorNode, APAgingReportNode, BrandingNode]
        Thought: The workflow looks correct
        Action: VALIDATE
        Observation: Workflow is valid
        Final Answer: {{"nodes": [...], "edges": [...], "entry_point": "BrandingLoaderNode", "finish_point": "BrandingNode"}}
        
        Now execute the ReACT pattern for the given query.
        """
        return prompt
    
    def _parse_react_response(self, response: str) -> Dict[str, Any]:
        """
        Parse ReACT response to extract workflow configuration
        
        Args:
            response: ReACT agent response
            
        Returns:
            Workflow configuration
        """
        import json
        import re
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                workflow_config = json.loads(json_match.group())
                if isinstance(workflow_config, dict) and 'nodes' in workflow_config:
                    return workflow_config
            
            # If JSON parsing fails, try to extract node information
            nodes = []
            edges = []
            
            # Extract node information
            node_pattern = r'"nodes":\s*\[(.*?)\]'
            node_match = re.search(node_pattern, response, re.DOTALL)
            if node_match:
                node_list = node_match.group(1)
                # Parse individual nodes
                node_names = re.findall(r'"([^"]+)"', node_list)
                for i, node_name in enumerate(node_names):
                    nodes.append({
                        'name': node_name.lower().replace(' ', '_'),
                        'type': 'agent',
                        'params': {
                            'agent_type': node_name,
                            'step_number': i + 1
                        }
                    })
            
            # Extract edges
            edge_pattern = r'"edges":\s*\[(.*?)\]'
            edge_match = re.search(edge_pattern, response, re.DOTALL)
            if edge_match:
                edge_list = edge_match.group(1)
                # Parse edges
                edge_pairs = re.findall(r'\{[^}]*"source":\s*"([^"]+)"[^}]*"target":\s*"([^"]+)"[^}]*\}', edge_list)
                for source, target in edge_pairs:
                    edges.append({
                        'source': source.lower().replace(' ', '_'),
                        'target': target.lower().replace(' ', '_')
                    })
            
            # Extract entry and finish points
            entry_match = re.search(r'"entry_point":\s*"([^"]+)"', response)
            finish_match = re.search(r'"finish_point":\s*"([^"]+)"', response)
            
            entry_point = entry_match.group(1).lower().replace(' ', '_') if entry_match else nodes[0]['name'] if nodes else 'start'
            finish_point = finish_match.group(1).lower().replace(' ', '_') if finish_match else nodes[-1]['name'] if nodes else 'end'
            
            return {
                'name': 'react_generated_workflow',
                'description': 'ReACT-generated workflow',
                'nodes': nodes,
                'edges': edges,
                'entry_point': entry_point,
                'finish_point': finish_point
            }
            
        except Exception as e:
            logger.error(f"Failed to parse ReACT response: {e}")
            # Return fallback workflow
            return {
                'name': 'fallback_workflow',
                'description': 'Fallback workflow due to parsing error',
                'nodes': [],
                'edges': [],
                'entry_point': 'start',
                'finish_point': 'end'
            }
    
    async def _analyze_query_for_steps(self, query: str, agent_type: str) -> List[str]:
        """
        Analyze query using LLM to determine required workflow steps
        
        Args:
            query: User query
            agent_type: Agent type
            
        Returns:
            List of required steps
        """
        try:
            # Initialize Groq client
            groq_client = GroqClient()
            
            # Create prompt for LLM-based query analysis
            prompt = self._create_query_analysis_prompt(query, agent_type)
            
            # Execute LLM call
            response = groq_client.generate(prompt, temperature=0.1, json_mode=True)
            
            # Parse LLM response to extract steps
            steps = self._parse_llm_response_for_steps(response)
            
            logger.info(f"LLM analyzed query '{query}' and determined steps: {steps}")
            return steps
            
        except Exception as e:
            logger.error(f"LLM query analysis failed: {e}")
            # Fallback to keyword-based analysis
            return self._analyze_query_for_steps_fallback(query, agent_type)
    
    def _create_query_analysis_prompt(self, query: str, agent_type: str) -> str:
        """
        Create prompt for LLM-based query analysis
        
        Args:
            query: User query
            agent_type: Agent type
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
        Analyze the following user query and determine the optimal workflow steps needed to fulfill it.

        User Query: "{query}"
        Agent Type: {agent_type}

        Available workflow steps:
        1. branding_loader - Load company branding configuration (colors, logo, etc.)
        2. data_fetch - Fetch data from database (invoices, documents, etc.)
        3. calculation - Perform calculations (aging buckets, totals, etc.)
        4. report_generation - Generate Excel/PDF reports
        5. branding - Apply company branding to reports
        6. document_processing - Process uploaded documents
        7. data_extraction - Extract data from processed documents
        8. validation - Validate extracted data

        Instructions:
        - Analyze the query to understand what the user wants
        - Determine which steps are necessary to fulfill the request
        - Consider the agent type to understand capabilities
        - Always include branding_loader and branding for report generation
        - Return the steps in the correct execution order
        - Use the exact step names listed above

        Examples:
        Query: "Generate AP aging report" -> ["branding_loader", "data_fetch", "calculation", "report_generation", "branding"]
        Query: "Process uploaded invoice" -> ["document_processing", "data_extraction", "validation"]
        Query: "Calculate outstanding amounts" -> ["data_fetch", "calculation"]

        Return ONLY the list of steps in JSON format:
        ["step1", "step2", "step3", ...]
        """
        return prompt
    
    def _parse_llm_response_for_steps(self, response: str) -> List[str]:
        """
        Parse LLM response to extract workflow steps
        
        Args:
            response: LLM response string
            
        Returns:
            List of workflow steps
        """
        import json
        import re
        
        try:
            # Try to parse as JSON first
            if response.strip().startswith('[') and response.strip().endswith(']'):
                steps = json.loads(response.strip())
                if isinstance(steps, list):
                    return steps
            
            # If not JSON, try to extract step names
            valid_steps = {
                'branding_loader', 'data_fetch', 'calculation', 
                'report_generation', 'branding', 'document_processing',
                'data_extraction', 'validation'
            }
            
            # Extract step names using regex
            step_pattern = r'\b(' + '|'.join(valid_steps) + r')\b'
            found_steps = re.findall(step_pattern, response.lower())
            
            # Remove duplicates while preserving order
            seen = set()
            unique_steps = []
            for step in found_steps:
                if step not in seen:
                    seen.add(step)
                    unique_steps.append(step)
            
            return unique_steps if unique_steps else self._get_default_steps(agent_type)
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._get_default_steps(agent_type)
    
    def _get_default_steps(self, agent_type: str) -> List[str]:
        """Get default steps based on agent type"""
        if agent_type == 'ap_aging':
            return ['branding_loader', 'data_fetch', 'calculation', 'report_generation', 'branding']
        elif agent_type == 'ar_aging':
            return ['branding_loader', 'data_fetch', 'calculation', 'report_generation', 'branding']
        elif agent_type == 'document_processing':
            return ['document_processing', 'data_extraction', 'validation']
        else:
            return ['data_fetch', 'processing', 'report_generation']
    
    def _analyze_query_for_steps_fallback(self, query: str, agent_type: str) -> List[str]:
        """
        Fallback keyword-based query analysis
        
        Args:
            query: User query
            agent_type: Agent type
            
        Returns:
            List of required steps
        """
        # Convert query to lowercase for analysis
        query_lower = query.lower()
        
        # Determine required steps based on query content
        required_steps = []
        
        # Always include branding for report generation
        if 'report' in query_lower or agent_type in ['ap_aging', 'ar_aging', 'ap_register', 'ar_register']:
            required_steps.append('branding_loader')
            required_steps.append('branding')
        
        # Add data fetching steps
        if any(keyword in query_lower for keyword in ['fetch', 'get', 'retrieve', 'invoices', 'data']):
            required_steps.append('data_fetch')
        
        # Add calculation steps
        if any(keyword in query_lower for keyword in ['calculate', 'aging', 'total', 'sum', 'aging buckets']):
            required_steps.append('calculation')
        
        # Add report generation steps
        if any(keyword in query_lower for keyword in ['generate', 'report', 'excel', 'output']):
            required_steps.append('report_generation')
        
        # Add document processing steps
        if any(keyword in query_lower for keyword in ['process', 'extract', 'parse', 'document', 'upload']):
            required_steps.append('document_processing')
        
        # If no specific steps identified, use default based on agent type
        if not required_steps:
            if agent_type == 'ap_aging':
                required_steps = ['branding_loader', 'data_fetch', 'calculation', 'report_generation', 'branding']
            elif agent_type == 'ar_aging':
                required_steps = ['branding_loader', 'data_fetch', 'calculation', 'report_generation', 'branding']
            elif agent_type == 'document_processing':
                required_steps = ['document_processing', 'data_extraction', 'validation']
            else:
                required_steps = ['data_fetch', 'processing', 'report_generation']
        
        return required_steps
    
    async def _build_dynamic_workflow(
        self,
        agent_type: str,
        required_steps: List[str],
        user_id: str,
        company_id: str,
        query: str,
        context: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build dynamic workflow based on required steps
        
        Args:
            agent_type: Agent type
            required_steps: List of required steps
            user_id: User identifier
            company_id: Company identifier
            query: User query
            context: Additional context
            params: Additional parameters
            
        Returns:
            Dynamic workflow configuration
        """
        nodes = []
        edges = []
        
        # Build nodes based on required steps
        for i, step in enumerate(required_steps):
            node_config = self._create_node_for_step(
                step=step,
                step_number=i + 1,
                user_id=user_id,
                company_id=company_id,
                query=query,
                context=context,
                params=params
            )
            nodes.append(node_config)
            
            # Create edges between consecutive steps
            if i > 0:
                edges.append({
                    'source': required_steps[i - 1],
                    'target': step
                })
        
        return {
            'name': f'dynamic_{agent_type}_workflow',
            'description': f'Dynamic workflow for {agent_type} based on query: {query}',
            'nodes': nodes,
            'edges': edges,
            'entry_point': required_steps[0] if required_steps else 'data_fetch',
            'finish_point': required_steps[-1] if required_steps else 'report_generation'
        }
    
    def _create_node_for_step(
        self,
        step: str,
        step_number: int,
        user_id: str,
        company_id: str,
        query: str,
        context: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create node configuration for a specific step
        
        Args:
            step: Step name
            step_number: Step number in workflow
            user_id: User identifier
            company_id: Company identifier
            query: User query
            context: Additional context
            params: Additional parameters
            
        Returns:
            Node configuration
        """
        if step == 'branding_loader':
            return {
                'name': 'branding_loader',
                'type': 'agent',
                'params': {
                    'agent_type': 'BrandingLoaderNode',
                    'user_id': user_id,
                    'company_id': company_id
                }
            }
        elif step == 'data_fetch':
            return {
                'name': 'data_fetch',
                'type': 'agent',
                'params': {
                    'agent_type': 'InvoiceFetchNode',
                    'user_id': user_id,
                    'company_id': company_id,
                    'filters': params.get('filters', {'category': 'purchase'})
                }
            }
        elif step == 'calculation':
            return {
                'name': 'calculation',
                'type': 'agent',
                'params': {
                    'agent_type': 'AgingCalculatorNode',
                    'user_id': user_id,
                    'company_id': company_id,
                    'as_of_date': params.get('as_of_date')
                }
            }
        elif step == 'report_generation':
            return {
                'name': 'report_generation',
                'type': 'agent',
                'params': {
                    'agent_type': 'APAgingReportNode',
                    'user_id': user_id,
                    'company_id': company_id,
                    'report_type': 'ap_aging'
                }
            }
        elif step == 'branding':
            return {
                'name': 'branding',
                'type': 'agent',
                'params': {
                    'agent_type': 'BrandingNode',
                    'user_id': user_id,
                    'company_id': company_id
                }
            }
        elif step == 'document_processing':
            return {
                'name': 'document_processing',
                'type': 'agent',
                'params': {
                    'agent_type': 'DocumentProcessingNode',
                    'user_id': user_id,
                    'company_id': company_id
                }
            }
        elif step == 'data_extraction':
            return {
                'name': 'data_extraction',
                'type': 'agent',
                'params': {
                    'agent_type': 'DataExtractionNode',
                    'user_id': user_id,
                    'company_id': company_id
                }
            }
        elif step == 'validation':
            return {
                'name': 'validation',
                'type': 'agent',
                'params': {
                    'agent_type': 'ValidationNode',
                    'user_id': user_id,
                    'company_id': company_id
                }
            }
        else:
            # Default node for unknown steps
            return {
                'name': step,
                'type': 'function',
                'params': {
                    'function': lambda x: x  # Pass-through function
                }
            }
    
    def create_report_workflow(
        self,
        report_type: str,
        user_id: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a specialized report generation workflow
        
        Args:
            report_type: Type of report (ap_aging, ar_aging, etc.)
            user_id: User identifier for context
            params: Report-specific parameters
            
        Returns:
            Workflow configuration
        """
        # Get agent capabilities for the report type
        agent_capabilities = self.get_agent_capabilities(f"{report_type}_agent")
        
        # Build workflow based on report type
        if report_type == 'ap_aging':
            workflow_config = self._build_ap_aging_workflow(user_id, params)
        elif report_type == 'ar_aging':
            workflow_config = self._build_ar_aging_workflow(user_id, params)
        elif report_type == 'ap_register':
            workflow_config = self._build_ap_register_workflow(user_id, params)
        elif report_type == 'ar_register':
            workflow_config = self._build_ar_register_workflow(user_id, params)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        return workflow_config
    
    def _build_ap_aging_workflow(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build AP Aging report workflow"""
        # Prepare invoice fetch params
        fetch_params = params.get('filters', {})
        if 'category' not in fetch_params:
            fetch_params['category'] = 'purchase'
        if 'company_id' not in fetch_params and params.get('company_id'):
            fetch_params['company_id'] = params.get('company_id')
        
        return {
            'name': 'ap_aging_report',
            'description': 'Generate AP Aging analysis report',
            'nodes': [
                {
                    'name': 'invoice_fetch',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'InvoiceFetchAgent',
                        'user_id': user_id,
                        **fetch_params  # Include category and company_id
                    }
                },
                {
                    'name': 'generate_excel',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'APAgingReportNode',
                        'user_id': user_id,
                        'company_id': params.get('company_id'),
                        'report_type': 'ap_aging'
                    }
                }
            ],
            'edges': [
                {'source': 'invoice_fetch', 'target': 'generate_excel'}
            ],
            'entry_point': 'invoice_fetch',
            'finish_point': 'generate_excel'
        }
    
    def _build_ar_aging_workflow(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build AR Aging report workflow"""
        return {
            'name': 'ar_aging_report',
            'description': 'Generate AR Aging analysis report',
            'nodes': [
                {
                    'name': 'invoice_fetch',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'InvoiceFetchAgent',
                        'user_id': user_id,
                        'filters': {'category': 'sales'}
                    }
                },
                {
                    'name': 'outstanding_calc',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'OutstandingCalculatorAgent'
                    }
                },
                {
                    'name': 'aging_calc',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'AgingCalculatorAgent',
                        'as_of_date': params.get('as_of_date')
                    }
                },
                {
                    'name': 'filter_unpaid',
                    'type': 'function',
                    'params': {
                        'function': self._filter_unpaid_invoices
                    }
                },
                {
                    'name': 'group_by_bucket',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'GroupingAgent',
                        'group_by': 'aging_bucket'
                    }
                },
                {
                    'name': 'generate_summary',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'SummaryAgent'
                    }
                },
                {
                    'name': 'generate_excel',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'ExcelGeneratorAgent',
                        'user_id': user_id,
                        'report_type': 'ar_aging'
                    }
                }
            ],
            'edges': [
                {'source': 'invoice_fetch', 'target': 'outstanding_calc'},
                {'source': 'outstanding_calc', 'target': 'aging_calc'},
                {'source': 'aging_calc', 'target': 'filter_unpaid'},
                {'source': 'filter_unpaid', 'target': 'group_by_bucket'},
                {'source': 'group_by_bucket', 'target': 'generate_summary'},
                {'source': 'generate_summary', 'target': 'generate_excel'}
            ],
            'entry_point': 'invoice_fetch',
            'finish_point': 'generate_excel'
        }
    
    def _build_ap_register_workflow(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build AP Register report workflow"""
        return {
            'name': 'ap_register_report',
            'description': 'Generate AP Register report',
            'nodes': [
                {
                    'name': 'invoice_fetch',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'InvoiceFetchAgent',
                        'user_id': user_id,
                        'filters': params.get('filters', {})
                    }
                },
                {
                    'name': 'calculate_outstanding',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'OutstandingCalculatorAgent'
                    }
                },
                {
                    'name': 'generate_summary',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'SummaryAgent'
                    }
                },
                {
                    'name': 'generate_excel',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'ExcelGeneratorAgent',
                        'user_id': user_id,
                        'report_type': 'ap_register'
                    }
                }
            ],
            'edges': [
                {'source': 'invoice_fetch', 'target': 'calculate_outstanding'},
                {'source': 'calculate_outstanding', 'target': 'generate_summary'},
                {'source': 'generate_summary', 'target': 'generate_excel'}
            ],
            'entry_point': 'invoice_fetch',
            'finish_point': 'generate_excel'
        }
    
    def _build_ar_register_workflow(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build AR Register report workflow"""
        return {
            'name': 'ar_register_report',
            'description': 'Generate AR Register report',
            'nodes': [
                {
                    'name': 'invoice_fetch',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'InvoiceFetchAgent',
                        'user_id': user_id,
                        'filters': {'category': 'sales'}
                    }
                },
                {
                    'name': 'calculate_outstanding',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'OutstandingCalculatorAgent'
                    }
                },
                {
                    'name': 'generate_summary',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'SummaryAgent'
                    }
                },
                {
                    'name': 'generate_excel',
                    'type': 'agent',
                    'params': {
                        'agent_type': 'ExcelGeneratorAgent',
                        'user_id': user_id,
                        'report_type': 'ar_register'
                    }
                }
            ],
            'edges': [
                {'source': 'invoice_fetch', 'target': 'calculate_outstanding'},
                {'source': 'calculate_outstanding', 'target': 'generate_summary'},
                {'source': 'generate_summary', 'target': 'generate_excel'}
            ],
            'entry_point': 'invoice_fetch',
            'finish_point': 'generate_excel'
        }
    
    def _filter_unpaid_invoices(self, invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter to unpaid/partially paid invoices"""
        return [
            inv for inv in invoices 
            if inv.get('status') in ['Unpaid', 'Partially Paid']
        ]
    
    def _get_workflow_key(self, workflow_config: Dict[str, Any]) -> str:
        """Generate a unique key for caching workflows"""
        import hashlib
        import json
        try:
            # Use json.dumps to serialize dicts, sort_keys for consistency
            config_str = json.dumps(workflow_config, sort_keys=True, default=str)
            return hashlib.md5(config_str.encode()).hexdigest()
        except (TypeError, ValueError) as e:
            # Fallback for unhashable types
            logger.warning(f"Failed to serialize workflow config: {e}")
            # Create a simple hash based on agent type and nodes
            agent_types = []
            for node in workflow_config.get('nodes', []):
                if node.get('type') == 'agent':
                    agent_types.append(node.get('params', {}).get('agent_type', ''))
            
            fallback_str = f"{workflow_config.get('name', '')}_{workflow_config.get('description', '')}_{agent_types}"
            return hashlib.md5(fallback_str.encode()).hexdigest()
    
    def cleanup(self):
        """Clean up resources"""
        self.workflows.clear()
        self.active_sessions.clear()