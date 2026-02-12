#!/usr/bin/env python3
"""
Comprehensive Integration Tests
Tests the complete system integration including LangGraph, MCP tools, and API v2
"""

import asyncio
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import time

# Add the project root to Python path
sys.path.insert(0, os.getcwd())

# Import test dependencies
from test_report_template_integration import get_test_data_from_database, create_ap_aging_test_data, create_ap_register_test_data
from mcp.server import get_mcp_server
from processing_layer.agents.langgraph_framework.report_template_integration import ReportTemplateIntegration
from data_layer.database.database_manager import get_database
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class IntegrationTestSuite:
    """Comprehensive integration test suite"""
    
    def __init__(self):
        self.mcp_server = get_mcp_server()
        self.report_integration = ReportTemplateIntegration()
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{'✅' if status == 'PASS' else '❌'} {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    async def test_mcp_server(self):
        """Test MCP server functionality"""
        print("\n🧪 Testing MCP Server")
        print("=" * 50)
        
        try:
            # Test server info
            server_info = self.mcp_server.get_server_info()
            if server_info["tools_count"] >= 8:
                self.log_test("MCP Server Info", "PASS", f"Tools: {server_info['tools_count']}")
            else:
                self.log_test("MCP Server Info", "FAIL", f"Expected 8+ tools, got {server_info['tools_count']}")
            
            # Test health check
            health = self.mcp_server.health_check()
            if health["status"] == "healthy":
                self.log_test("MCP Health Check", "PASS", "Server is healthy")
            else:
                self.log_test("MCP Health Check", "FAIL", f"Server status: {health['status']}")
            
            # Test tools
            tools = self.mcp_server.get_tools()
            if len(tools) >= 8:
                self.log_test("MCP Tools Available", "PASS", f"{len(tools)} tools available")
            else:
                self.log_test("MCP Tools Available", "FAIL", f"Expected 8+ tools, got {len(tools)}")
            
            # Test specific tool execution
            template_result = self.mcp_server.execute_tool("get_available_templates", {})
            if template_result["status"] == "success":
                self.log_test("MCP Tool Execution", "PASS", "get_available_templates executed successfully")
            else:
                self.log_test("MCP Tool Execution", "FAIL", f"Tool execution failed: {template_result.get('message', 'Unknown error')}")
            
            return True
            
        except Exception as e:
            self.log_test("MCP Server", "FAIL", f"Exception: {e}")
            return False
    
    async def test_langgraph_integration(self):
        """Test LangGraph integration"""
        print("\n🧪 Testing LangGraph Integration")
        print("=" * 50)
        
        try:
            # Test template integration
            templates = self.report_integration.get_available_templates()
            if len(templates) >= 7:
                self.log_test("LangGraph Templates", "PASS", f"{len(templates)} templates available")
            else:
                self.log_test("LangGraph Templates", "FAIL", f"Expected 7+ templates, got {len(templates)}")
            
            # Test template capabilities
            capabilities = self.report_integration.get_template_capabilities()
            if len(capabilities) >= 7:
                self.log_test("LangGraph Capabilities", "PASS", f"{len(capabilities)} capabilities available")
            else:
                self.log_test("LangGraph Capabilities", "FAIL", f"Expected 7+ capabilities, got {len(capabilities)}")
            
            # Test template info
            template_info = self.report_integration.get_template_info('ap_aging')
            if template_info and 'name' in template_info:
                self.log_test("LangGraph Template Info", "PASS", f"AP Aging template: {template_info['name']}")
            else:
                self.log_test("LangGraph Template Info", "FAIL", "Could not get template info")
            
            return True
            
        except Exception as e:
            self.log_test("LangGraph Integration", "FAIL", f"Exception: {e}")
            return False
    
    async def test_report_generation(self):
        """Test report generation with real data"""
        print("\n🧪 Testing Report Generation")
        print("=" * 50)
        
        try:
            # Get test data
            database_data = get_test_data_from_database()
            if not database_data:
                # Use mock data
                database_data = {
                    'company_id': 'test_company_123',
                    'company_name': 'Test Company',
                    'invoices': [
                        (1, 'Test Vendor 1', 'V001', 'INV-001', '2026-01-01', '2026-01-15', 'Test Description 1', 10000.0, 1800.0, 11800.0, 0.0, 11800.0, 'Unpaid'),
                        (2, 'Test Vendor 2', 'V002', 'INV-002', '2025-12-01', '2025-12-15', 'Test Description 2', 5000.0, 900.0, 5900.0, 2000.0, 3900.0, 'Partial')
                    ],
                    'payments': []
                }
            
            # Test AP Aging report generation
            ap_aging_data = create_ap_aging_test_data(database_data)
            if ap_aging_data:
                result = self.report_integration.generate_report(
                    'ap_aging',
                    {'data': ap_aging_data, 'company_id': database_data['company_id']},
                    database_data['company_id'],
                    {'as_of_date': '2026-01-26'}
                )
                
                if result['status'] == 'success':
                    self.log_test("AP Aging Report Generation", "PASS", f"File: {Path(result['file_path']).name}")
                else:
                    self.log_test("AP Aging Report Generation", "FAIL", f"Generation failed: {result.get('error', 'Unknown error')}")
            else:
                self.log_test("AP Aging Report Generation", "FAIL", "Could not create test data")
            
            # Test AP Register report generation
            ap_register_data = create_ap_register_test_data(database_data)
            if ap_register_data:
                result = self.report_integration.generate_report(
                    'ap_register',
                    {'data': ap_register_data, 'company_id': database_data['company_id']},
                    database_data['company_id']
                )
                
                if result['status'] == 'success':
                    self.log_test("AP Register Report Generation", "PASS", f"File: {Path(result['file_path']).name}")
                else:
                    self.log_test("AP Register Report Generation", "FAIL", f"Generation failed: {result.get('error', 'Unknown error')}")
            else:
                self.log_test("AP Register Report Generation", "FAIL", "Could not create test data")
            
            return True
            
        except Exception as e:
            self.log_test("Report Generation", "FAIL", f"Exception: {e}")
            return False
    
    async def test_mcp_report_generation(self):
        """Test MCP tools for report generation"""
        print("\n🧪 Testing MCP Report Generation Tools")
        print("=" * 50)
        
        try:
            # Test get available templates via MCP
            templates_result = self.mcp_server.execute_tool("get_available_templates", {})
            if templates_result["status"] == "success":
                self.log_test("MCP Get Templates", "PASS", f"{len(templates_result.get('templates', []))} templates available")
            else:
                self.log_test("MCP Get Templates", "FAIL", f"Failed: {templates_result.get('message', 'Unknown error')}")
            
            # Test generate report via MCP
            database_data = get_test_data_from_database() or {
                'company_id': 'test_company_123',
                'company_name': 'Test Company',
                'invoices': [
                    (1, 'Test Vendor 1', 'V001', 'INV-001', '2026-01-01', '2026-01-15', 'Test Description 1', 10000.0, 1800.0, 11800.0, 0.0, 11800.0, 'Unpaid'),
                    (2, 'Test Vendor 2', 'V002', 'INV-002', '2025-12-01', '2025-12-15', 'Test Description 2', 5000.0, 900.0, 5900.0, 2000.0, 3900.0, 'Partial')
                ],
                'payments': []
            }
            
            ap_aging_data = create_ap_aging_test_data(database_data)
            if ap_aging_data:
                report_result = self.mcp_server.execute_tool("generate_report", {
                    "template_type": "ap_aging",
                    "report_data": {'data': ap_aging_data, 'company_id': database_data['company_id']},
                    "company_id": database_data['company_id'],
                    "params": {"as_of_date": "2026-01-26"}
                })
                
                if report_result["status"] == "success":
                    self.log_test("MCP Generate Report", "PASS", f"Report generated via MCP")
                else:
                    self.log_test("MCP Generate Report", "FAIL", f"Failed: {report_result.get('message', 'Unknown error')}")
            else:
                self.log_test("MCP Generate Report", "FAIL", "Could not create test data")
            
            # Test list generated reports via MCP
            list_result = self.mcp_server.execute_tool("list_generated_reports", {})
            if list_result["status"] == "success":
                self.log_test("MCP List Reports", "PASS", f"{len(list_result.get('reports', []))} reports found")
            else:
                self.log_test("MCP List Reports", "FAIL", f"Failed: {list_result.get('message', 'Unknown error')}")
            
            return True
            
        except Exception as e:
            self.log_test("MCP Report Generation", "FAIL", f"Exception: {e}")
            return False
    
    async def test_system_monitoring(self):
        """Test system monitoring and metrics"""
        print("\n🧪 Testing System Monitoring")
        print("=" * 50)
        
        try:
            # Test system status via MCP
            status_result = self.mcp_server.execute_tool("get_system_status", {})
            if status_result["status"] == "success":
                system_info = status_result.get("system", {})
                self.log_test("MCP System Status", "PASS", f"System monitoring working")
            else:
                self.log_test("MCP System Status", "FAIL", f"Failed: {status_result.get('message', 'Unknown error')}")
            
            # Test database connection
            db = get_database()
            if db.conn:
                self.log_test("Database Connection", "PASS", "Database connection established")
            else:
                self.log_test("Database Connection", "FAIL", "Database connection failed")
            
            return True
            
        except Exception as e:
            self.log_test("System Monitoring", "FAIL", f"Exception: {e}")
            return False
    
    async def test_performance(self):
        """Test system performance"""
        print("\n🧪 Testing Performance")
        print("=" * 50)
        
        try:
            # Test report generation performance
            database_data = get_test_data_from_database() or {
                'company_id': 'test_company_123',
                'company_name': 'Test Company',
                'invoices': [
                    (1, 'Test Vendor 1', 'V001', 'INV-001', '2026-01-01', '2026-01-15', 'Test Description 1', 10000.0, 1800.0, 11800.0, 0.0, 11800.0, 'Unpaid'),
                    (2, 'Test Vendor 2', 'V002', 'INV-002', '2025-12-01', '2025-12-15', 'Test Description 2', 5000.0, 900.0, 5900.0, 2000.0, 3900.0, 'Partial')
                ],
                'payments': []
            }
            
            # Measure AP Aging report generation time
            start_time = time.time()
            ap_aging_data = create_ap_aging_test_data(database_data)
            if ap_aging_data:
                result = self.report_integration.generate_report(
                    'ap_aging',
                    {'data': ap_aging_data, 'company_id': database_data['company_id']},
                    database_data['company_id'],
                    {'as_of_date': '2026-01-26'}
                )
                generation_time = time.time() - start_time
                
                if result['status'] == 'success':
                    self.log_test("Report Generation Performance", "PASS", f"Generated in {generation_time:.2f}s")
                else:
                    self.log_test("Report Generation Performance", "FAIL", "Generation failed")
            else:
                self.log_test("Report Generation Performance", "FAIL", "Could not create test data")
            
            # Test MCP tool execution performance
            start_time = time.time()
            templates_result = self.mcp_server.execute_tool("get_available_templates", {})
            mcp_time = time.time() - start_time
            
            if templates_result["status"] == "success":
                self.log_test("MCP Tool Performance", "PASS", f"Executed in {mcp_time:.3f}s")
            else:
                self.log_test("MCP Tool Performance", "FAIL", "Tool execution failed")
            
            return True
            
        except Exception as e:
            self.log_test("Performance Testing", "FAIL", f"Exception: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 COMPREHENSIVE INTEGRATION TEST SUITE")
        print("=" * 80)
        print(f"Started at: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Run all test suites
        test_results = []
        
        test_results.append(await self.test_mcp_server())
        test_results.append(await self.test_langgraph_integration())
        test_results.append(await self.test_report_generation())
        test_results.append(await self.test_mcp_report_generation())
        test_results.append(await self.test_system_monitoring())
        test_results.append(await self.test_performance())
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 INTEGRATION TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(1 for result in test_results if result)
        total_tests = len(test_results)
        
        print(f"Total Test Suites: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
        
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_icon} {result['test']}: {result['status']}")
            if result['details']:
                print(f"     {result['details']}")
        
        print("\n" + "=" * 80)
        
        if passed_tests == total_tests:
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("   The system is ready for production deployment.")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("   Please review the failed tests and address any issues.")
        
        print("=" * 80)
        
        return passed_tests == total_tests


async def main():
    """Main test runner"""
    # Test imports first
    print("🔍 Testing imports...")
    
    try:
        from mcp.server import get_mcp_server
        from processing_layer.agents.langgraph_framework.report_template_integration import ReportTemplateIntegration
        from data_layer.database.database_manager import get_database
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Run integration tests
    test_suite = IntegrationTestSuite()
    success = await test_suite.run_all_tests()
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)