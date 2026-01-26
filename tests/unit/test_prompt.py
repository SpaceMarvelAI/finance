"""
Test Financial Report System with Prompt Library
Comprehensive testing of router + prompt library integration
"""

import sys
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, '/home/claude')

from intelligence_layer.orchestration.financial_report_system import FinancialReportSystem
from intelligence_layer.routing.router_prompt_integrator import RouterPromptIntegrator
from intelligence_layer.prompts.prompt_library import PromptLibrary


def test_prompt_library():
    """Test prompt library functionality"""
    print("\n" + "="*80)
    print("TEST 1: PROMPT LIBRARY")
    print("="*80)
    
    library = PromptLibrary()
    
    # List all prompts
    prompts = library.list_all_prompts()
    print(f"\n✓ Loaded {len(prompts)} prompt templates")
    
    for prompt in prompts:
        print(f"\n  📄 {prompt['name']}")
        print(f"     Category: {prompt['category']}")
        print(f"     Report Type: {prompt['report_type']}")
        print(f"     Example: {prompt['examples'][0]}")
    
    # Test variable injection
    print("\n" + "-"*80)
    print("Testing variable injection...")
    
    variables = {
        "time_period": "December 2024",
        "vendor_filter": "AWS, Google Cloud, Microsoft Azure",
        "amount_threshold": "$10,000",
        "aging_buckets": "30, 60, 90, 120 days"
    }
    
    rendered = library.inject_variables("ap_aging_report", variables)
    
    print("\n✓ Successfully rendered AP Aging prompt")
    print(f"\nRendered Prompt (first 400 chars):")
    print(rendered[:400] + "...")


