"""
Enhanced LLM Workflow Generator
Phase 3.2: Advanced LLM Workflow Generation Engine
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import re

from shared.llm.groq_client import GroqClient
from shared.config.logging_config import get_logger
from processing_layer.workflows.llm_workflow_generator import LLMWorkflowGenerator


logger = get_logger(__name__)


class WorkflowComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    ADVANCED = "advanced"


class QueryType(Enum):
    REPORT_GENERATION = "report_generation"
    DATA_ANALYSIS = "data_analysis"
    CUSTOM_CALCULATION = "custom_calculation"
    MULTI_STEP_PROCESS = "multi_step_process"


@dataclass
class QueryAnalysis:
    """Enhanced query analysis result"""
    query_type: QueryType
    report_type: str
    data_source: str
    complexity: WorkflowComplexity
    key_requirements: List[str]
    time_range: str
    filters: Dict[str, Any]
    aggregations: List[str]
    custom_calculations: List[str]
    output_format: str
    confidence_score: float
    suggested_nodes: List[str]


@dataclass
class WorkflowOptimization:
    """Workflow optimization suggestions"""
    performance_improvements: List[str]
    node_optimizations: List[str]
    caching_opportunities: List[str]
    parallel_execution_opportunities: List[str]
    memory_optimizations: List[str]


class EnhancedLLMWorkflowGenerator(LLMWorkflowGenerator):
    """
    Enhanced LLM Workflow Generator with advanced capabilities
    """
    
    def __init__(self):
        super().__init__()
        self.query_cache = {}
        self.optimization_cache = {}
        self.node_performance_metrics = {}
        
    async def generate_workflow_advanced(self, query: str, company_id: str, user_id: str) -> Dict[str, Any]:
        """
        Generate advanced workflow with enhanced analysis and optimization
        
        Args:
            query: User's natural language query
            company_id: Company identifier
            user_id: User identifier
            
        Returns:
            Enhanced workflow definition with optimization metadata
        """
        try:
            # Step 1: Enhanced query analysis
            analysis = await self._analyze_query_advanced(query, company_id)
            
            # Step 2: Generate workflow structure
            workflow_definition = self._generate_workflow_structure_advanced(analysis, query)
            
            # Step 3: Optimize workflow
            optimized_workflow = await self._optimize_workflow(workflow_definition, analysis)
            
            # Step 4: Validate and enhance
            validated_workflow = self._validate_and_enhance_workflow(optimized_workflow, analysis)
            
            # Step 5: Add performance metadata
            enhanced_workflow = self._add_performance_metadata(validated_workflow, analysis)
            
            logger.info(f"Generated advanced workflow for query: {query}")
            return enhanced_workflow
            
        except Exception as e:
            logger.error(f"Failed to generate advanced workflow: {e}")
            return await self._create_fallback_workflow_advanced(query, company_id, user_id)
    
    async def _analyze_query_advanced(self, query: str, company_id: str) -> QueryAnalysis:
        """Enhanced query analysis with detailed requirements extraction"""
        
        # Check cache first
        cache_key = f"{query}_{company_id}"
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        try:
            # Enhanced LLM analysis prompt
            prompt = f"""
            Perform detailed analysis of this financial query:

            Query: "{query}"
            
            Please analyze and extract the following information in JSON format:
            
            1. query_type: "report_generation", "data_analysis", "custom_calculation", or "multi_step_process"
            2. report_type: Specific report type (ap_aging, ar_register, dso, etc.)
            3. data_source: Primary data source (vendor_invoices, customer_invoices, payment_transactions, etc.)
            4. complexity: "simple", "medium", "complex", or "advanced"
            5. key_requirements: List of specific requirements and features needed
            6. time_range: Time range specification (last_30_days, last_90_days, custom, all_time)
            7. filters: Dictionary of filter conditions (status, amount_range, entity_ids, etc.)
            8. aggregations: List of aggregation operations needed (group_by, sum, avg, count, etc.)
            9. custom_calculations: List of custom calculations needed (aging_days, outstanding_percentage, etc.)
            10. output_format: Desired output format (excel, pdf, dashboard, etc.)
            11. confidence_score: Confidence in analysis (0.0 to 1.0)
            12. suggested_nodes: List of suggested workflow nodes
            
            Also identify:
            - Any implicit requirements
            - Potential performance bottlenecks
            - Required data transformations
            - Expected output size
            
            Return ONLY valid JSON, no explanation.
            """
            
            response = self.llm.generate(prompt)
            
            # Clean the response to extract JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]  # Remove ```json
            if response.endswith('```'):
                response = response[:-3]  # Remove ```
            
            # Try to parse JSON with multiple fallback strategies
            analysis_data = self._parse_llm_response(response)
            
            # Create QueryAnalysis object with proper defaults
            query_type_value = analysis_data.get('query_type', 'report_generation')
            if query_type_value is None:
                query_type_value = 'report_generation'
            
            report_type_value = analysis_data.get('report_type', 'custom')
            if report_type_value is None:
                report_type_value = 'custom'
            
            data_source_value = analysis_data.get('data_source', 'vendor_invoices')
            if data_source_value is None:
                data_source_value = 'vendor_invoices'
            
            complexity_value = analysis_data.get('complexity', 'medium')
            if complexity_value is None:
                complexity_value = 'medium'
            
            analysis = QueryAnalysis(
                query_type=QueryType(query_type_value),
                report_type=report_type_value,
                data_source=data_source_value,
                complexity=WorkflowComplexity(complexity_value),
                key_requirements=analysis_data.get('key_requirements', []),
                time_range=analysis_data.get('time_range', 'all_time'),
                filters=analysis_data.get('filters', {}),
                aggregations=analysis_data.get('aggregations', []),
                custom_calculations=analysis_data.get('custom_calculations', []),
                output_format=analysis_data.get('output_format', 'excel'),
                confidence_score=analysis_data.get('confidence_score', 0.8),
                suggested_nodes=analysis_data.get('suggested_nodes', [])
            )
            
            # Cache the result
            self.query_cache[cache_key] = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return self._get_default_analysis_advanced(query)
    
    def _get_default_analysis_advanced(self, query: str) -> QueryAnalysis:
        """Fallback analysis for query"""
        query_lower = query.lower()
        
        # Extract time range
        time_range = "all_time"
        if "last 30 days" in query_lower or "past month" in query_lower:
            time_range = "last_30_days"
        elif "last 90 days" in query_lower or "past quarter" in query_lower:
            time_range = "last_90_days"
        elif "last year" in query_lower or "past year" in query_lower:
            time_range = "last_year"
        
        # Extract filters
        filters = {}
        if "overdue" in query_lower:
            filters['status'] = ['overdue']
        if "paid" in query_lower:
            filters['status'] = ['paid']
        if "unpaid" in query_lower or "outstanding" in query_lower:
            filters['status'] = ['unpaid', 'partial']
        
        # Extract aggregations
        aggregations = []
        if "group" in query_lower or "by" in query_lower:
            aggregations.append('group_by')
        if "sum" in query_lower or "total" in query_lower:
            aggregations.append('sum')
        if "average" in query_lower or "avg" in query_lower:
            aggregations.append('avg')
        
        return QueryAnalysis(
            query_type=QueryType.REPORT_GENERATION,
            report_type='custom',
            data_source='vendor_invoices',
            complexity=WorkflowComplexity.MEDIUM,
            key_requirements=['data_fetch', 'filtering', 'aggregation'],
            time_range=time_range,
            filters=filters,
            aggregations=aggregations,
            custom_calculations=[],
            output_format='excel',
            confidence_score=0.6,
            suggested_nodes=['InvoiceFetchNode', 'FilterNode', 'GroupingNode', 'SummaryNode']
        )
    
    def _generate_workflow_structure_advanced(self, analysis: QueryAnalysis, query: str) -> Dict[str, Any]:
        """Generate advanced workflow structure based on detailed analysis"""
        
        nodes = []
        step_number = 1
        
        # 1. Data Fetch Node with advanced parameters
        fetch_node = self._create_enhanced_fetch_node(analysis, step_number)
        nodes.append(fetch_node)
        step_number += 1
        
        # 2. Preprocessing nodes based on requirements
        preprocessing_nodes = self._create_preprocessing_nodes(analysis, step_number)
        nodes.extend(preprocessing_nodes)
        step_number += len(preprocessing_nodes)
        
        # 3. Filtering nodes
        filter_nodes = self._create_filter_nodes(analysis, step_number)
        nodes.extend(filter_nodes)
        step_number += len(filter_nodes)
        
        # 4. Custom calculations
        calculation_nodes = self._create_calculation_nodes(analysis, step_number)
        nodes.extend(calculation_nodes)
        step_number += len(calculation_nodes)
        
        # 5. Aggregation nodes
        aggregation_nodes = self._create_aggregation_nodes(analysis, step_number)
        nodes.extend(aggregation_nodes)
        step_number += len(aggregation_nodes)
        
        # 6. Output generation
        output_nodes = self._create_output_nodes(analysis, step_number)
        nodes.extend(output_nodes)
        step_number += len(output_nodes)
        
        # 7. Post-processing and optimization
        post_processing_nodes = self._create_post_processing_nodes(analysis, step_number)
        nodes.extend(post_processing_nodes)
        
        # Generate edges
        edges = self._generate_edges_advanced(nodes)
        
        # Convert QueryAnalysis to dict with proper enum serialization
        analysis_dict = {
            'query_type': analysis.query_type.value,
            'report_type': analysis.report_type,
            'data_source': analysis.data_source,
            'complexity': analysis.complexity.value,
            'key_requirements': analysis.key_requirements,
            'time_range': analysis.time_range,
            'filters': analysis.filters,
            'aggregations': analysis.aggregations,
            'custom_calculations': analysis.custom_calculations,
            'output_format': analysis.output_format,
            'confidence_score': analysis.confidence_score,
            'suggested_nodes': analysis.suggested_nodes
        }
        
        workflow_definition = {
            'edges': edges,
            'nodes': nodes,
            'metadata': {
                'analysis': analysis_dict,
                'generated_at': datetime.now().isoformat(),
                'query': query,
                'optimization_level': 'advanced',
                'estimated_complexity': analysis.complexity.value,
                'estimated_execution_time': self._estimate_execution_time(analysis)
            }
        }
        
        return workflow_definition
    
    def _create_enhanced_fetch_node(self, analysis: QueryAnalysis, step_number: int) -> Dict[str, Any]:
        """Create enhanced data fetch node with advanced parameters"""
        
        # Determine category based on data source
        category = 'purchase' if 'vendor' in analysis.data_source else 'sales'
        
        # Build advanced parameters
        params = {
            'category': category,
            'date_range': analysis.time_range,
            'status_filter': analysis.filters.get('status', ['all']),
            'include_details': True,
            'batch_size': 1000,
            'parallel_fetch': True
        }
        
        # Add specific filters
        if 'amount_min' in analysis.filters:
            params['amount_min'] = analysis.filters['amount_min']
        if 'amount_max' in analysis.filters:
            params['amount_max'] = analysis.filters['amount_max']
        if 'entity_ids' in analysis.filters:
            params['entity_ids'] = analysis.filters['entity_ids']
        
        return {
            'title': f"Enhanced {analysis.data_source.replace('_', ' ').title()} Fetch",
            'params': params,
            'status': 'pending',
            'step_id': f'step_{step_number}',
            'node_type': 'EnhancedInvoiceFetchNode',
            'step_number': step_number,
            'description': f'Fetch {analysis.data_source} with advanced filtering and optimization',
            'performance_tuning': {
                'batch_size': 1000,
                'parallel_fetch': True,
                'index_optimization': True,
                'memory_efficient': True
            }
        }
    
    def _create_preprocessing_nodes(self, analysis: QueryAnalysis, step_number: int) -> List[Dict[str, Any]]:
        """Create preprocessing nodes for data cleaning and transformation"""
        
        nodes = []
        
        # Data cleaning node
        if any(req in analysis.key_requirements for req in ['clean_data', 'validate_data', 'handle_missing']):
            cleaning_node = {
                'title': 'Data Quality Validation',
                'params': {
                    'validation_rules': ['required_fields', 'data_types', 'range_checks'],
                    'handle_missing': 'impute_or_remove',
                    'duplicate_detection': True
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'DataQualityNode',
                'step_number': step_number,
                'description': 'Validate and clean data quality'
            }
            nodes.append(cleaning_node)
            step_number += 1
        
        # Currency conversion node
        if 'currency_conversion' in analysis.key_requirements:
            currency_node = {
                'title': 'Currency Conversion',
                'params': {
                    'target_currency': 'INR',
                    'exchange_rate_source': 'api',
                    'conversion_method': 'historical_rates'
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'CurrencyConversionNode',
                'step_number': step_number,
                'description': 'Convert amounts to target currency'
            }
            nodes.append(currency_node)
            step_number += 1
        
        return nodes
    
    def _create_filter_nodes(self, analysis: QueryAnalysis, step_number: int) -> List[Dict[str, Any]]:
        """Create filtering nodes based on analysis"""
        
        nodes = []
        
        # Status filter
        if 'status' in analysis.filters:
            status_filter = {
                'title': 'Status Filtering',
                'params': {
                    'field': 'payment_status',
                    'values': analysis.filters['status'],
                    'operator': 'in'
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'StatusFilterNode',
                'step_number': step_number,
                'description': f'Filter by status: {analysis.filters["status"]}'
            }
            nodes.append(status_filter)
            step_number += 1
        
        # Amount range filter
        if 'amount_min' in analysis.filters or 'amount_max' in analysis.filters:
            amount_filter = {
                'title': 'Amount Range Filtering',
                'params': {
                    'field': 'inr_amount',
                    'min_value': analysis.filters.get('amount_min'),
                    'max_value': analysis.filters.get('amount_max'),
                    'operator': 'between'
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'AmountFilterNode',
                'step_number': step_number,
                'description': 'Filter by amount range'
            }
            nodes.append(amount_filter)
            step_number += 1
        
        return nodes
    
    def _create_calculation_nodes(self, analysis: QueryAnalysis, step_number: int) -> List[Dict[str, Any]]:
        """Create custom calculation nodes"""
        
        nodes = []
        
        # Aging calculation
        if 'aging_days' in analysis.custom_calculations:
            aging_node = {
                'title': 'Aging Days Calculation',
                'params': {
                    'base_date_field': 'invoice_date',
                    'reference_date': 'auto',
                    'include_weekends': True,
                    'bucket_definition': ['0-30', '31-60', '61-90', '90+']
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'AgingCalculationNode',
                'step_number': step_number,
                'description': 'Calculate aging days and buckets'
            }
            nodes.append(aging_node)
            step_number += 1
        
        # Outstanding percentage
        if 'outstanding_percentage' in analysis.custom_calculations:
            percentage_node = {
                'title': 'Outstanding Percentage Calculation',
                'params': {
                    'numerator_field': 'outstanding_amount',
                    'denominator_field': 'total_amount',
                    'round_decimals': 2
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'PercentageCalculationNode',
                'step_number': step_number,
                'description': 'Calculate outstanding percentage'
            }
            nodes.append(percentage_node)
            step_number += 1
        
        return nodes
    
    def _create_aggregation_nodes(self, analysis: QueryAnalysis, step_number: int) -> List[Dict[str, Any]]:
        """Create aggregation nodes based on requirements"""
        
        nodes = []
        
        # Grouping
        if 'group_by' in analysis.aggregations:
            group_node = {
                'title': 'Advanced Grouping',
                'params': {
                    'group_by_fields': self._extract_group_fields(analysis),
                    'aggregation_functions': self._extract_aggregation_functions(analysis),
                    'sort_results': True,
                    'include_subtotals': True
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'AdvancedGroupingNode',
                'step_number': step_number,
                'description': 'Perform advanced grouping with aggregations'
            }
            nodes.append(group_node)
            step_number += 1
        
        # Summary statistics
        if any(func in analysis.aggregations for func in ['sum', 'avg', 'count']):
            summary_node = {
                'title': 'Summary Statistics',
                'params': {
                    'aggregation_functions': self._extract_aggregation_functions(analysis),
                    'include_percentages': True,
                    'include_trends': True
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'SummaryStatisticsNode',
                'step_number': step_number,
                'description': 'Calculate summary statistics and trends'
            }
            nodes.append(summary_node)
            step_number += 1
        
        return nodes
    
    def _create_output_nodes(self, analysis: QueryAnalysis, step_number: int) -> List[Dict[str, Any]]:
        """Create output generation nodes"""
        
        nodes = []
        
        # Report generation
        report_node = {
            'title': f'{analysis.report_type.replace("_", " ").title()} Report Generation',
            'params': {
                'output_format': analysis.output_format,
                'include_charts': True,
                'include_summary': True,
                'include_details': True,
                'branding': 'auto'
            },
            'status': 'pending',
            'step_id': f'step_{step_number}',
            'node_type': 'EnhancedReportGeneratorNode',
            'step_number': step_number,
            'description': f'Generate {analysis.report_type} report'
        }
        nodes.append(report_node)
        step_number += 1
        
        # Branding application
        if analysis.output_format in ['excel', 'pdf']:
            branding_node = {
                'title': 'Company Branding Application',
                'params': {
                    'company_id': 'auto',
                    'include_logo': True,
                    'primary_color': 'auto',
                    'secondary_color': 'auto',
                    'font_family': 'auto'
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'BrandingApplicationNode',
                'step_number': step_number,
                'description': 'Apply company branding to output'
            }
            nodes.append(branding_node)
            step_number += 1
        
        return nodes
    
    def _create_post_processing_nodes(self, analysis: QueryAnalysis, step_number: int) -> List[Dict[str, Any]]:
        """Create post-processing nodes for final optimization"""
        
        nodes = []
        
        # Performance optimization
        if analysis.complexity in [WorkflowComplexity.COMPLEX, WorkflowComplexity.ADVANCED]:
            optimization_node = {
                'title': 'Performance Optimization',
                'params': {
                    'memory_cleanup': True,
                    'cache_results': True,
                    'compress_output': True,
                    'optimize_for_size': True
                },
                'status': 'pending',
                'step_id': f'step_{step_number}',
                'node_type': 'PerformanceOptimizationNode',
                'step_number': step_number,
                'description': 'Optimize workflow performance and output size'
            }
            nodes.append(optimization_node)
            step_number += 1
        
        return nodes
    
    def _generate_edges_advanced(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate optimized edges with parallel execution opportunities"""
        
        edges = []
        
        # Create sequential edges by default
        for i in range(len(nodes) - 1):
            source_node = nodes[i]
            target_node = nodes[i + 1]
            
            edge = {
                'source': source_node['step_id'],
                'target': target_node['step_id'],
                'type': 'sequential'
            }
            edges.append(edge)
        
        # Identify parallel execution opportunities
        parallel_edges = self._identify_parallel_execution(nodes)
        edges.extend(parallel_edges)
        
        return edges
    
    def _identify_parallel_execution(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify nodes that can be executed in parallel"""
        
        parallel_edges = []
        
        # Look for independent nodes that can run in parallel
        for i, node in enumerate(nodes):
            if node['node_type'] in ['DataQualityNode', 'CurrencyConversionNode']:
                # These nodes can potentially run in parallel with others
                for j in range(i + 1, len(nodes)):
                    target_node = nodes[j]
                    if target_node['node_type'] not in ['DataQualityNode', 'CurrencyConversionNode']:
                        # Create parallel edge
                        parallel_edge = {
                            'source': node['step_id'],
                            'target': target_node['step_id'],
                            'type': 'parallel',
                            'condition': 'data_ready'
                        }
                        parallel_edges.append(parallel_edge)
                        break
        
        return parallel_edges
    
    async def _optimize_workflow(self, workflow_definition: Dict[str, Any], analysis: QueryAnalysis) -> Dict[str, Any]:
        """Optimize workflow for performance and efficiency"""
        
        # Check cache first
        cache_key = f"optimization_{analysis.report_type}_{analysis.complexity.value}"
        if cache_key in self.optimization_cache:
            return self.optimization_cache[cache_key]
        
        try:
            # Performance optimization suggestions
            optimization_suggestions = await self._get_optimization_suggestions(workflow_definition, analysis)
            
            # Apply optimizations
            optimized_workflow = self._apply_optimizations(workflow_definition, optimization_suggestions)
            
            # Cache the result
            self.optimization_cache[cache_key] = optimized_workflow
            
            return optimized_workflow
            
        except Exception as e:
            logger.error(f"Workflow optimization failed: {e}")
            return workflow_definition
    
    async def _get_optimization_suggestions(self, workflow_definition: Dict[str, Any], analysis: QueryAnalysis) -> WorkflowOptimization:
        """Get optimization suggestions from LLM with robust fallback handling"""
        
        # Convert analysis to dict with proper enum serialization
        analysis_dict = {
            'query_type': analysis.query_type.value,
            'report_type': analysis.report_type,
            'data_source': analysis.data_source,
            'complexity': analysis.complexity.value,
            'key_requirements': analysis.key_requirements,
            'time_range': analysis.time_range,
            'filters': analysis.filters,
            'aggregations': analysis.aggregations,
            'custom_calculations': analysis.custom_calculations,
            'output_format': analysis.output_format,
            'confidence_score': analysis.confidence_score,
            'suggested_nodes': analysis.suggested_nodes
        }
        
        prompt = f"""
        Analyze this workflow for optimization opportunities:

        Workflow: {json.dumps(workflow_definition, indent=2)}
        Analysis: {json.dumps(analysis_dict, indent=2)}

        Please provide optimization suggestions in JSON format:
        1. performance_improvements: List of performance improvements
        2. node_optimizations: List of specific node optimizations
        3. caching_opportunities: List of caching opportunities
        4. parallel_execution_opportunities: List of parallel execution opportunities
        5. memory_optimizations: List of memory optimizations

        Return ONLY valid JSON, no explanation.
        """
        
        try:
            response = self.llm.generate(prompt)
            
            # Clean the response to extract JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]  # Remove ```json
            if response.endswith('```'):
                response = response[:-3]  # Remove ```
            
            # Try to parse JSON with multiple fallback strategies
            suggestions_data = self._parse_llm_response(response)
            
            return WorkflowOptimization(
                performance_improvements=suggestions_data.get('performance_improvements', []),
                node_optimizations=suggestions_data.get('node_optimizations', []),
                caching_opportunities=suggestions_data.get('caching_opportunities', []),
                parallel_execution_opportunities=suggestions_data.get('parallel_execution_opportunities', []),
                memory_optimizations=suggestions_data.get('memory_optimizations', [])
            )
            
        except Exception as e:
            logger.warning(f"Optimization suggestions failed, using defaults: {e}")
            # Return default optimization suggestions
            return WorkflowOptimization(
                performance_improvements=['batch_processing', 'parallel_processing'],
                node_optimizations=['database_optimization'],
                caching_opportunities=['result_caching'],
                parallel_execution_opportunities=['data_fetch', 'calculation'],
                memory_optimizations=['memory_cleanup', 'compress_output']
            )
    
    def _apply_optimizations(self, workflow_definition: Dict[str, Any], optimization: WorkflowOptimization) -> Dict[str, Any]:
        """Apply optimization suggestions to workflow"""
        
        # Apply performance improvements
        for improvement in optimization.performance_improvements:
            workflow_definition = self._apply_performance_improvement(workflow_definition, improvement)
        
        # Apply node optimizations
        for node_optimization in optimization.node_optimizations:
            workflow_definition = self._apply_node_optimization(workflow_definition, node_optimization)
        
        # Add caching opportunities
        for cache_opportunity in optimization.caching_opportunities:
            workflow_definition = self._add_caching(workflow_definition, cache_opportunity)
        
        return workflow_definition
    
    def _apply_performance_improvement(self, workflow_definition: Dict[str, Any], improvement: str) -> Dict[str, Any]:
        """Apply specific performance improvement"""
        
        # Example: Add batch processing
        if "batch_processing" in improvement:
            for node in workflow_definition['nodes']:
                if node['node_type'] in ['InvoiceFetchNode', 'EnhancedInvoiceFetchNode']:
                    node['params']['batch_size'] = 2000
                    node['performance_tuning']['batch_size'] = 2000
        
        # Example: Enable parallel processing
        if "parallel_processing" in improvement:
            for node in workflow_definition['nodes']:
                if node['node_type'] in ['InvoiceFetchNode', 'EnhancedInvoiceFetchNode']:
                    node['params']['parallel_fetch'] = True
                    node['performance_tuning']['parallel_fetch'] = True
        
        return workflow_definition
    
    def _apply_node_optimization(self, workflow_definition: Dict[str, Any], optimization: str) -> Dict[str, Any]:
        """Apply specific node optimization"""
        
        # Example: Optimize database queries
        if "database_optimization" in optimization:
            for node in workflow_definition['nodes']:
                if node['node_type'] in ['InvoiceFetchNode', 'EnhancedInvoiceFetchNode']:
                    node['params']['use_index'] = True
                    node['params']['limit_results'] = 10000
        
        return workflow_definition
    
    def _add_caching(self, workflow_definition: Dict[str, Any], cache_opportunity: str) -> Dict[str, Any]:
        """Add caching to workflow"""
        
        # Example: Add result caching
        if "result_caching" in cache_opportunity:
            for node in workflow_definition['nodes']:
                if node['node_type'] in ['SummaryStatisticsNode', 'AdvancedGroupingNode']:
                    node['params']['cache_result'] = True
                    node['params']['cache_duration'] = 3600  # 1 hour
        
        return workflow_definition
    
    def _validate_and_enhance_workflow(self, workflow_definition: Dict[str, Any], analysis: QueryAnalysis) -> Dict[str, Any]:
        """Validate and enhance workflow with additional metadata"""
        
        # Validate workflow structure
        validation_result = self._validate_workflow_structure(workflow_definition)
        
        if not validation_result['valid']:
            logger.warning(f"Workflow validation issues: {validation_result['warnings']}")
        
        # Enhance with additional metadata
        workflow_definition['metadata']['validation'] = validation_result
        workflow_definition['metadata']['enhancement_level'] = 'advanced'
        workflow_definition['metadata']['optimization_applied'] = True
        
        return workflow_definition
    
    def _validate_workflow_structure(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Validate workflow structure and return validation results"""
        
        warnings = []
        
        # Check for required nodes
        node_types = [node['node_type'] for node in workflow_definition['nodes']]
        
        if 'EnhancedInvoiceFetchNode' not in node_types:
            warnings.append("Missing data fetch node")
        
        if 'EnhancedReportGeneratorNode' not in node_types:
            warnings.append("Missing report generation node")
        
        # Check for proper sequencing
        if len(workflow_definition['edges']) < len(workflow_definition['nodes']) - 1:
            warnings.append("Insufficient edges for node count")
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings,
            'node_count': len(workflow_definition['nodes']),
            'edge_count': len(workflow_definition['edges'])
        }
    
    def _add_performance_metadata(self, workflow_definition: Dict[str, Any], analysis: QueryAnalysis) -> Dict[str, Any]:
        """Add performance metadata to workflow"""
        
        performance_metadata = {
            'estimated_execution_time': self._estimate_execution_time(analysis),
            'memory_requirements': self._estimate_memory_requirements(analysis),
            'parallelizable_nodes': self._identify_parallelizable_nodes(workflow_definition),
            'bottleneck_analysis': self._analyze_bottlenecks(workflow_definition),
            'scaling_recommendations': self._get_scaling_recommendations(analysis)
        }
        
        workflow_definition['metadata']['performance'] = performance_metadata
        
        return workflow_definition
    
    def _estimate_execution_time(self, analysis: QueryAnalysis) -> str:
        """Estimate workflow execution time"""
        
        base_time = 30  # seconds
        
        if analysis.complexity == WorkflowComplexity.SIMPLE:
            return f"{base_time} seconds"
        elif analysis.complexity == WorkflowComplexity.MEDIUM:
            return f"{base_time * 2} seconds"
        elif analysis.complexity == WorkflowComplexity.COMPLEX:
            return f"{base_time * 5} seconds"
        else:
            return f"{base_time * 10} seconds"
    
    def _estimate_memory_requirements(self, analysis: QueryAnalysis) -> str:
        """Estimate memory requirements"""
        
        if analysis.complexity == WorkflowComplexity.SIMPLE:
            return "1GB"
        elif analysis.complexity == WorkflowComplexity.MEDIUM:
            return "2GB"
        elif analysis.complexity == WorkflowComplexity.COMPLEX:
            return "4GB"
        else:
            return "8GB"
    
    def _identify_parallelizable_nodes(self, workflow_definition: Dict[str, Any]) -> List[str]:
        """Identify nodes that can be parallelized"""
        
        parallelizable = []
        
        for node in workflow_definition['nodes']:
            if node['node_type'] in ['DataQualityNode', 'CurrencyConversionNode', 'FilterNode']:
                parallelizable.append(node['step_id'])
        
        return parallelizable
    
    def _analyze_bottlenecks(self, workflow_definition: Dict[str, Any]) -> List[str]:
        """Analyze potential bottlenecks"""
        
        bottlenecks = []
        
        for node in workflow_definition['nodes']:
            if node['node_type'] in ['EnhancedInvoiceFetchNode']:
                bottlenecks.append(f"{node['step_id']}: Data fetch - potential I/O bottleneck")
            elif node['node_type'] in ['AdvancedGroupingNode', 'SummaryStatisticsNode']:
                bottlenecks.append(f"{node['step_id']}: Aggregation - potential CPU bottleneck")
        
        return bottlenecks
    
    def _get_scaling_recommendations(self, analysis: QueryAnalysis) -> List[str]:
        """Get scaling recommendations"""
        
        recommendations = []
        
        if analysis.complexity in [WorkflowComplexity.COMPLEX, WorkflowComplexity.ADVANCED]:
            recommendations.append("Consider horizontal scaling for data fetch operations")
            recommendations.append("Implement result caching for frequently accessed data")
            recommendations.append("Use database indexing for large datasets")
        
        if analysis.complexity == WorkflowComplexity.ADVANCED:
            recommendations.append("Consider distributed processing for large aggregations")
            recommendations.append("Implement streaming for real-time data processing")
        
        return recommendations
    
    def _extract_group_fields(self, analysis: QueryAnalysis) -> List[str]:
        """Extract grouping fields from analysis"""
        
        # Default grouping fields based on report type
        if 'vendor' in analysis.report_type:
            return ['vendor_id', 'vendor_name']
        elif 'customer' in analysis.report_type:
            return ['customer_id', 'customer_name']
        elif 'aging' in analysis.report_type:
            return ['aging_bucket']
        else:
            return ['category', 'status']
    
    def _extract_aggregation_functions(self, analysis: QueryAnalysis) -> List[str]:
        """Extract aggregation functions from analysis"""
        
        functions = []
        
        if 'sum' in analysis.aggregations:
            functions.append('sum')
        if 'avg' in analysis.aggregations:
            functions.append('avg')
        if 'count' in analysis.aggregations:
            functions.append('count')
        
        # Default aggregations
        if not functions:
            functions = ['sum', 'count']
        
        return functions
    
    async def _create_fallback_workflow_advanced(self, query: str, company_id: str, user_id: str) -> Dict[str, Any]:
        """Create fallback workflow with advanced features"""
        
        return {
            'edges': [],
            'nodes': [
                {
                    'title': 'Enhanced Data Fetch',
                    'params': {
                        'query': query,
                        'company_id': company_id,
                        'batch_size': 500,
                        'parallel_fetch': True
                    },
                    'status': 'pending',
                    'step_id': 'step_1',
                    'node_type': 'EnhancedInvoiceFetchNode',
                    'step_number': 1,
                    'performance_tuning': {
                        'batch_size': 500,
                        'parallel_fetch': True
                    }
                },
                {
                    'title': 'Advanced Report Generation',
                    'params': {
                        'query': query,
                        'output_format': 'excel',
                        'include_charts': True,
                        'branding': 'auto'
                    },
                    'status': 'pending',
                    'step_id': 'step_2',
                    'node_type': 'EnhancedReportGeneratorNode',
                    'step_number': 2
                }
            ],
            'metadata': {
                'analysis': {
                    'query_type': 'report_generation',
                    'report_type': 'custom',
                    'complexity': 'simple',
                    'confidence_score': 0.5
                },
                'generated_at': datetime.now().isoformat(),
                'query': query,
                'optimization_level': 'basic',
                'fallback': True
            }
        }
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response with multiple fallback strategies"""
        try:
            # Try direct JSON parsing first
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Try to extract JSON object from text
            brace_start = response.find('{')
            brace_end = response.rfind('}')
            if brace_start != -1 and brace_end != -1:
                try:
                    return json.loads(response[brace_start:brace_end + 1])
                except json.JSONDecodeError:
                    pass
            
            # Fallback to empty dict
            logger.warning(f"Failed to parse LLM response as JSON: {response[:100]}...")
            return {}


# Global instance
enhanced_workflow_generator = EnhancedLLMWorkflowGenerator()


async def generate_advanced_workflow(query: str, company_id: str, user_id: str) -> Dict[str, Any]:
    """Convenience function to generate advanced workflow"""
    return await enhanced_workflow_generator.generate_workflow_advanced(query, company_id, user_id)