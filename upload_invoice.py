#!/usr/bin/env python3

                print(f"    Error uploading invoice: {e}")
    """Upload invoices from CSV file (new schema)"""
    print(f"\n📄 Processing: {file_path}")
    try:
        from processing_layer.document_processing.parsers.csv_parser import CSVParser
        from data_layer.database.session import SessionLocal
        from sqlalchemy import text
        session = SessionLocal()
        parser = CSVParser()
        result = parser.parse(file_path)
        if not result or not result.get('invoices'):
            print(" No invoices found in file")
            return 0
        invoices = result['invoices']
        print(f"   Found {len(invoices)} invoices")
        # Get or create default company
        company_id = None
        company = session.execute(text("SELECT id FROM companies LIMIT 1")).scalar()
        if not company:
            session.execute(text("""
                INSERT INTO companies (id, name, currency) VALUES ('spacemarvel_001', 'METASPACE MARVEL AI PRIVATE LIMITED', 'USD')
            """))
            session.commit()
            company_id = 'spacemarvel_001'
        else:
            company_id = company
        uploaded_count = 0
        for inv_data in invoices:
            try:
                # Get or create vendor
                vendor_name = inv_data.get('vendor_name', 'Unknown')
                vendor_id = session.execute(text("SELECT id FROM vendors WHERE vendor_name=:name"), {"name": vendor_name}).scalar()
                if not vendor_id:
                    session.execute(text("""
                        INSERT INTO vendors (company_id, vendor_name, created_at, updated_at)
                        VALUES (:company_id, :vendor_name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """), {"company_id": company_id, "vendor_name": vendor_name})
                    session.commit()
                    vendor_id = session.execute(text("SELECT id FROM vendors WHERE vendor_name=:name"), {"name": vendor_name}).scalar()
                # Insert invoice into documents table
                session.execute(text("""
                    INSERT INTO documents (
                        company_id, file_name, file_type, document_number, document_date, category,
                        grand_total, tax_total, paid_amount, outstanding, vendor_name, vendor_id,
                        parsed_data, canonical_data, original_currency, original_amount, inr_amount, exchange_rate,
                        uploaded_at, processed_at, created_at, updated_at
                    ) VALUES (
                        :company_id, :file_name, :file_type, :document_number, :document_date, :category,
                        :grand_total, :tax_total, :paid_amount, :outstanding, :vendor_name, :vendor_id,
                        :parsed_data, :canonical_data, :original_currency, :original_amount, :inr_amount, :exchange_rate,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """), {
                    "company_id": company_id,
                    "file_name": inv_data.get('file_name', ''),
                    "file_type": inv_data.get('file_type', 'csv'),
                    "document_number": inv_data.get('invoice_number'),
                    "document_date": inv_data.get('invoice_date'),
                    "category": inv_data.get('category', 'vendor_invoice'),
                    "grand_total": inv_data.get('total_amount', 0),
                    "tax_total": inv_data.get('tax_total', 0),
                    "paid_amount": inv_data.get('paid_amount', 0),
                    "outstanding": inv_data.get('outstanding', inv_data.get('total_amount', 0)),
                    "vendor_name": vendor_name,
                    "vendor_id": vendor_id,
                    "parsed_data": json.dumps(inv_data),
                    "canonical_data": json.dumps({}),
                    "original_currency": inv_data.get('currency', 'USD'),
                    "original_amount": inv_data.get('total_amount', 0),
                    "inr_amount": inv_data.get('inr_amount', 0),
                    "exchange_rate": inv_data.get('exchange_rate', 1.0)
                })
                uploaded_count += 1
                print(f"    {inv_data.get('invoice_number')} - {vendor_name} - ${inv_data.get('total_amount', 0):,.2f}")
            except Exception as e:
                print(f"    Error uploading invoice: {e}")
                continue
        session.commit()
        session.close()
        print(f"\n Uploaded {uploaded_count} invoices")
        return uploaded_count
    except Exception as e:
        print(f" Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return 0
                continue
        
        # Commit all
        session.commit()
        session.close()
        
        print(f"\n Uploaded {uploaded_count} invoices")
        return uploaded_count
        
    except Exception as e:
        print(f" Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return 0


def upload_from_pdf(file_path):
    """Upload invoice from a PDF file using EnhancedIngestionAgent"""
    print(f"\n📄 Processing PDF: {file_path}")
    try:
        from processing_layer.document_processing.enhanced_ingestion_agent import EnhancedIngestionAgent
        agent = EnhancedIngestionAgent()
        result = agent.process_document(file_path)
        if result and result.get('success'):
            print(f"    Uploaded: {file_path}")
            return 1
        else:
            print(f"    Failed to upload: {file_path}")
            return 0
    except Exception as e:
        print(f"    Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return 0


def upload_from_directory(directory):
    """Upload all invoices from a directory"""
    
    print(f"\n📁 Scanning directory: {directory}")
    
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f" Directory not found: {directory}")
        return 0
    
    # Find all invoice files
    csv_files = list(dir_path.glob('*.csv'))
    xlsx_files = list(dir_path.glob('*.xlsx'))
    pdf_files = list(dir_path.glob('*.pdf'))
    
    total_files = len(csv_files) + len(xlsx_files) + len(pdf_files)
    
    print(f"   Found {total_files} files:")
    print(f"   • CSV: {len(csv_files)}")
    print(f"   • Excel: {len(xlsx_files)}")
    print(f"   • PDF: {len(pdf_files)}")
    
    total_uploaded = 0
    
    # Process CSV files
    for csv_file in csv_files:
        count = upload_from_csv(str(csv_file))
        total_uploaded += count
    
    # PDF support using EnhancedIngestionAgent
    for pdf_file in pdf_files:
        count = upload_from_pdf(str(pdf_file))
        total_uploaded += count
    
    if xlsx_files:
        print(f"\n⚠️  Excel processing coming soon! For now, convert to CSV or use CSV upload")
    
    return total_uploaded


def create_sample_csv():
    """Create a sample invoice CSV for testing"""
    
    print("\n📝 Creating sample invoice CSV...")
    
    sample_data = """invoice_number,vendor_name,invoice_date,due_date,total_amount,paid_amount,payment_status,currency
INV-001,AWS,2025-12-01,2026-01-01,1500.00,0.00,unpaid,USD
INV-002,Google Cloud,2025-12-05,2026-01-05,2350.00,2350.00,paid,USD
INV-003,Microsoft Azure,2025-12-10,2026-01-10,3200.00,0.00,unpaid,USD
INV-004,AWS,2025-12-15,2026-01-15,1800.00,0.00,unpaid,USD
INV-005,Figma,2025-12-20,2026-01-20,450.00,450.00,paid,USD
INV-006,LinkedIn,2025-12-22,2026-01-22,980.00,0.00,unpaid,USD
INV-007,Namecheap,2025-12-25,2026-01-25,125.00,125.00,paid,USD
INV-008,GoDaddy,2025-12-28,2026-01-28,299.00,0.00,unpaid,USD"""
    
    output_file = Path('sample_invoices.csv')
    output_file.write_text(sample_data)
    
    print(f" Sample CSV created: {output_file}")
    print(f"   Contains 8 sample invoices")
    print(f"\n💡 Upload with:")
    print(f"   python upload_invoices.py sample_invoices.csv")
    
    return str(output_file)


def show_database_summary():
    """Show summary of what's in database"""
    
    print("\n" + "="*80)
    print("DATABASE SUMMARY")
    print("="*80)
    
    try:
        from data_layer.database.session import SessionLocal
        from data_layer.models.database_models import Invoice, Vendor, Payment
        
        session = SessionLocal()
        
        # Count records
        invoice_count = session.query(Invoice).count()
        vendor_count = session.query(Vendor).count()
        payment_count = session.query(Payment).count()
        
        print(f"\n📊 Current Database:")
        print(f"   Invoices: {invoice_count}")
        print(f"   Vendors: {vendor_count}")
        print(f"   Payments: {payment_count}")
        
        if invoice_count > 0:
            # Show totals
            from sqlalchemy import func
            total = session.query(func.sum(Invoice.total_amount)).scalar() or 0
            paid = session.query(func.sum(Invoice.paid_amount)).scalar() or 0
            outstanding = total - paid
            
            print(f"\n💰 Financial Summary:")
            print(f"   Total Amount: ${total:,.2f}")
            print(f"   Paid Amount: ${paid:,.2f}")
            print(f"   Outstanding: ${outstanding:,.2f}")
            
            # Show by status
            statuses = session.query(
                Invoice.payment_status, 
                func.count(Invoice.id)
            ).group_by(Invoice.payment_status).all()
            
            print(f"\n📋 By Status:")
            for status, count in statuses:
                print(f"   {status}: {count}")
        
        session.close()
        
    except Exception as e:
        print(f" Error: {e}")


def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload invoices to database')
    parser.add_argument('file', nargs='?', help='CSV file to upload')
    parser.add_argument('--directory', '-d', help='Upload all files from directory')
    parser.add_argument('--sample', action='store_true', help='Create sample CSV file')
    parser.add_argument('--summary', action='store_true', help='Show database summary')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("INVOICE UPLOAD SYSTEM")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    if args.sample:
        csv_file = create_sample_csv()
        print(f"\n💡 Now upload it:")
        print(f"   python upload_invoices.py {csv_file}")
        return
    
    if args.summary:
        show_database_summary()
        return
    
    if args.directory:
        uploaded = upload_from_directory(args.directory)
        print(f"\n Total uploaded: {uploaded} invoices")
    elif args.file:
        ext = Path(args.file).suffix.lower()
        if ext == '.csv':
            uploaded = upload_from_csv(args.file)
        elif ext == '.pdf':
            uploaded = upload_from_pdf(args.file)
        else:
            print(f" Unsupported file type: {ext}")
            return
    else:
        print("\n📋 Usage:")
        print("   python upload_invoices.py file.csv          # Upload single CSV")
        print("   python upload_invoices.py -d ./data/uploads # Upload from directory")
        print("   python upload_invoices.py --sample          # Create sample CSV")
        print("   python upload_invoices.py --summary         # Show database summary")
        return
    
    # Show summary after upload
    if args.file or args.directory:
        show_database_summary()
        
        print("\n💡 Next: Generate reports!")
        print("   python generate_reports.py --interactive")
    
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    main()