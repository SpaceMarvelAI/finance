#!/usr/bin/env python3
"""
Create test invoices for AP aging report testing
"""
from data_layer.database.database_manager import get_database
from datetime import datetime, timedelta

db = get_database()
cursor = db.conn.cursor()

try:
    # Get the test company ID
    company_id = 'c3582256-2a1f-4aa2-9df8-ad4c159503ea'
    
    # Get a vendor to use
    cursor.execute("SELECT id FROM vendors WHERE company_id = %s LIMIT 1", (company_id,))
    vendor = cursor.fetchone()
    if not vendor:
        print("No vendors found for company, creating one...")
        cursor.execute("""
            INSERT INTO vendors (id, vendor_name, company_id) 
            VALUES (gen_random_uuid(), %s, %s)
            RETURNING id
        """, ('Test Vendor', company_id))
        vendor = cursor.fetchone()
    
    vendor_id = vendor[0]
    print(f"Using vendor: {vendor_id}")
    
    # Insert test invoices
    today = datetime.now().date()
    invoices_to_insert = [
        ('INV-001', today - timedelta(days=45), today - timedelta(days=15), 10000, 0, 10000),
        ('INV-002', today - timedelta(days=75), today - timedelta(days=45), 15000, 5000, 10000),
        ('INV-003', today - timedelta(days=120), today - timedelta(days=90), 20000, 0, 20000),
    ]
    
    for inv_num, inv_date, due_date, total, paid, outstanding in invoices_to_insert:
        cursor.execute("""
            INSERT INTO vendor_invoices 
            (id, invoice_number, invoice_date, due_date, vendor_id, company_id,
             subtotal_amount, tax_amount, total_amount, paid_amount, outstanding_amount,
             original_currency, exchange_rate, inr_amount, payment_status, payment_terms_days)
            VALUES 
            (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (inv_num, inv_date, due_date, vendor_id, company_id, 
              total*0.9, total*0.1, total, paid, outstanding,
              'INR', 1.0, total, 'Unpaid', 30))
    
    db.conn.commit()
    print(f"✓ Inserted {len(invoices_to_insert)} test invoices")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    db.conn.rollback()
finally:
    cursor.close()
