"""
Test Enhanced LLM Workflow Generation System
Phase 3.2: LLM Workflow Generation Engine
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

from processing_layer.workflows.enhanced_llm_workflow_generator import (
    EnhancedLLMWorkflowGenerator,
    QueryAnalysis,
    WorkflowOptimization,
    WorkflowComplexity,
    QueryType
)
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class EnhancedWorkflowTestSuite:
    """Test suite for enhanced LLM workflow generation"""
    
    def __init__(self):
        self.generator = EnhancedLLMWorkflowGenerator()
        self.test_results = []
        
    async def run_all_tests(self):
        """Run all test cases"""
        print("🧪 Running Enhanced LLM Workflow Generation Test Suite")
        print("=" * 60)
        
        # Test 1: Basic query analysis
        await self.test_basic_query_analysis()
        
        # Test 2: Advanced query analysis
        await self.test_advanced_query_analysis()
        
        # Test 3: Workflow generation
        await self.test_workflow_generation()
        
        # Test 4: Workflow optimization
        await self.test_workflow_optimization()
        
        # Test 5: Performance metadata
        await self.test_performance_metadata()
        
        # Test 6: Caching functionality
        await self.test_caching_functionality()
        
        # Test 7: Error handling
        await self.test_error_handling()
        
        # Test 8: Complex workflow generation
        await self.test_complex_workflow_generation()
        
        # Print results
        self.print_test_results()
        
    async def test_basic_query_analysis(self):
        """Test basic query analysis functionality"""
        print("📋 Test 1: Basic Query Analysis")
        
        try:
            query = "Generate AP aging report for last 30 days"
            analysis = await self.generator._analyze_query_advanced(query, "test_company")
            
            # Validate analysis structure
            assert isinstance(analysis, QueryAnalysis), "Analysis should be QueryAnalysis instance"
            assert analysis.query_type == QueryType.REPORT_GENERATION, "Should be report generation type"
            assert analysis.complexity == WorkflowComplexity.MEDIUM, "Should be medium complexity"
            assert "aging" in analysis.report_type, "Should detect aging report type"
            assert analysis.time_range == "last_30_days", "Should detect time range"
            
            self.test_results.append({
                "test": "Basic Query Analysis",
                "status": "PASS",
                "details": f"Query: {query}, Type: {analysis.query_type.value}, Complexity: {analysis.complexity.value}"
            })
            print("✅ Basic query analysis passed")
            
        except Exception as e:
            self.test_results.append({
                "test": "Basic Query Analysis",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"❌ Basic query analysis failed: {e}")
    
    async def test_advanced_query_analysis(self):
        """Test advanced query analysis with complex requirements"""
        print("📋 Test 2: Advanced Query Analysis")
        
        try:
            query = "Create AR register with outstanding amounts, DSO calculation, and trend analysis for Q4 2025"
            analysis = await self.generator._analyze_query_advanced(query, "test_company")
            
            # Validate advanced analysis
            assert analysis.query_type == QueryType.DATA_ANALYSIS, "Should be data analysis type"
            assert analysis.complexity == WorkflowComplexity.ADVANCED, "Should be advanced complexity"
            assert "dso" in analysis.custom_calculations, "Should detect DSO calculation"
            assert "trend" in str(analysis.key_requirements).lower(), "Should detect trend analysis"
            assert "q4" in analysis.time_range.lower() or "2025" in analysis.time_range, "Should detect Q4 2025"
            
            self.test_results.append({
                "test": "Advanced Query Analysis",
                "status": "PASS",
                "details": f"Complexity: {analysis.complexity.value}, Custom calculations: {analysis.custom_calculations}"
            })
            print("✅ Advanced query analysis passed")
            
        except Exception as e:
            self.test_results.append({
                "test": "Advanced Query Analysis",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"❌ Advanced query analysis failed: {e}")
    
    async def test_workflow_generation(self):
        """Test workflow generation from query"""
        print("📋 Test 3: Workflow Generation")
        
        try:
            query = "Generate AP aging report for last 90 days with vendor grouping"
            workflow = await self.generator.generate_workflow_advanced(
                query, "test_company", "test_user"
            )
            
            # Validate workflow structure
            assert "nodes" in workflow, "Workflow should have nodes"
            assert "edges" in workflow, "Workflow should have edges"
            assert "metadata" in workflow, "Workflow should have metadata"
            
            # Validate nodes
            nodes = workflow["nodes"]
            assert len(nodes) > 0, "Should have at least one node"
            
            # Check for required node types
            node_types = [node["node_type"] for node in nodes]
            assert "EnhancedInvoiceFetchNode" in node_types, "Should have fetch node"
            assert "EnhancedReportGeneratorNode" in node_types, "Should have report generator node"
            
            # Validate metadata
            metadata = workflow["metadata"]
            assert "analysis" in metadata, "Should have analysis in metadata"
            assert "optimization_level" in metadata, "Should have optimization level"
            
            self.test_results.append({
                "test": "Workflow Generation",
                "status": "PASS",
                "details": f"Generated {len(nodes)} nodes, optimization: {metadata.get('optimization_level')}"
            })
            print("✅ Workflow generation passed")
            
        except Exception as e:
            self.test_results.append({
                "test": "Workflow Generation",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"❌ Workflow generation failed: {e}")
    
    async def test_workflow_optimization(self):
        """Test workflow optimization functionality"""
        print("📋 Test 4: Workflow Optimization")
        
        try:
            # Create a sample workflow
            sample_workflow = {
                "nodes": [
                    {
                        "title": "Data Fetch",
                        "node_type": "EnhancedInvoiceFetchNode",
                        "params": {"batch_size": 500},
                        "step_number": 1
                    },
                    {
                        "title": "Report Generation",
                        "node_type": "EnhancedReportGeneratorNode",
                        "params": {"output_format": "excel"},
                        "step_number": 2
                    }
                ],
                "edges": [
                    {"source": "step_1", "target": "step_2", "type": "sequential"}
                ]
            }
            
            # Test optimization
            optimization = await self.generator._get_optimization_suggestions(
                sample_workflow,
                QueryAnalysis(
                    query_type=QueryType.REPORT_GENERATION,
                    report_type="ap_aging",
                    data_source="vendor_invoices",
                    complexity=WorkflowComplexity.MEDIUM,
                    key_requirements=[],
                    time_range="last_90_days",
                    filters={},
                    aggregations=[],
                    custom_calculations=[],
                    output_format="excel",
                    confidence_score=0.8,
                    suggested_nodes=[]
                )
            )
            
            # Validate optimization suggestions
            assert isinstance(optimization, WorkflowOptimization), "Should return WorkflowOptimization"
            assert isinstance(optimization.performance_improvements, list), "Should have performance improvements"
            assert isinstance(optimization.node_optimizations, list), "Should have node optimizations"
            
            # Apply optimizations
            optimized_workflow = self.generator._apply_optimizations(sample_workflow, optimization)
            
            self.test_results.append({
                "test": "Workflow Optimization",
                "status": "PASS",
                "details": f"Optimizations: {len(optimization.performance_improvements)} performance, {len(optimization.node_optimizations)} node"
            })
            print("✅ Workflow optimization passed")
            
        except Exception as e:
            self.test_results.append({
                "test": "Workflow Optimization",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"❌ Workflow optimization failed: {e}")
    
    async def test_performance_metadata(self):
        """Test performance metadata generation"""
        print("📋 Test 5: Performance Metadata")
        
        try:
            # Create analysis for performance testing
            analysis = QueryAnalysis(
                query_type=QueryType.REPORT_GENERATION,
                report_type="ap_aging",
                data_source="vendor_invoices",
                complexity=WorkflowComplexity.COMPLEX,
                key_requirements=["data_fetch", "grouping", "aggregation"],
                time_range="last_90_days",
                filters={"status": ["unpaid"]},
                aggregations=["sum", "count"],
                custom_calculations=["aging_days"],
                output_format="excel",
                confidence_score=0.9,
                suggested_nodes=["EnhancedInvoiceFetchNode", "GroupingNode", "SummaryNode"]
            )
            
            # Test execution time estimation
            exec_time = self.generator._estimate_execution_time(analysis)
            assert "seconds" in exec_time, "Should estimate execution time"
            
            # Test memory requirements
            memory = self.generator._estimate_memory_requirements(analysis)
            assert memory in ["1GB", "2GB", "4GB", "8GB"], "Should estimate memory requirements"
            
            # Test parallelizable nodes identification
            sample_workflow = {
                "nodes": [
                    {"node_type": "DataQualityNode", "step_id": "step_1"},
                    {"node_type": "EnhancedInvoiceFetchNode", "step_id": "step_2"},
                    {"node_type": "FilterNode", "step_id": "step_3"}
                ]
            }
            parallel_nodes = self.generator._identify_parallelizable_nodes(sample_workflow)
            assert isinstance(parallel_nodes, list), "Should return list of parallelizable nodes"
            
            self.test_results.append({
                "test": "Performance Metadata",
                "status": "PASS",
                "details": f"Exec time: {exec_time}, Memory: {memory}, Parallel nodes: {len(parallel_nodes)}"
            })
            print("✅ Performance metadata passed")
            
        except Exception as e:
            self.test_results.append({
                "test": "Performance Metadata",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"❌ Performance metadata failed: {e}")
    
    async def test_caching_functionality(self):
        """Test caching functionality"""
        print("📋 Test 6: Caching Functionality")
        
        try:
            query = "Generate AP aging report"
            company_id = "test_company"
            
            # First call should populate cache
            analysis1 = await self.generator._analyze_query_advanced(query, company_id)
            
            # Second call should use cache
            analysis2 = await self.generator._analyze_query_advanced(query, company_id)
            
            # Should be the same object (cached)
            assert analysis1 is analysis2, "Should return cached analysis"
            
            # Test cache size
            cache_size = len(self.generator.query_cache)
            assert cache_size > 0, "Cache should have entries"
            
            self.test_results.append({
                "test": "Caching Functionality",
                "status": "PASS",
                "details": f"Cache hit successful, cache size: {cache_size}"
            })
            print("✅ Caching functionality passed")
            
        except Exception as e:
            self.test_results.append({
                "test": "Caching Functionality",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"❌ Caching functionality failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling and fallback mechanisms"""
        print("📋 Test 7: Error Handling")
        
        try:
            # Test with invalid query
            invalid_query = ""
            workflow = await self.generator.generate_workflow_advanced(
                invalid_query, "test_company", "test_user"
            )
            
            # Should return fallback workflow
            assert "nodes" in workflow, "Should return fallback workflow"
            assert workflow.get("metadata", {}).get("fallback", False), "Should be fallback workflow"
            
            # Test with very long query
            long_query = "A" * 10000
            workflow2 = await self.generator.generate_workflow_advanced(
                long_query, "test_company", "test_user"
            )
            
            # Should handle gracefully
            assert "nodes" in workflow2, "Should handle long queries"
            
            self.test_results.append({
                "test": "Error Handling",
                "status": "PASS",
                "details": "Graceful handling of invalid and long queries"
            })
            print("✅ Error handling passed")
            
        except Exception as e:
            self.test_results.append({
                "test": "Error Handling",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"❌ Error handling failed: {e}")
    
    async def test_complex_workflow_generation(self):
        """Test complex workflow generation with multiple requirements"""
        print("📋 Test 8: Complex Workflow Generation")
        
        try:
            query = "Generate comprehensive financial report with AP aging, AR register, DSO analysis, currency conversion, and trend analysis for multiple entities"
            
            workflow = await self.generator.generate_workflow_advanced(
                query, "test_company", "test_user"
            )
            
            # Validate complex workflow
            nodes = workflow["nodes"]
            metadata = workflow["metadata"]
            
            # Should have multiple nodes
            assert len(nodes) > 5, "Should have multiple nodes for complex query"
            
            # Should have advanced optimization
            assert metadata.get("optimization_level") == "advanced", "Should use advanced optimization"
            
            # Should have performance metadata
            performance = metadata.get("performance", {})
            assert "estimated_execution_time" in performance, "Should have execution time estimate"
            assert "memory_requirements" in performance, "Should have memory requirements"
            assert "bottleneck_analysis" in performance, "Should have bottleneck analysis"
            
            # Should have validation metadata
            validation = metadata.get("validation", {})
            assert "valid" in validation, "Should have validation results"
            
            self.test_results.append({
                "test": "Complex Workflow Generation",
                "status": "PASS",
                "details": f"Generated {len(nodes)} nodes with advanced optimization"
            })
            print("✅ Complex workflow generation passed")
            
        except Exception as e:
            self.test_results.append({
                "test": "Complex Workflow Generation",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"❌ Complex workflow generation failed: {e}")
    
    def print_test_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed = sum(1 for result in self.test_results if result["status"] == "FAIL")
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 Detailed Results:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{i}. {status_icon} {result['test']}: {result['details']}")
        
        if failed == 0:
            print("\n🎉 All tests passed! Enhanced LLM Workflow Generation is working correctly.")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Please review the implementation.")
        
        # Save results to file
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "test_summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "success_rate": (passed/total)*100
                },
                "test_results": self.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📄 Test results saved to: {results_file}")


async def main():
    """Main test execution"""
    test_suite = EnhancedWorkflowTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())