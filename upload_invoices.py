#!/usr/bin/env python3
"""
Working Upload Script - Parse AND Save to Database
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from processing_layer.document_processing.enhanced_ingestion_agent import EnhancedIngestionAgent
from data_layer.database.database_manager import DatabaseManager
from datetime import datetime


def upload_invoice(file_path):
    """Upload invoice - parse with Docling and save to database"""
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f" File not found: {file_path}")
        return False
    
    print(f"\n{'='*80}")
    print(f"UPLOADING: {file_path.name}")
    print(f"{'='*80}\n")
    
    try:
        # Step 1: Parse with EnhancedIngestionAgent
        print("[1/3] Parsing document...")
        
        agent = EnhancedIngestionAgent()
        state = {'file_path': str(file_path)}
        result = agent.execute(state)
        
        if result.get('error_message'):
            print(f"\n Parse failed: {result['error_message']}")
            return False
        
        parsed_data = result.get('parsed_data', {})
        text = parsed_data.get('text', '')
        
        print(f" Parsed: {len(text)} characters\n")
        
        # Step 2: Simple classification
        print("[2/3] Classifying document...")
        
        text_lower = text.lower()
        if any(w in text_lower for w in ['bill to', 'customer', 'sold to']):
            category = 'customer_invoice'
        else:
            category = 'vendor_invoice'
        
        # Extract vendor name (simple)
        vendor_name = None
        lines = text.split('\n')[:10] if text else []
        for line in lines:
            line = line.strip()
            if len(line) > 3 and line.lower() not in ['invoice', 'receipt', 'bill']:
                vendor_name = line[:100]
                break
        
        print(f"   Category: {category}")
        if vendor_name:
            print(f"   Vendor: {vendor_name}")
        print()
        
        # Step 3: Save to database
        print("[3/3] Saving to database...")
        
        db = DatabaseManager()
        
        document_data = {
            'company_id': 'spacemarvel_001',
            'file_name': file_path.name,
            'file_path': str(file_path),
            'category': category,
            'vendor_name': vendor_name,
            'grand_total': 0.0,
            'outstanding': 0.0,
            'parsed_data': parsed_data,
            'uploaded_at': datetime.now()
        }
        
        doc_id = db.insert_document(document_data)
        db.close()
        
        print(f" Saved: Document ID {doc_id}\n")
        
        print(f"{'='*80}")
        print(" UPLOAD COMPLETE")
        print(f"{'='*80}\n")
        
        return True
        
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("\nUsage: python upload_working.py <file_path>\n")
        sys.exit(1)
    
    upload_invoice(sys.argv[1])


if __name__ == '__main__':
    main()