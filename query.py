#!/usr/bin/env python3
"""
Simple Query Interface
Ask questions and get reports
"""

import sys
from pathlib import Path

# Add restructured to path
sys.path.insert(0, 'restructured')

from intelligence_layer.orchestration.enhanced_orchestrator import EnhancedOrchestrator


def query():
    """Interactive query interface"""
    
    print("\n" + "="*80)
    print("FINANCIAL AUTOMATION - QUERY INTERFACE")
    print("="*80)
    print("\n💬 Ask questions in natural language")
    print("🚪 Type 'exit' or 'quit' to stop")
    print("\n" + "="*80 + "\n")
    
    # Initialize orchestrator
    orchestrator = EnhancedOrchestrator()
    
    while True:
        try:
            # Get user input
            user_query = input("📝 Your Query: ").strip()
            
            if not user_query:
                continue
            
            if user_query.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            # Process query
            print()
            result = orchestrator.execute(user_query)
            print()
            
            # Show result
            if result.get('status') == 'success':
                print(" Report generated successfully")
                
                if 'report_path' in result:
                    print(f"📊 File: {result['report_path']}")
                
                print(f"⏱️  Time: {result.get('execution_time', 0):.2f}s")
            else:
                print(f"⚠️  Status: {result.get('status')}")
                if 'error' in result:
                    print(f"Error: {result['error']}")
            
            print("-"*80 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n Error: {e}\n")


def main():
    """Main entry point"""
    query()


if __name__ == '__main__':
    main()