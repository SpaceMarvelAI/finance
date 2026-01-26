"""
Complete Financial Report Generation System
Natural Language Query → Professional Report

Integrates:
- LLM Router (domain classification + variable extraction)
- Prompt Library (11 domains, 15+ report types)
- Report Generation Agents
- Excel/PDF output
"""

import sys
import json
from typing import Dict, Any, Optional
from datetime import datetime

from .router_prompt_integrator import RouterPromptIntegrator
from .prompt_library import PromptLibrary

# Setup logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinancialReportSystem:
    """
    Complete Financial Report Generation System
    
    User Journey:
    1. User asks question in natural language
    2. System classifies domain and extracts variables
    3. System selects appropriate prompt template
    4. System generates report using agents
    5. User receives professional Excel/PDF report
    """
    
    def __init__(self):
        self.integrator = RouterPromptIntegrator()
        self.library = PromptLibrary()
        self.logger = logger
        
        print("✓ Financial Report System Initialized")
        print("✓ 11 Domains Loaded")
        print("✓ 15+ Report Templates Ready")
        print()
    
    def generate_report(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Generate report from natural language query
        
        Args:
            query: Natural language query
            context: Optional context (user_id, org_id, preferences)
            dry_run: If True, only show what would be generated
            
        Returns:
            Report result with file path or configuration
        """
        context = context or {}
        
        self.logger.info(f"{'[DRY RUN] ' if dry_run else ''}Processing: {query}")
        
        # Step 1: Process query through router-prompt integration
        result = self.integrator.process_query(query, context)
        
        if result['status'] == 'error':
            return result
        
        # Step 2: Display classification results
        print("\n" + "="*80)
        print("QUERY PROCESSING RESULTS")
        print("="*80)
        print(f"Query: {query}")
        print(f"Domain: {result['domain']}")
        print(f"Agent: {result['agent']}")
        print(f"Prompt: {result['prompt_id']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Processing Time: {result['execution_time']:.2f}s")
        
        print("\n📊 Extracted Variables:")
        for category, values in result['variables'].items():
            if values:
                print(f"  {category.capitalize()}: {json.dumps(values, indent=4)}")
        
        # If dry run, return configuration without executing
        if dry_run:
            print("\n[DRY RUN] Skipping report generation")
            return {
                **result,
                'mode': 'dry_run',
                'message': 'Configuration generated successfully'
            }
        
        # Step 3: Generate actual report
        print("\n" + "="*80)
        print("GENERATING REPORT...")
        print("="*80)
        
        try:
            report_output = self._execute_report_generation(
                result['report_config'],
                context
            )
            
            print("\n✓ Report Generated Successfully!")
            
            if 'file_path' in report_output:
                print(f"✓ File: {report_output['file_path']}")
            
            return {
                **result,
                'report_output': report_output,
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}", exc_info=True)
            return {
                **result,
                'status': 'error',
                'error': f'Report generation failed: {str(e)}'
            }
    
    def _execute_report_generation(
        self,
        report_config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute actual report generation
        
        This integrates with your existing agents and nodes
        """
        # Import your orchestrator
        try:
            from enhanced_orchestrator import EnhancedOrchestrator
            orchestrator = EnhancedOrchestrator()
        except ImportError:
            # Fallback to regular orchestrator
            from intelligence_layer.orchestration.orchestrator import Orchestrator
            orchestrator = Orchestrator()
        
        # Build parameters for agent
        params = {
            **report_config['variables'],
            'report_type': report_config['report_type'],
            'output_format': report_config['output_format'],
            'user_query': report_config['user_query']
        }
        
        # Add context
        if context:
            params.update(context)
        
        # Execute report generation
        result = orchestrator.generate_report(
            report_type=report_config['report_type'],
            params=params
        )
        
        return result
    
    def interactive_mode(self):
        """Run in interactive mode for testing"""
        print("\n" + "="*80)
        print("FINANCIAL REPORT SYSTEM - INTERACTIVE MODE")
        print("="*80)
        print("Ask questions in natural language to generate reports")
        print("Type 'help' for examples, 'exit' to quit")
        print("="*80 + "\n")
        
        while True:
            try:
                query = input("\n💬 Your query: ").strip()
                
                if not query:
                    continue
                
                if query.lower() == 'exit':
                    print("Goodbye!")
                    break
                
                if query.lower() == 'help':
                    self._show_examples()
                    continue
                
                if query.lower() == 'domains':
                    self._show_domains()
                    continue
                
                # Process query in dry run mode by default
                result = self.generate_report(query, dry_run=True)
                
                if result['status'] == 'success':
                    # Ask if user wants to generate actual report
                    generate = input("\n🎯 Generate actual report? (y/n): ").strip().lower()
                    
                    if generate == 'y':
                        result = self.generate_report(query, dry_run=False)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n Error: {e}")
                logger.error(f"Interactive mode error: {e}", exc_info=True)
    
    def _show_examples(self):
        """Show example queries"""
        examples = {
            "AP Layer": [
                "Show me AP aging for last month",
                "List AWS invoices from December over $5000",
                "Show overdue vendor invoices"
            ],
            "AR Layer": [
                "Generate AR aging report for Q4",
                "Show unpaid customer invoices",
                "Calculate DSO for last quarter"
            ],
            "Analysis Layer": [
                "Analyze revenue trends for 2024 year over year",
                "Show expense analysis by department",
                "Revenue breakdown by product category"
            ],
            "Tax Layer": [
                "Calculate GST for last month",
                "Generate GST return for Q3",
                "Show tax liability for December"
            ],
            "Budget Layer": [
                "Budget vs actual for Engineering",
                "Show variance analysis for Q4",
                "Department spending vs budget"
            ],
            "Cash Flow Layer": [
                "Cash flow forecast for next quarter",
                "Show weekly cash projections",
                "Cash runway analysis"
            ],
            "Reconciliation Layer": [
                "Reconcile bank statement for December",
                "Match bank transactions",
                "Show unreconciled items"
            ],
            "Alert Layer": [
                "Show critical overdue items",
                "Alert for invoices over 90 days",
                "SLA violations requiring attention"
            ]
        }
        
        print("\n" + "="*80)
        print("EXAMPLE QUERIES")
        print("="*80)
        
        for domain, queries in examples.items():
            print(f"\n{domain}:")
            for query in queries:
                print(f"  • {query}")
    
    def _show_domains(self):
        """Show available domains and their capabilities"""
        domains = {
            "FinanceLayer": "Financial dashboards and KPIs",
            "APLayer": "Accounts Payable (vendor invoices, aging, payments)",
            "ARLayer": "Accounts Receivable (customer invoices, collections)",
            "AnalysisLayer": "Trend analysis, forecasting, metrics",
            "ReconciliationLayer": "Bank reconciliation, payment matching",
            "ComplianceLayer": "Audit trails, regulatory reports",
            "CashFlowLayer": "Cash forecasting, liquidity management",
            "TaxLayer": "GST/VAT/TDS calculations",
            "BudgetLayer": "Budget planning, variance analysis",
            "AlertLayer": "Overdue tracking, SLA monitoring",
            "ReportLayer": "Custom reports, scheduled reporting"
        }
        
        print("\n" + "="*80)
        print("AVAILABLE DOMAINS")
        print("="*80)
        
        for domain, description in domains.items():
            print(f"\n{domain}")
            print(f"  {description}")
    
    def batch_process(self, queries: list) -> list:
        """Process multiple queries in batch"""
        results = []
        
        print("\n" + "="*80)
        print(f"BATCH PROCESSING {len(queries)} QUERIES")
        print("="*80)
        
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Processing: {query}")
            
            result = self.generate_report(query, dry_run=True)
            results.append(result)
            
            if result['status'] == 'success':
                print(f"  ✓ Domain: {result['domain']}")
                print(f"  ✓ Confidence: {result['confidence']:.2%}")
            else:
                print(f"  ✗ Error: {result['error']}")
        
        return results


# ===== CLI INTERFACE =====

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Financial Report Generation System - Natural Language Interface"
    )
    
    parser.add_argument(
        "query",
        nargs="*",
        help="Natural language query (e.g., 'Show AP aging for last month')"
    )
    
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Show what would be generated without executing"
    )
    
    parser.add_argument(
        "--examples",
        "-e",
        action="store_true",
        help="Show example queries"
    )
    
    parser.add_argument(
        "--domains",
        action="store_true",
        help="Show available domains"
    )
    
    args = parser.parse_args()
    
    # Initialize system
    system = FinancialReportSystem()
    
    # Show examples
    if args.examples:
        system._show_examples()
        return
    
    # Show domains
    if args.domains:
        system._show_domains()
        return
    
    # Interactive mode
    if args.interactive:
        system.interactive_mode()
        return
    
    # Process query
    if args.query:
        query = " ".join(args.query)
        result = system.generate_report(query, dry_run=args.dry_run)
        
        # Print result as JSON
        print("\n" + "="*80)
        print("RESULT")
        print("="*80)
        print(json.dumps(result, indent=2, default=str))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()