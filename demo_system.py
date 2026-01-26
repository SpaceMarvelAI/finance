"""
Complete Financial Automation Demo
Shows entire flow: Upload → Parse → Extract → Calculate → Query → Report
"""

import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent))

from agents.ingestion_agent import IngestionAgent
from agents.extraction_agent import ExtractionAgent
from agents.query_agent import ConversationalFinancialAgent
from processing_layer.agents.core.base_agent import BaseAgent
from shared.llm.groq_client import get_groq_client
from data_layer.schemas.canonical_schema import CanonicalFinancialDocument
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


def demo_complete_system(invoice_files: list):
    """
    Complete system demonstration
    
    Flow:
    1. Upload invoices
    2. Parse with Docling
    3. Extract with LLM
    4. Calculate with Python
    5. Query with natural language
    6. Generate reports
    """
    
    print("="*70)
    print("FINANCIAL AUTOMATION SYSTEM - COMPLETE DEMO")
    print("="*70)
    
    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        print("\n GROQ_API_KEY not set!")
        print("Get key: https://console.groq.com/keys")
        return
    
    # Initialize agents
    print("\n🤖 Initializing agents...")
    ingestion_agent = IngestionAgent()
    groq_client = get_groq_client("accurate")
    extraction_agent = ExtractionAgent(groq_client)
    financial_agent = ConversationalFinancialAgent()
    
    print("✓ All agents initialized")
    
    # ========== PHASE 1: DOCUMENT PROCESSING ==========
    print("\n" + "="*70)
    print("PHASE 1: DOCUMENT PROCESSING")
    print("="*70)
    
    processed_documents = []
    
    for i, file_path in enumerate(invoice_files, 1):
        print(f"\n📄 Processing document {i}/{len(invoice_files)}: {Path(file_path).name}")
        
        # Create state
        state = dict(
            file_path=file_path,
            company_id="demo-company",
            input_data={},
            parsed_data={},
            canonical_data={},
            validation_errors=[],
            validation_warnings=[],
            is_valid=False,
            calculations={},
            report_type="",
            report_data={},
            report_path="",
            current_step="",
            workflow_id=f"doc-{i}",
            metadata={},
            error_message=""
        )
        
        # Step 1: Parse
        print("  → Parsing with Docling...")
        state = ingestion_agent.execute(state)
        
        if state.get("error_message"):
            print(f"   Failed: {state['error_message']}")
            continue
        
        print("  ✓ Parsed")
        
        # Step 2: Extract schema
        print("  → Extracting schema with LLM...")
        state = extraction_agent.execute(state)
        
        if state.get("error_message"):
            print(f"   Failed: {state['error_message']}")
            continue
        
        print("  ✓ Schema extracted")
        
        # Convert to canonical document
        try:
            canonical_doc = CanonicalFinancialDocument(**state["canonical_data"])
            processed_documents.append(canonical_doc)
            
            print(f"  ✓ Document ready: {canonical_doc.document_metadata.document_number}")
            print(f"     Amount: ${canonical_doc.totals.grand_total:,.2f}")
        except Exception as e:
            print(f"   Failed to create canonical doc: {e}")
    
    print(f"\n Processed {len(processed_documents)} documents successfully")
    
    # Load into financial agent
    print("\n📊 Loading documents into financial system...")
    financial_agent.load_documents(processed_documents)
    print("✓ Documents loaded")
    
    # ========== PHASE 2: INTERACTIVE QUERIES ==========
    print("\n" + "="*70)
    print("PHASE 2: NATURAL LANGUAGE QUERIES")
    print("="*70)
    
    # Example queries
    queries = [
        "Show me AR aging report",
        "What's my total receivables?",
        "Show me AP summary",
        "Give me a P&L statement",
        "Show cash flow",
        "What's my GST liability?",
        "Show vendor summary",
        "Give me all key metrics"
    ]
    
    print("\n💬 You can ask questions like:")
    for q in queries:
        print(f"  - {q}")
    
    print("\n" + "-"*70)
    print("DEMO QUERIES:")
    print("-"*70)
    
    # Run demo queries
    demo_queries = [
        "Show me AR aging report",
        "What's my total receivables and payables?",
        "Give me P&L for this period"
    ]
    
    for query in demo_queries:
        print(f"\n👤 User: {query}")
        print("-"*70)
        
        response = financial_agent.ask(query)
        
        print(f"🤖 Assistant:\n{response}")
        print("-"*70)
    
    # ========== PHASE 3: INTERACTIVE MODE ==========
    print("\n" + "="*70)
    print("PHASE 3: INTERACTIVE MODE")
    print("="*70)
    print("\nType your questions (or 'exit' to quit):")
    print("Examples:")
    print("  - Show me vendor summary")
    print("  - What's my cash flow?")
    print("  - Show GST report")
    print()
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Process query
            response = financial_agent.ask(user_input)
            
            print(f"\n🤖 Assistant:\n{response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n Error: {e}")
    
    # ========== SUMMARY ==========
    print("\n" + "="*70)
    print("DEMO SUMMARY")
    print("="*70)
    print(f"\n Documents Processed: {len(processed_documents)}")
    print(f" Queries Answered: {len(financial_agent.get_conversation_history()) // 2}")
    print(f" System Status: Fully Operational")
    
    print("\n🎯 What You Can Do Now:")
    print("  1. Upload more invoices")
    print("  2. Ask any financial question")
    print("  3. Generate reports (AR, AP, P&L, etc.)")
    print("  4. No Tally or ERP needed!")
    
    print("\n" + "="*70)


def quick_demo():
    """Quick demo with sample queries (no document processing)"""
    
    print("="*70)
    print("QUICK DEMO - Natural Language Financial Queries")
    print("="*70)
    
    if not os.getenv("GROQ_API_KEY"):
        print("\n GROQ_API_KEY not set!")
        return
    
    # Initialize agent
    financial_agent = ConversationalFinancialAgent()
    
    print("\n📊 Financial system ready!")
    print("\n💬 Ask questions like:")
    print("  - Show me AR aging")
    print("  - What's my P&L?")
    print("  - Show vendor summary")
    print("\nType 'exit' to quit\n")
    
    while True:
        try:
            query = input("👤 You: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Process query
            response = financial_agent.ask(query)
            print(f"\n🤖 Assistant:\n{response}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n Error: {e}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Financial Automation System Demo"
    )
    parser.add_argument(
        "--mode",
        choices=["complete", "quick"],
        default="quick",
        help="Demo mode: complete (with document processing) or quick (query only)"
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Invoice files to process (for complete mode)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "complete":
        if not args.files:
            print("Error: --files required for complete mode")
            print("\nExample:")
            print("  python demo_system.py --mode complete --files invoice1.pdf invoice2.csv")
            return
        
        demo_complete_system(args.files)
    else:
        quick_demo()


if __name__ == "__main__":
    main()