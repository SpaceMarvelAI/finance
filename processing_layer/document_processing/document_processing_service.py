"""
Enhanced Document Upload and Processing Service
Handles complete workflow: Upload -> Parse -> Classify -> Extract -> Store
"""

from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import psycopg2.extras

from processing_layer.document_processing.document_processor import (
    DocumentClassifier,
    IntelligentExtractor,
    MasterDataManager,
    DocumentType
)
import json 


class DocumentProcessingService:
    """
    Complete document processing pipeline
    
    Workflow:
    1. Upload file
    2. Parse with Docling
    3. Classify document type
    4. Extract structured data
    5. Create/update master data (vendors, customers)
    6. Store in appropriate tables
    7. Return processing result
    """
    
    def __init__(self, db_session, docling_parser, company_id: str, user_company_name: str = None):
        self.db = db_session
        self.docling_parser = docling_parser
        self.company_id = company_id
        self.user_company_name = user_company_name  # For intelligent classification
        
        # Initialize components
        self.classifier = DocumentClassifier()
        self.extractor = IntelligentExtractor()
        self.master_data_manager = MasterDataManager(db_session)
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        # Try multiple date formats
        date_formats = [
            '%m/%d/%Y',          # 8/15/2025
            '%d/%m/%Y',          # 15/8/2025
            '%Y-%m-%d',          # 2025-08-15
            '%d-%m-%Y',          # 16-07-2025
            '%B %d, %Y',         # August 20, 2025
            '%d %B %Y',          # 20 August 2025
            '%b %d, %Y',         # Aug 20, 2025
            '%d %b %Y',          # 20 Aug 2025
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        print(f"   ⚠️ Could not parse date: {date_str}")
        return None
    
    def _calculate_due_date(self, invoice_date: Optional[datetime], payment_terms_days: int = 30) -> Optional[datetime]:
        """Calculate due date from invoice date and payment terms"""
        if not invoice_date:
            return None
        
        return invoice_date + timedelta(days=payment_terms_days)
    
    def _convert_to_inr(self, amount: float, currency: str, invoice_date: Optional[datetime] = None) -> float:
        """Convert amount to INR using live exchange rates"""
        if currency == "INR":
            return amount
        
        try:
            from shared.utils.live_exchange_rates import get_rate_provider
            
            rate_provider = get_rate_provider()
            date_str = invoice_date.strftime('%Y-%m-%d') if invoice_date else datetime.now().strftime('%Y-%m-%d')
            
            # Convert using live rates
            inr_amount = rate_provider.convert(amount, currency, date_str)
            
            print(f"   💱 Converted {currency} {amount:.2f} → INR ₹{inr_amount:.2f}")
            
            return inr_amount
            
        except Exception as e:
            print(f"   ⚠️ Currency conversion failed: {e}, using fallback")
            
            # Fallback to static rates
            try:
                from shared.utils.currency_converter import CurrencyConverter
                converter = CurrencyConverter()
                date_str = invoice_date.strftime('%Y-%m-%d') if invoice_date else datetime.now().strftime('%Y-%m-%d')
                return converter.convert(amount, currency, 'INR', date_str)
            except:
                print(f"   ⚠️ All conversion methods failed, returning original amount")
                return amount
    
    def _save_transaction(
            self,
            doc_type: DocumentType,
            document_id: str,
            extracted_data: Dict,
            master_data_ids: Dict[str, str]
        ) -> Optional[str]:
            """Save to transaction table - WORKING VERSION"""
            
            target_table = extracted_data.get("target_table")
            fields = extracted_data.get("extracted_fields", {})
            
            if not target_table:
                return None
            
            transaction_id = str(uuid.uuid4())
            
            # Extract amounts
            total_amount = float(fields.get("total_amount", 0) or 0)
            tax_amount = float(fields.get("tax_amount", 0) or 0)
            paid_amount = float(fields.get("paid_amount", 0) or 0)
            
            subtotal = total_amount - tax_amount if tax_amount else total_amount
            outstanding = total_amount - paid_amount
            
            currency = fields.get("currency", "INR")
            
            # Parse date
            invoice_date = None
            invoice_date_str = fields.get("invoice_date")
            if invoice_date_str:
                for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y']:
                    try:
                        invoice_date = datetime.strptime(invoice_date_str, fmt)
                        break
                    except:
                        continue
            
            payment_terms = int(fields.get("payment_terms_days") or 30)
            due_date = (invoice_date + timedelta(days=payment_terms)) if invoice_date else None
            
            # Convert currency
            if currency != "INR" and total_amount > 0:
                try:
                    from shared.utils.live_exchange_rates import get_rate_provider
                    rate_provider = get_rate_provider()
                    date_str = invoice_date.strftime('%Y-%m-%d') if invoice_date else None
                    inr_amount = rate_provider.convert(total_amount, currency, date_str)
                    exchange_rate = inr_amount / total_amount if total_amount > 0 else 1.0
                    print(f"   💱 Converted {currency} {total_amount:.2f} → INR ₹{inr_amount:.2f}")
                except Exception as e:
                    print(f"   ⚠️ Conversion failed: {e}")
                    inr_amount = total_amount
                    exchange_rate = 1.0
            else:
                inr_amount = total_amount
                exchange_rate = 1.0
            
            cursor = self.db.conn.cursor()
            
            try:
                # Get line items if they exist
                line_items = fields.get("line_items")
                line_items_json = json.dumps(line_items) if line_items else None
                
                if target_table == "vendor_invoices":
                    print(f"   💾 Saving to vendor_invoices...")
                    
                    cursor.execute("""
                        INSERT INTO vendor_invoices (
                            id, company_id, vendor_id, document_id,
                            invoice_number, invoice_date, due_date,
                            subtotal_amount, tax_amount, total_amount,
                            paid_amount, outstanding_amount,
                            original_currency, exchange_rate, inr_amount,
                            payment_status, payment_terms_days, line_items
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        transaction_id, self.company_id, master_data_ids.get("vendor_id"),
                        document_id, fields.get("invoice_number"), invoice_date, due_date,
                        subtotal, tax_amount, total_amount, paid_amount, outstanding,
                        currency, exchange_rate, inr_amount,
                        "unpaid" if outstanding > 0 else "paid", payment_terms, line_items_json
                    ))
                    
                    self.db.conn.commit()
                    print(f"   ✅ Saved: {currency} {total_amount:.2f} = INR ₹{inr_amount:.2f}")
                    if line_items:
                        print(f"   📦 Line items: {len(line_items)} items saved")
                
                elif target_table == "customer_invoices":
                    print(f"   💾 Saving to customer_invoices...")
                    
                    # Ensure invoice_number is not null
                    invoice_number = fields.get("invoice_number") or f"DOC-{transaction_id[:8]}"
                    
                    cursor.execute("""
                        INSERT INTO customer_invoices (
                            id, company_id, customer_id, document_id,
                            invoice_number, invoice_date, due_date,
                            subtotal_amount, tax_amount, total_amount,
                            received_amount, outstanding_amount,
                            original_currency, exchange_rate, inr_amount,
                            payment_status, payment_terms_days, line_items
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        transaction_id, self.company_id, master_data_ids.get("customer_id"),
                        document_id, invoice_number, invoice_date, due_date,
                        subtotal, tax_amount, total_amount, paid_amount, outstanding,
                        currency, exchange_rate, inr_amount,
                        "unpaid" if outstanding > 0 else "paid", payment_terms, line_items_json
                    ))
                    
                    self.db.conn.commit()
                    print(f"   ✅ Saved: {currency} {total_amount:.2f} = INR ₹{inr_amount:.2f}")
                    if line_items:
                        print(f"   📦 Line items: {len(line_items)} items saved")
                
                cursor.close()
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.db.conn.rollback()
                import traceback
                traceback.print_exc()
                return None
            
            return transaction_id
    
    def _classify_invoice(self, extracted_data: Dict, docling_output: Dict) -> Dict:
        """
        Intelligent invoice classification
        Determines if invoice is PURCHASE (vendor invoice) or SALES (customer invoice)
        """
        
        classification = {
            "category": "unknown",
            "party_info": {
                "name": None,
                "type": None,
                "confidence": 0.0,
                "reasoning": "Cannot determine - missing information"
            }
        }
        
        if not self.user_company_name:
            return classification
        
        fields = extracted_data.get("extracted_fields", {})
        vendor_name = fields.get("vendor_name", "")
        customer_name = fields.get("customer_name", "")
        
        # Get company aliases
        company_aliases = self.db.get_company_aliases(self.company_id)
        print(f"\n🏢 COMPANY ALIASES: {company_aliases}")
        
        company_names_to_check = [self.user_company_name] + company_aliases
        
        print(f"\n🔍 INTELLIGENT CLASSIFICATION:")
        print(f"   User Company: {self.user_company_name}")
        print(f"   Company Aliases: {company_aliases}")
        print(f"   Vendor Name: {vendor_name}")
        print(f"   Customer Name: {customer_name}")
        
        # Check if user's company is vendor or customer
        is_user_vendor = any(
            alias.upper() in vendor_name.upper() 
            for alias in company_names_to_check 
            if alias and vendor_name
        )
        
        is_user_customer = any(
            alias.upper() in customer_name.upper() 
            for alias in company_names_to_check 
            if alias and customer_name
        )
        
        if is_user_vendor:
            # User company is the vendor → SALES invoice
            classification["category"] = "sales"
            classification["party_info"] = {
                "name": customer_name,
                "type": "customer",
                "confidence": 0.9,
                "reasoning": f"User company '{vendor_name}' is the vendor, making this a sale"
            }
            print(f"   🎯 SALES - {vendor_name} is selling to {customer_name}")
        
        elif is_user_customer:
            # User company is the customer → PURCHASE invoice
            classification["category"] = "purchase"
            classification["party_info"] = {
                "name": vendor_name,
                "type": "vendor",
                "confidence": 0.9,
                "reasoning": f"User company '{customer_name}' is the customer, making this a purchase"
            }
            print(f"   🎯 PURCHASE - {vendor_name} is selling to {customer_name}")
        
        else:
            # Fallback logic
            if vendor_name and not customer_name:
                classification["category"] = "purchase"
                classification["party_info"]["name"] = vendor_name
                classification["party_info"]["type"] = "vendor"
            elif customer_name and not vendor_name:
                classification["category"] = "sales"
                classification["party_info"]["name"] = customer_name
                classification["party_info"]["type"] = "customer"
        
        return classification
    
    def process_upload(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """
        Process uploaded document through complete pipeline
        FIXED VERSION - Updates target table based on classification
        """
        
        result = {
            "success": False,
            "document_id": None,
            "document_type": None,
            "extracted_data": None,
            "errors": [],
            "warnings": [],
        }
        
        try:
            # Step 1: Parse document
            print(f"[1/7] Parsing document...")
            docling_output = self._parse_document(file_path)
            
            if not docling_output:
                result["errors"].append("Failed to parse document")
                return result
            
            # Step 2: Classify document type
            print(f"\n[2/7] Classifying document type...")
            doc_type = self.classifier.classify(docling_output, file_name)
            result["document_type"] = doc_type.value
            print(f"    Classification: {doc_type.value}")
            
            # Step 3: Extract structured data
            print(f"\n[3/7] Extracting data for {doc_type.value}...")
            extracted = self.extractor.extract(doc_type, docling_output)
            result["extracted_data"] = extracted
            
            print(f"\n📊 EXTRACTION RESULTS:")
            print(f"   Target table: {extracted.get('target_table')}")
            print(f"   Extracted fields: {list(extracted.get('extracted_fields', {}).keys())}")
            print(f"   Confidence: {extracted.get('confidence', 0):.2%}")
            
            # Step 4: Intelligent Invoice Classification
            print(f"\n[4/7] Intelligent invoice classification...")
            invoice_classification = self._classify_invoice(extracted, docling_output)
            result["invoice_category"] = invoice_classification.get("category", "unknown")
            result["party_info"] = invoice_classification.get("party_info", {})
            
            # ✅ FIX: Update target table based on classification
            if result["invoice_category"] == "sales":
                extracted["target_table"] = "customer_invoices"
                extracted["master_data_needed"] = ["customer"]
                print(f"   ✅ Updated target_table to: customer_invoices")
            elif result["invoice_category"] == "purchase":
                extracted["target_table"] = "vendor_invoices"
                extracted["master_data_needed"] = ["vendor"]
                print(f"   ✅ Updated target_table to: vendor_invoices")
            
            extracted["category"] = result["invoice_category"]
            
            print(f"   Category: {result['invoice_category']}")
            print(f"   Party: {result['party_info'].get('name')} ({result['party_info'].get('type')})")
            
            # Step 5: Save document record
            print(f"\n[5/7] Saving document to database...")
            document_id = self._save_document(
                file_name=file_name,
                file_path=file_path,
                doc_type=doc_type,
                docling_output=docling_output,
                extracted_data=extracted
            )
            result["document_id"] = document_id
            print(f"    Saved to database: {document_id}")
            
            # Step 6: Handle master data
            print(f"\n[6/7] Processing master data...")
            master_data_ids = self._process_master_data(extracted)
            
            # Step 7: Save to transaction table (NOW ACTUALLY WORKS!)
            print(f"\n[7/7] Saving to {extracted.get('target_table')}...")
            transaction_id = self._save_transaction(
                doc_type=doc_type,
                document_id=document_id,
                extracted_data=extracted,
                master_data_ids=master_data_ids
            )
            
            result["transaction_id"] = transaction_id
            result["success"] = True
            
            print(f"\n✅ Document processed successfully!")
            print(f"   Type: {doc_type.value}")
            print(f"   Category: {result['invoice_category']}")
            print(f"   Document ID: {document_id}")
            print(f"   Transaction ID: {transaction_id}")
            
        except Exception as e:
            result["errors"].append(str(e))
            print(f"❌ Error processing document: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def _parse_document(self, file_path: str) -> Optional[Dict]:
        """Parse document with Docling"""
        try:
            print(f"\n{'='*80}")
            print(f"📄 DOCLING PARSER - Processing: {Path(file_path).name}")
            print(f"{'='*80}")
            
            parsed = self.docling_parser.parse(file_path)
            
            if parsed:
                print(f"\n✅ Docling parsing completed")
                if isinstance(parsed, dict) and 'text' in parsed:
                    print(f"   Extracted {len(parsed.get('text', ''))} characters")
            else:
                print(f"\n⚠️ Docling returned None")
            
            print(f"{'='*80}\n")
            
            return parsed
            
        except Exception as e:
            print(f"\n❌ Error parsing document: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_document(
        self,
        file_name: str,
        file_path: str,
        doc_type: DocumentType,
        docling_output: Dict,
        extracted_data: Dict
    ) -> str:
        """Save document record to documents table"""
        
        fields = extracted_data.get("extracted_fields", {})
        
        # Prepare document data
        document_data = {
            "company_id": self.company_id,
            "file_name": file_name,
            "file_path": file_path,
            "document_number": fields.get("invoice_number", ""),
            "document_date": fields.get("invoice_date", ""),
            "category": extracted_data.get("category", ""),
            "vendor_name": fields.get("vendor_name", ""),
            "customer_name": fields.get("customer_name", ""),
            "grand_total": fields.get("total_amount", 0.0),
            "tax_total": fields.get("tax_amount", 0.0),
            "paid_amount": fields.get("paid_amount", 0.0),
            "detected_currency": fields.get("currency", "INR"),
            "parsed_data": docling_output,
            "canonical_data": extracted_data
        }
        
        # Insert into database
        document_id = self.db.insert_document(document_data)
        
        return document_id
    
    def _process_master_data(self, extracted_data: Dict) -> Dict[str, str]:
        """Process master data (vendors, customers)"""
        
        master_data_ids = {}
        master_data_needed = extracted_data.get("master_data_needed", [])
        fields = extracted_data.get("extracted_fields", {})
        
        if "vendor" in master_data_needed:
            vendor_name = fields.get("vendor_name")
            if vendor_name:
                vendor_id = self.master_data_manager.create_or_get_vendor(
                    company_id=self.company_id,
                    vendor_name=vendor_name
                )
                master_data_ids["vendor_id"] = vendor_id
                print(f"   📇 Vendor: {vendor_name} ({vendor_id})")
        
        if "customer" in master_data_needed:
            customer_name = fields.get("customer_name")
            if customer_name:
                customer_id = self.master_data_manager.create_or_get_customer(
                    company_id=self.company_id,
                    customer_name=customer_name
                )
                master_data_ids["customer_id"] = customer_id
                print(f"   📇 Customer: {customer_name} ({customer_id})")
        
        return master_data_ids

# ============================================================================
# QUERY SERVICE
# ============================================================================

class QueryService:
    """
    Intelligent query service
    Determines which data to retrieve based on user query
    """
    
    def __init__(self, db_session, company_id: str):
        self.db = db_session
        self.company_id = company_id
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process user query and return relevant data
        
        Examples:
        - "Show me all unpaid vendor invoices"
        - "What's my AP aging?"
        - "List all bank transactions from last month"
        - "Show me purchase orders for Vendor ABC"
        """
        
        query_lower = user_query.lower()
        
        # Determine intent
        if any(word in query_lower for word in ["ap aging", "accounts payable aging", "vendor aging"]):
            return self._get_ap_aging()
        
        elif any(word in query_lower for word in ["ar aging", "accounts receivable aging", "customer aging"]):
            return self._get_ar_aging()
        
        elif any(word in query_lower for word in ["unpaid", "outstanding"]) and "vendor" in query_lower:
            return self._get_unpaid_vendor_invoices()
        
        elif any(word in query_lower for word in ["unpaid", "outstanding"]) and "customer" in query_lower:
            return self._get_unpaid_customer_invoices()
        
        elif "bank" in query_lower and "transaction" in query_lower:
            return self._get_bank_transactions()
        
        elif "purchase order" in query_lower:
            return self._get_purchase_orders()
        
        elif "expense" in query_lower:
            return self._get_expenses()
        
        else:
            return {
                "error": "Could not determine query intent",
                "suggestion": "Try queries like: 'Show AP aging', 'List unpaid invoices', 'Show bank transactions'"
            }
    
    def _get_ap_aging(self) -> Dict[str, Any]:
        """Get AP aging report data"""
        # Query vendor_invoices table
        # Group by aging buckets
        return {"report_type": "ap_aging", "data": []}
    
    def _get_ar_aging(self) -> Dict[str, Any]:
        """Get AR aging report data"""
        # Query customer_invoices table
        return {"report_type": "ar_aging", "data": []}
    
    def _get_unpaid_vendor_invoices(self) -> Dict[str, Any]:
        """Get unpaid vendor invoices"""
        # Query vendor_invoices where payment_status = 'unpaid'
        return {"report_type": "unpaid_vendor_invoices", "data": []}
    
    def _get_unpaid_customer_invoices(self) -> Dict[str, Any]:
        """Get unpaid customer invoices"""
        return {"report_type": "unpaid_customer_invoices", "data": []}
    
    def _get_bank_transactions(self) -> Dict[str, Any]:
        """Get bank transactions"""
        return {"report_type": "bank_transactions", "data": []}
    
    def _get_purchase_orders(self) -> Dict[str, Any]:
        """Get purchase orders"""
        return {"report_type": "purchase_orders", "data": []}
    
    def _get_expenses(self) -> Dict[str, Any]:
        """Get expense bills"""
        return {"report_type": "expenses", "data": []}