"""
Simple Ingestion Test - Show Parsed Content
Works with existing IngestionAgent
"""

import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent))

# Import from your existing structure
from processing_layer.document_processing.enhanced_ingestion_agent import EnhancedIngestionAgent
from shared.config.logging_config import get_logger

logger = get_logger(__name__)


def print_line(char="=", width=100):
    print(char * width)


def test_file_parsing(file_path):
    """Parse a file and show what was extracted"""
    
    print("\n")
    print_line("=")
    print(f"🔍 PARSING: {Path(file_path).name}")
    print_line("=")
    
    # Create agent
    agent = EnhancedIngestionAgent()
    
    # Create simple state dict
    state = {
        "file_path": file_path,
        "company_id": "test",
        "workflow_id": "test-001",
        "input_data": {},
        "parsed_data": {},
        "canonical_data": {},
        "validation_errors": [],
        "validation_warnings": [],
        "is_valid": False,
        "calculations": {},
        "report_type": "",
        "report_data": {},
        "report_path": "",
        "current_step": "",
        "metadata": {},
        "error_message": "",
        "file_type": ""
    }
    
    try:
        # Execute parsing
        result = agent.execute(state)
        
        if result.get("error_message"):
            print(f"\n Error: {result['error_message']}\n")
            return
        
        print(f"\n Parsing Successful!")
        print(f"File Type: {result.get('file_type', 'Unknown')}\n")
        
        # Get parsed data
        parsed = result.get('parsed_data', {})
        text = parsed.get('text', '')
        
        # 1. SHOW EXTRACTED TEXT
        print_line("-")
        print("📄 EXTRACTED TEXT (First 1500 characters)")
        print_line("-")
        print(text[:1500])
        if len(text) > 1500:
            print(f"\n... [Truncated. Total: {len(text)} characters]")
        print()
        
        # 2. SHOW METADATA
        print_line("-")
        print("📊 METADATA")
        print_line("-")
        metadata = parsed.get('metadata', {})
        if metadata:
            for key, value in metadata.items():
                print(f"{key}: {value}")
        else:
            print("No metadata")
        print()
        
        # 3. FIND AMOUNTS
        print_line("-")
        print("💰 AMOUNTS FOUND")
        print_line("-")
        
        amounts = re.findall(r'[$₹€£]\s*[\d,]+\.?\d*|\b[\d,]+\.\d{2}\b', text)
        if amounts:
            unique_amounts = list(dict.fromkeys(amounts))[:15]  # Keep order, remove duplicates
            for i, amt in enumerate(unique_amounts, 1):
                print(f"  {i}. {amt}")
        else:
            print("  No amounts detected")
        print()
        
        # 4. FIND DATES
        print_line("-")
        print("📅 DATES FOUND")
        print_line("-")
        
        dates = re.findall(
            r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}',
            text,
            re.IGNORECASE
        )
        if dates:
            unique_dates = list(dict.fromkeys(dates))[:10]
            for i, date in enumerate(unique_dates, 1):
                print(f"  {i}. {date}")
        else:
            print("  No dates detected")
        print()
        
        # 5. FIND INVOICE NUMBERS
        print_line("-")
        print("🔢 INVOICE NUMBERS FOUND")
        print_line("-")
        
        invoices = re.findall(
            r'Invoice\s*#?\s*:?\s*[\w\d\-]+|Bill\s*#?\s*:?\s*[\w\d\-]+|INV[#\-\s]*[\w\d]+',
            text,
            re.IGNORECASE
        )
        if invoices:
            unique_invoices = list(dict.fromkeys(invoices))[:10]
            for i, inv in enumerate(unique_invoices, 1):
                print(f"  {i}. {inv}")
        else:
            print("  No invoice numbers detected")
        print()
        
        # 6. FIND KEY TERMS
        print_line("-")
        print("🔑 KEY TERMS DETECTED")
        print_line("-")
        
        key_terms = {
            'Invoice': 'invoice' in text.lower(),
            'Total': 'total' in text.lower(),
            'Amount': 'amount' in text.lower(),
            'Date': 'date' in text.lower(),
            'Vendor': 'vendor' in text.lower() or 'supplier' in text.lower(),
            'Customer': 'customer' in text.lower(),
            'Payment': 'payment' in text.lower(),
            'Tax': 'tax' in text.lower() or 'gst' in text.lower(),
        }
        
        for term, found in key_terms.items():
            status = "" if found else ""
            print(f"  {status} {term}")
        print()
        
    except Exception as e:
        print(f"\n Test Failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main test function"""
    
    print("\n")
    print_line("=", 100)
    print("🧪 DOCLING PARSING TEST - See What Gets Extracted".center(100))
    print_line("=", 100)
    
    # Test files
    base_path = Path(__file__).parent
    test_files = [
        "/Users/apple/Downloads/financial_automation/test_data/invoice.csv",
        "/Users/apple/Downloads/financial_automation/test_data/Godaddy My Account _ BillingNOV 2024.pdf",
        "/Users/apple/Downloads/financial_automation/test_data/Invoice-FFDOJMBE-0001.pdf",
        "/Users/apple/Downloads/financial_automation/test_data/billing-invoice.xlsx",
        "/Users/apple/Downloads/financial_automation/test_data/namecheap-order- AUG 25.pdf",
    ]
    
    tested = 0
    for file_name in test_files:
        file_path = base_path / file_name
        
        if file_path.exists():
            test_file_parsing(str(file_path))
            tested += 1
        else:
            print(f"\n⚠️  File not found: {file_name}")
    
    print("\n")
    print_line("=", 100)
    print(f" Tested {tested} files - Check output above to verify parsing accuracy".center(100))
    print_line("=", 100)
    print("\n")


if __name__ == "__main__":
    main()