def test_router_integration():
    """Test router-prompt integration"""
    print("\n" + "="*80)
    print("TEST 2: ROUTER-PROMPT INTEGRATION")
    print("="*80)
    
    integrator = RouterPromptIntegrator()
    
    test_queries = [
        "Show me AP aging for last month",
        "List AWS invoices from December over $5000",
        "Generate revenue trend analysis for Q4 year over year",
        "Calculate GST for last quarter",
        "Budget vs actual variance for Engineering department"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print("-"*80)
        
        result = integrator.process_query(query)
        
        if result['status'] == 'success':
            print(f"✓ Domain: {result['domain']}")
            print(f"✓ Agent: {result['agent']}")
            print(f"✓ Prompt ID: {result['prompt_id']}")
            print(f"✓ Confidence: {result['confidence']:.2%}")
            print(f"✓ Processing Time: {result['execution_time']:.2f}s")
            
            print("\nExtracted Variables:")
            for category, values in result['variables'].items():
                if values:
                    print(f"  {category}: {values}")
            
            print(f"\nPrompt Preview (first 250 chars):")
            print(result['rendered_prompt'][:250] + "...")
        else:
            print(f"✗ Error: {result['error']}")


def test_end_to_end_system():
    """Test complete end-to-end system"""
    print("\n" + "="*80)
    print("TEST 3: END-TO-END SYSTEM")
    print("="*80)
    
    system = FinancialReportSystem()
    
    test_scenarios = [
        {
            "name": "AP Aging Report",
            "query": "Show me AP aging for all vendors in December 2024",
            "expected_domain": "APLayer"
        },
        {
            "name": "AR Invoice Register",
            "query": "List all unpaid customer invoices over $5000",
            "expected_domain": "ARLayer"
        },
        {
            "name": "Revenue Analysis",
            "query": "Analyze revenue trends for Q4 compared to last year",
            "expected_domain": "AnalysisLayer"
        },
        {
            "name": "Cash Flow Forecast",
            "query": "Generate cash flow forecast for next 90 days",
            "expected_domain": "CashFlowLayer"
        },
        {
            "name": "GST Calculation",
            "query": "Calculate GST for last month with input credits",
            "expected_domain": "TaxLayer"
        },
        {
            "name": "Budget Variance",
            "query": "Show budget variance for Engineering department in Q4",
            "expected_domain": "BudgetLayer"
        },
        {
            "name": "Overdue Alerts",
            "query": "Show all critical overdue invoices over 90 days",
            "expected_domain": "AlertLayer"
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n{'='*80}")
        print(f"Scenario: {scenario['name']}")
        print(f"Query: {scenario['query']}")
        print("-"*80)
        
        result = system.generate_report(scenario['query'], dry_run=True)
        
        # Check if domain matches expected
        domain_match = result.get('domain') == scenario['expected_domain']
        
        if result['status'] == 'success':
            print(f"✓ Status: Success")
            print(f"✓ Domain: {result['domain']} {'✓' if domain_match else '✗ Expected: ' + scenario['expected_domain']}")
            print(f"✓ Confidence: {result['confidence']:.2%}")
            print(f"✓ Prompt: {result['prompt_id']}")
            
            results.append({
                'scenario': scenario['name'],
                'success': True,
                'domain_match': domain_match,
                'confidence': result['confidence']
            })
        else:
            print(f"✗ Status: Failed")
            print(f"✗ Error: {result.get('error')}")
            
            results.append({
                'scenario': scenario['name'],
                'success': False,
                'domain_match': False,
                'confidence': 0
            })
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    domain_matches = sum(1 for r in results if r['domain_match'])
    avg_confidence = sum(r['confidence'] for r in results) / total if total > 0 else 0
    
    print(f"\nTotal Scenarios: {total}")
    print(f"Successful: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"Domain Matches: {domain_matches}/{total} ({domain_matches/total*100:.1f}%)")
    print(f"Average Confidence: {avg_confidence:.2%}")
    
    if successful == total and domain_matches == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  Some tests failed")


def demo_query_suggestions():
    """Demo query suggestions feature"""
    print("\n" + "="*80)
    print("TEST 4: QUERY SUGGESTIONS")
    print("="*80)
    
    integrator = RouterPromptIntegrator()
    
    domains = ["APLayer", "ARLayer", "AnalysisLayer", "TaxLayer", "BudgetLayer"]
    
    for domain in domains:
        print(f"\n{domain} - Suggested Queries:")
        suggestions = integrator.suggest_queries(domain)
        
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"  {i}. {suggestion}")


def demo_batch_processing():
    """Demo batch processing"""
    print("\n" + "="*80)
    print("TEST 5: BATCH PROCESSING")
    print("="*80)
    
    system = FinancialReportSystem()
    
    queries = [
        "AP aging for last month",
        "AR aging with DSO",
        "Revenue analysis Q4",
        "GST calculation December",
        "Budget variance Engineering",
        "Cash flow next quarter",
        "Overdue invoices over 60 days"
    ]
    
    results = system.batch_process(queries)
    
    print("\n" + "="*80)
    print("BATCH RESULTS")
    print("="*80)
    
    successful = sum(1 for r in results if r['status'] == 'success')
    
    print(f"\nProcessed: {len(results)} queries")
    print(f"Success Rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
    
    if successful == len(results):
        print("\n✓ All queries processed successfully!")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("FINANCIAL REPORT SYSTEM - COMPREHENSIVE TESTS")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: Prompt Library
        test_prompt_library()
        
        # Test 2: Router Integration
        test_router_integration()
        
        # Test 3: End-to-End System
        test_end_to_end_system()
        
        # Test 4: Query Suggestions
        demo_query_suggestions()
        
        # Test 5: Batch Processing
        demo_batch_processing()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        if test_name == "library":
            test_prompt_library()
        elif test_name == "router":
            test_router_integration()
        elif test_name == "system":
            test_end_to_end_system()
        elif test_name == "suggestions":
            demo_query_suggestions()
        elif test_name == "batch":
            demo_batch_processing()
        else:
            print("Usage: python test_prompt_system.py [library|router|system|suggestions|batch]")
    else:
        run_all_tests()