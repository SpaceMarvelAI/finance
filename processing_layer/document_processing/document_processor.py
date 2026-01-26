"""
Intelligent Document Classifier and Extractor
Automatically identifies document type and extracts relevant data
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import re
from enum import Enum
import json
import psycopg2
import psycopg2.extras
import uuid
class DocumentType(Enum):
    """Document types"""
    VENDOR_INVOICE = "vendor_invoice"
    CUSTOMER_INVOICE = "customer_invoice"
    PURCHASE_ORDER = "purchase_order"
    SALES_ORDER = "sales_order"
    BANK_STATEMENT = "bank_statement"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    EXPENSE_BILL = "expense_bill"
    RECEIPT = "receipt"
    UNKNOWN = "unknown"


class DocumentClassifier:
    """
    Intelligently classifies documents based on content
    Uses keywords, patterns, and structure analysis
    """
    
    # Classification rules
    CLASSIFICATION_RULES = {
        DocumentType.VENDOR_INVOICE: {
            "keywords": ["invoice", "bill", "payable", "vendor", "supplier", "purchase", "receipt", "order"],
            "patterns": [
                r"vendor\s*invoice",
                r"bill\s*to",
                r"accounts\s*payable",
                r"payment\s*terms",
                r"receipt",
                r"order\s*#",
                r"order\s*date",
            ],
            "indicators": ["seller", "buyer", "due_date", "invoice_number", "order_number", "receipt_number"]
        },
        DocumentType.CUSTOMER_INVOICE: {
            "keywords": ["invoice", "bill", "receivable", "customer", "sales"],
            "patterns": [
                r"sales\s*invoice",
                r"invoice\s*to",
                r"accounts\s*receivable",
            ],
            "indicators": ["customer", "bill_to", "invoice_number"]
        },
        DocumentType.PURCHASE_ORDER: {
            "keywords": ["purchase order", "PO", "requisition"],
            "patterns": [
                r"purchase\s*order",
                r"PO\s*#?\s*\d+",
            ],
            "indicators": ["po_number", "order_date", "delivery_date"]
        },
        DocumentType.SALES_ORDER: {
            "keywords": ["sales order", "SO", "order confirmation"],
            "patterns": [
                r"sales\s*order",
                r"SO\s*#?\s*\d+",
                r"order\s*confirmation",
            ],
            "indicators": ["so_number", "customer", "ship_to"]
        },
        DocumentType.BANK_STATEMENT: {
            "keywords": ["bank statement", "account statement", "transaction history"],
            "patterns": [
                r"bank\s*statement",
                r"account\s*number",
                r"opening\s*balance",
                r"closing\s*balance",
            ],
            "indicators": ["account_number", "transactions", "balance"]
        },
        DocumentType.CREDIT_NOTE: {
            "keywords": ["credit note", "credit memo", "refund"],
            "patterns": [
                r"credit\s*note",
                r"credit\s*memo",
                r"refund",
            ],
            "indicators": ["reference_invoice", "credit_amount"]
        },
        DocumentType.DEBIT_NOTE: {
            "keywords": ["debit note", "debit memo", "charge"],
            "patterns": [
                r"debit\s*note",
                r"debit\s*memo",
            ],
            "indicators": ["reference_invoice", "debit_amount"]
        },
        DocumentType.EXPENSE_BILL: {
            "keywords": ["receipt", "expense", "reimbursement", "bill"],
            "patterns": [
                r"receipt",
                r"expense\s*report",
                r"reimbursement",
            ],
            "indicators": ["merchant", "total", "date"]
        },
    }
    
    def classify(self, docling_output: Dict[str, Any], file_name: str = "") -> DocumentType:
        """
        Classify document based on Docling parsed output
        
        Args:
            docling_output: Parsed output from Docling
            file_name: Original filename
            
        Returns:
            DocumentType enum
        """
        
        # Extract text content from Docling output
        text_content = self._extract_text(docling_output)
        text_lower = text_content.lower()
        
        # Score each document type
        scores = {}
        
        for doc_type, rules in self.CLASSIFICATION_RULES.items():
            score = 0
            
            # Check keywords
            for keyword in rules["keywords"]:
                if keyword.lower() in text_lower:
                    score += 2
            
            # Check patterns
            for pattern in rules["patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 3
            
            # Check indicators in structure
            for indicator in rules["indicators"]:
                if self._has_indicator(docling_output, indicator):
                    score += 5
            
            # Filename hints
            if file_name:
                for keyword in rules["keywords"]:
                    if keyword.lower() in file_name.lower():
                        score += 1
            
            scores[doc_type] = score
        
        # Return highest scoring type
        if scores:
            best_match = max(scores, key=scores.get)
            if scores[best_match] > 5:  # Minimum confidence threshold
                return best_match
        
        return DocumentType.UNKNOWN
    
    def _extract_text(self, docling_output: Dict) -> str:
        """Extract all text from Docling output"""
        text_parts = []
        
        if isinstance(docling_output, dict):
            for key, value in docling_output.items():
                if isinstance(value, str):
                    text_parts.append(value)
                elif isinstance(value, (list, dict)):
                    text_parts.append(self._extract_text(value))
        elif isinstance(docling_output, list):
            for item in docling_output:
                text_parts.append(self._extract_text(item))
        elif isinstance(docling_output, str):
            text_parts.append(docling_output)
        
        return " ".join(text_parts)
    
    def _has_indicator(self, docling_output: Dict, indicator: str) -> bool:
        """Check if indicator field exists in parsed output"""
        if isinstance(docling_output, dict):
            if indicator in docling_output:
                return True
            for value in docling_output.values():
                if self._has_indicator(value, indicator):
                    return True
        return False


class IntelligentExtractor:
    """
    Extracts relevant data based on document type
    HYBRID APPROACH: Regex first (fast, free), LLM fallback (smart, expensive)
    """
    
    # Field extraction rules for each document type
    EXTRACTION_RULES = {
        DocumentType.VENDOR_INVOICE: {
            "target_table": "vendor_invoices",
            "master_data": ["vendor"],
            "required_fields": {
                "invoice_number": ["document_metadata.document_number", "invoice_no", "invoice_number"],
                "invoice_date": ["document_metadata.document_date", "invoice_date", "date"],
                "vendor_name": ["seller.name", "vendor.name", "from"],
                "total_amount": ["totals.grand_total", "total", "amount_due"],
                "tax_amount": ["totals.tax_total", "tax", "vat"],
            },
            "optional_fields": {
                "due_date": ["payment_terms.due_date", "due_date"],
                "subtotal": ["totals.subtotal", "subtotal"],
                "paid_amount": ["totals.amount_paid", "paid"],
                "line_items": ["line_items"],
                "po_number": ["purchase_order", "po_number"],
            }
        },
        
        DocumentType.CUSTOMER_INVOICE: {
            "target_table": "customer_invoices",
            "master_data": ["customer"],
            "required_fields": {
                "invoice_number": ["document_metadata.document_number"],
                "invoice_date": ["document_metadata.document_date"],
                "customer_name": ["buyer.name", "customer.name", "bill_to"],
                "total_amount": ["totals.grand_total"],
            },
            "optional_fields": {
                "due_date": ["payment_terms.due_date"],
                "tax_amount": ["totals.tax_total"],
                "line_items": ["line_items"],
            }
        },
        
        DocumentType.PURCHASE_ORDER: {
            "target_table": "purchase_orders",
            "master_data": ["vendor"],
            "required_fields": {
                "po_number": ["po_number", "order_number"],
                "po_date": ["order_date", "date"],
                "vendor_name": ["vendor.name", "supplier"],
                "total_amount": ["total", "order_total"],
            },
            "optional_fields": {
                "expected_delivery_date": ["delivery_date"],
                "line_items": ["items"],
            }
        },
        
        DocumentType.BANK_STATEMENT: {
            "target_table": "bank_transactions",
            "master_data": ["bank_account"],
            "required_fields": {
                "account_number": ["account_number", "account"],
            },
            "optional_fields": {
                "transactions": ["transactions", "entries"],
                "opening_balance": ["opening_balance"],
                "closing_balance": ["closing_balance"],
            }
        },
        
        DocumentType.EXPENSE_BILL: {
            "target_table": "expense_bills",
            "master_data": [],
            "required_fields": {
                "bill_date": ["date", "transaction_date"],
                "total_amount": ["total", "amount"],
                "vendor_name": ["merchant", "vendor", "from"],
            },
            "optional_fields": {
                "bill_number": ["receipt_number", "transaction_id"],
                "category": ["category"],
            }
        },
    }
    
    def __init__(self):
        """Initialize with LLM client for intelligent extraction"""
        self.llm = None
        self.llm_calls = 0
        self.max_llm_calls_per_hour = 100
        
        try:
            from shared.llm.groq_client import GroqClient
            self.llm = GroqClient()
            print(" LLM available for intelligent extraction")
        except Exception as e:
            print(f"âš ï¸  LLM not available: {e}")
            print("   Will use regex-only extraction")
    
    def extract(self, doc_type: DocumentType, docling_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data based on document type
        
        Args:
            doc_type: Classified document type
            docling_output: Parsed Docling output
            
        Returns:
            Structured data ready for database insertion
        """
        
        # Log the parsed Docling output for debugging
        print(f"\n🔍 DOCling Parsed Output:")
        print(f"   Type: {type(docling_output)}")
        print(f"   Keys: {list(docling_output.keys()) if isinstance(docling_output, dict) else 'Not a dict'}")
        if isinstance(docling_output, dict):
            text_content = docling_output.get('text', '')
            print(f"   Text length: {len(text_content)} chars")
            print(f"   First 5000 chars: {text_content[:5000]}")
            print(f"   Metadata: {docling_output.get('metadata', {})}")
        
        if doc_type not in self.EXTRACTION_RULES:
            return {"error": f"No extraction rules for {doc_type}"}
        
        rules = self.EXTRACTION_RULES[doc_type]
        extracted_data = {
            "document_type": doc_type.value,
            "target_table": rules["target_table"],
            "master_data_needed": rules["master_data"],
            "extracted_fields": {},
            "missing_required_fields": [],
            "confidence": 1.0,
        }
        
        # Try structured extraction first
        for field_name, possible_paths in rules["required_fields"].items():
            value = self._find_value(docling_output, possible_paths)
            if value is not None:
                extracted_data["extracted_fields"][field_name] = value
            else:
                extracted_data["missing_required_fields"].append(field_name)
                extracted_data["confidence"] *= 0.8
        
        # If structured extraction failed, try text-based extraction
        if extracted_data["missing_required_fields"]:
            print(f"\nðŸ”„ Structured extraction incomplete, trying text-based extraction...")
            text = docling_output.get("text", "")
            if text:
                text_extracted = self._extract_from_text(text, doc_type)
                for field, value in text_extracted.items():
                    # Add ALL extracted fields, not just missing ones
                    if value is not None:
                        extracted_data["extracted_fields"][field] = value
                        if field in extracted_data["missing_required_fields"]:
                            extracted_data["missing_required_fields"].remove(field)
                        print(f"    Extracted {field}: {value}")
        
        # Extract optional fields
        for field_name, possible_paths in rules.get("optional_fields", {}).items():
            value = self._find_value(docling_output, possible_paths)
            if value is not None:
                extracted_data["extracted_fields"][field_name] = value
        
        return extracted_data
    
    def _extract_line_items(self, text: str, doc_type: DocumentType) -> List[Dict[str, Any]]:
        """
        Extract line items from invoice text using multiple approaches
        
        Returns:
            List of line item dictionaries with: description, quantity, unit_price, amount
        """
        line_items = []
        
        # Approach 1: Table-based extraction (most reliable)
        table_items = self._extract_table_line_items(text)
        if table_items:
            line_items.extend(table_items)
            print(f"   📊 Found {len(table_items)} items in table format")
        
        # Approach 2: Text-based extraction for simple invoices
        if not table_items:
            text_items = self._extract_text_line_items(text)
            if text_items:
                line_items.extend(text_items)
                print(f"   📝 Found {len(text_items)} items in text format")
        
        # Approach 3: LLM fallback for complex formats
        if not line_items and self.llm and self._can_use_llm():
            try:
                llm_items = self._extract_llm_line_items(text, doc_type)
                if llm_items:
                    line_items.extend(llm_items)
                    print(f"   🤖 Found {len(llm_items)} items via LLM")
                    self.llm_calls += 1
            except Exception as e:
                print(f"   ⚠️ LLM line item extraction failed: {str(e)[:50]}")
        
        # Clean and validate line items
        cleaned_items = []
        for item in line_items:
            cleaned_item = self._clean_line_item(item)
            if cleaned_item:
                cleaned_items.append(cleaned_item)
        
        return cleaned_items
    
    def _extract_table_line_items(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract line items from table format using regex patterns
        Handles various table formats: | Description | Qty | Price | Amount |
        """
        items = []
        
        # Pattern 1: Markdown-style tables with pipes
        table_pattern = r'\|\s*([^|]+?)\s*\|\s*([\d,]+(?:\.\d+)?)\s*\|\s*([₹$€]?\s*[\d,]+(?:\.\d+)?)\s*\|\s*([₹$€]?\s*[\d,]+(?:\.\d+)?)\s*\|'
        matches = re.findall(table_pattern, text, re.IGNORECASE)
        
        for match in matches:
            description, quantity, unit_price, amount = match
            
            # Clean values
            description = description.strip()
            quantity = self._clean_number(quantity)
            unit_price = self._clean_currency(unit_price)
            amount = self._clean_currency(amount)
            
            if description and quantity and unit_price and amount:
                # Validate that quantity * unit_price ≈ amount
                calculated = quantity * unit_price
                if abs(calculated - amount) < 0.5:  # Allow small rounding differences
                    items.append({
                        'description': description,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'amount': amount
                    })
        
        # Pattern 2: Simple tab-separated or space-separated tables
        if not items:
            # Look for lines with multiple numbers that could be qty, price, amount
            lines = text.split('\n')
            for line in lines:
                # Skip headers and totals
                if any(word in line.lower() for word in ['description', 'qty', 'quantity', 'price', 'amount', 'total', 'subtotal']):
                    continue
                
                # Look for patterns like: Description 1 100.00 100.00
                item_pattern = r'([A-Za-z][A-Za-z\s&,.]+?)\s+(\d+)\s+([₹$€]?\s*[\d,]+(?:\.\d+)?)\s+([₹$€]?\s*[\d,]+(?:\.\d+)?)'
                match = re.search(item_pattern, line, re.IGNORECASE)
                
                if match:
                    description, quantity, unit_price, amount = match.groups()
                    
                    description = description.strip()
                    quantity = self._clean_number(quantity)
                    unit_price = self._clean_currency(unit_price)
                    amount = self._clean_currency(amount)
                    
                    if description and quantity and unit_price and amount:
                        calculated = quantity * unit_price
                        if abs(calculated - amount) < 0.5:
                            items.append({
                                'description': description,
                                'quantity': quantity,
                                'unit_price': unit_price,
                                'amount': amount
                            })
        
        return items
    
    def _extract_text_line_items(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract line items from text format
        Handles formats like: "1 x Product Name @ $100.00 = $100.00"
        """
        items = []
        
        # Pattern for: Description x Quantity @ UnitPrice = Total
        patterns = [
            r'([A-Za-z][A-Za-z\s&,.]+?)\s*x\s*(\d+)\s*@\s*([₹$€]?\s*[\d,]+(?:\.\d+)?)\s*=\s*([₹$€]?\s*[\d,]+(?:\.\d+)?)',
            r'(\d+)\s*x\s*([A-Za-z][A-Za-z\s&,.]+?)\s*@\s*([₹$€]?\s*[\d,]+(?:\.\d+)?)\s*=\s*([₹$€]?\s*[\d,]+(?:\.\d+)?)',
            r'([A-Za-z][A-Za-z\s&,.]+?)\s*(\d+)\s*([₹$€]?\s*[\d,]+(?:\.\d+)?)\s*([₹$€]?\s*[\d,]+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) == 4:
                    # Pattern 1 & 2: Description x Qty @ Price = Total
                    if 'x' in pattern and '@' in pattern:
                        if 'x' in match[0]:  # First pattern
                            description, quantity, unit_price, amount = match
                        else:  # Second pattern
                            quantity, description, unit_price, amount = match
                    else:  # Third pattern: Description Qty Price Total
                        description, quantity, unit_price, amount = match
                    
                    description = description.strip()
                    quantity = self._clean_number(quantity)
                    unit_price = self._clean_currency(unit_price)
                    amount = self._clean_currency(amount)
                    
                    if description and quantity and unit_price and amount:
                        calculated = quantity * unit_price
                        if abs(calculated - amount) < 0.5:
                            items.append({
                                'description': description,
                                'quantity': quantity,
                                'unit_price': unit_price,
                                'amount': amount
                            })
        
        return items
    
    def _extract_llm_line_items(self, text: str, doc_type: DocumentType) -> List[Dict[str, Any]]:
        """
        Use LLM to extract line items from complex formats
        """
        prompt = f"""Extract line items from this invoice. Return ONLY valid JSON array.

Invoice text (first 3000 chars):
{text[:3000]}

Extract line items with these fields:
- description: Item description
- quantity: Quantity (number)
- unit_price: Unit price (number)
- amount: Total amount for this line (number)

Rules:
- Return ONLY JSON array, no markdown, no explanation
- Remove currency symbols and commas from numbers
- Return empty array if no line items found
- Be strict about validation: quantity * unit_price should equal amount

JSON:"""
        
        try:
            response = self.llm.generate(prompt)
            response_text = response.strip()
            
            # Clean response
            if '```' in response_text:
                lines = response_text.split('\n')
                response_text = '\n'.join([l for l in lines if not l.strip().startswith('```')])
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            items = json.loads(response_text)
            
            # Validate and clean items
            cleaned_items = []
            for item in items:
                if isinstance(item, dict):
                    cleaned_item = self._clean_line_item(item)
                    if cleaned_item:
                        cleaned_items.append(cleaned_item)
            
            return cleaned_items
            
        except Exception as e:
            print(f"   ⚠️ LLM line item extraction failed: {str(e)[:50]}")
            return []
    
    def _clean_line_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Clean and validate a line item
        """
        try:
            description = str(item.get('description', '')).strip()
            quantity = self._clean_number(item.get('quantity'))
            unit_price = self._clean_number(item.get('unit_price'))
            amount = self._clean_number(item.get('amount'))
            
            # Validate
            if not description or not quantity or not unit_price or not amount:
                return None
            
            if quantity <= 0 or unit_price <= 0 or amount <= 0:
                return None
            
            # Validate calculation
            calculated = quantity * unit_price
            if abs(calculated - amount) > 1.0:  # Allow small rounding differences
                return None
            
            return {
                'description': description,
                'quantity': float(quantity),
                'unit_price': float(unit_price),
                'amount': float(amount)
            }
            
        except:
            return None
    
    def _clean_number(self, value: Any) -> Optional[float]:
        """
        Clean and convert a value to float
        """
        if value is None:
            return None
        
        try:
            # Convert to string and clean
            val_str = str(value).replace(',', '').replace('₹', '').replace('$', '').replace('€', '').replace('£', '').strip()
            return float(val_str)
        except:
            return None
    
    def _clean_currency(self, value: Any) -> Optional[float]:
        """
        Clean currency string to float
        """
        if value is None:
            return None
        
        try:
            # Remove currency symbols and commas
            val_str = str(value).replace('₹', '').replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip()
            return float(val_str)
        except:
            return None
    
    def _extract_from_text(self, text: str, doc_type: DocumentType) -> Dict[str, Any]:
        """
        HYBRID EXTRACTION: Regex first (fast, free), LLM fallback (smart, expensive)
        
        Strategy:
        1. Try regex first (works for 80% of cases, instant, free)
        2. Check completeness
        3. If missing critical fields, use LLM (only when needed)
        4. Merge results
        """
        
        # STEP 1: Try regex first (fast, free)
        extracted = self._regex_extract_fields(text, doc_type)
        
        # STEP 2: Check completeness
        required_fields = self._get_required_fields(doc_type)
        missing_fields = [f for f in required_fields if f not in extracted or not extracted[f]]
        
        if not missing_fields:
            print(f"    Regex extracted all {len(extracted)} fields")
            return extracted
        
        # STEP 3: LLM fallback only for missing fields
        print(f"   âš ï¸  Regex missing: {', '.join(missing_fields)}")
        
        if self.llm and self._can_use_llm():
            try:
                print(f"   ðŸ¤– Using LLM to extract missing fields...")
                llm_extracted = self._llm_extract_fields(text, doc_type, missing_fields)
                
                # Merge: Keep regex results, fill gaps with LLM
                for field, value in llm_extracted.items():
                    if field in missing_fields and value:
                        extracted[field] = value
                        print(f"    LLM found {field}: {value}")
                
                self.llm_calls += 1
                
            except Exception as e:
                print(f"   âš ï¸  LLM failed: {str(e)[:80]}")
        else:
            print(f"   âš ï¸  LLM not available or rate limited")
        
        return extracted
    
    def _get_required_fields(self, doc_type: DocumentType) -> List[str]:
        """Get list of required fields for document type"""
        if doc_type == DocumentType.VENDOR_INVOICE:
            return ['invoice_number', 'invoice_date', 'vendor_name', 'total_amount', 'customer_name']
        elif doc_type == DocumentType.CUSTOMER_INVOICE:
            return ['invoice_number', 'invoice_date', 'customer_name', 'total_amount']
        elif doc_type == DocumentType.PURCHASE_ORDER:
            return ['po_number', 'po_date', 'vendor_name', 'total_amount']
        return []
    
    def _can_use_llm(self) -> bool:
        """Check if we can use LLM (rate limiting)"""
        if self.llm_calls >= self.max_llm_calls_per_hour:
            print(f"   âš ï¸  LLM rate limit reached ({self.llm_calls} calls this session)")
            return False
        return True
    
    def _llm_extract_fields(self, text: str, doc_type: DocumentType, missing_fields: List[str]) -> Dict[str, Any]:
        """
        Use LLM ONLY for missing fields (more efficient)
        """
        
        # Build targeted prompt for missing fields only
        fields_desc = {}
        for field in missing_fields:
            if field in ['invoice_number', 'po_number']:
                fields_desc[field] = "invoice/order/receipt/transaction number"
            elif field in ['invoice_date', 'po_date']:
                fields_desc[field] = "invoice/order/transaction date"
            elif field == 'vendor_name':
                fields_desc[field] = "vendor/company name (issuer, at top)"
            elif field == 'customer_name':
                fields_desc[field] = "customer/buyer name"
            elif field == 'total_amount':
                fields_desc[field] = "<numeric total amount>"
            elif field == 'tax_amount':
                fields_desc[field] = "<numeric tax, 0 if not found>"
        
        prompt = f"""Extract ONLY these missing fields. Return ONLY valid JSON.

Document (first 2500 chars):
{text[:2500]}

Extract only:
{json.dumps(fields_desc, indent=2)}

Rules:
- Return ONLY the requested fields
- Remove currency symbols ($, â‚¹, â‚¬) and commas from numbers
- Return null if field truly not found
- Return ONLY JSON, no markdown, no explanation

JSON:"""
        
        try:
            response = self.llm.generate(prompt)
            response_text = response.strip()
            
            # Clean response
            if '```' in response_text:
                lines = response_text.split('\n')
                response_text = '\n'.join([l for l in lines if not l.strip().startswith('```')])
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            extracted = json.loads(response_text)
            
            # Clean numeric fields
            for field in ['total_amount', 'tax_amount']:
                if field in extracted and extracted[field]:
                    val_str = str(extracted[field]).replace('$', '').replace(',', '').replace('â‚¹', '').replace('â‚¬', '').strip()
                    try:
                        extracted[field] = float(val_str)
                    except:
                        extracted[field] = 0.0 if field == 'tax_amount' else None
            
            return extracted
            
        except Exception as e:
            print(f"   âš ï¸  LLM error: {str(e)[:80]}")
            return {}
    
    def _regex_extract_fields(self, text: str, doc_type: DocumentType) -> Dict[str, Any]:
        """
        Regex extraction with SMART GENERIC PATTERNS
        No hardcoding - works with most vendors
        """
        extracted = {}
        
        if doc_type in [DocumentType.VENDOR_INVOICE, DocumentType.CUSTOMER_INVOICE, 
                        DocumentType.PURCHASE_ORDER, DocumentType.RECEIPT]:
            
            # 1. Invoice/Order/Receipt Number (Unchanged)
            number_patterns = [
                r'Invoice\s+Number[:\s]+([A-Z0-9-]+)',
                r'Invoice\s+No\.?[:\s]+([A-Z0-9-]+)',
                r'Order\s+Number[:\s]+(\d+)',
                r'Order\s*#[:\s]*(\d+)',
                r'(?:INV|ORD|REC)[:\s#-]+([A-Z0-9-]+)',
                r'#\s*([A-Z]{2,}\d{3,})',
            ]
            for pattern in number_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    invoice_num = match.group(1).strip()
                    invalid = ['Invoice', 'INVOICE', 'invoice', 'Number', 'Total', 'Date']
                    is_valid = (
                        invoice_num not in invalid and
                        len(invoice_num) >= 3 and
                        re.search(r'\d', invoice_num)
                    )
                    if is_valid:
                        extracted['invoice_number'] = invoice_num
                        print(f"   ✅ Found invoice number: {invoice_num}")
                        break
            
            if 'invoice_number' not in extracted:
                header_match = re.search(r'##\s+([A-Z]{2,}[0-9-]+)', text)
                if header_match:
                    num = header_match.group(1)
                    if num not in ['Invoice', 'INVOICE'] and len(num) >= 3:
                        extracted['invoice_number'] = num
                        print(f"   ✅ Found invoice number in header: {num}")
                        
            # 2. Date (Unchanged)
            date_patterns = [
                r'(?:Invoice|Order|Transaction|Issue)\s+Date[:\s]+(\d{1,2}/\d{1,2}/\d{4})',
                r'(?:Date|Dated)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{4}-\d{2}-\d{2})',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted['invoice_date'] = match.group(1).strip()
                    break
            
            # 3. Total Amount - PRIORITIZED LOGIC
            # Priority 1: Explicit "Grand Total" or "Amount Due"
            high_priority_patterns = [
                r'(?:Grand\s+Total|Amount\s+Due|Total\s+Payable|Final\s+Amount)[:\s]+[$₹€]?\s*([\d,]+\.?\d{2})',
                r'[$₹€]\s*([\d,]+\.?\d{2})\s+(?:due|payable)',
            ]
            
            # Priority 2: Generic "Total" (careful to avoid Sub Total)
            generic_patterns = [
                r'(?<!Sub\s)(?<!Net\s)(?:Total)[:\s]+[$₹€]?\s*([\d,]+\.?\d{2})',
            ]
            
            found_amount = False
            
            # Check High Priority First
            for pattern in high_priority_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        extracted['total_amount'] = float(match.group(1).replace(',', ''))
                        found_amount = True
                        break
                    except: pass
            
            # Check Generic only if high priority failed
            if not found_amount:
                for pattern in generic_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        try:
                            val = float(match.group(1).replace(',', ''))
                            extracted['total_amount'] = val
                            break
                        except: pass

            # 4. Vendor Name (Unchanged)
            vendor_patterns = [
                r'([A-Z][A-Za-z\s&,\.]+(?:Inc\.|LLC|Ltd\.|Limited|Corp\.|Corporation|Company))',
                r'##\s+([A-Z][A-Za-z\s&,\.]+(?:Inc\.|LLC|Ltd\.|Limited|Corp\.))',
                r'##\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            ]
            
            top_text = text[:800]
            lines = top_text.split('\n')
            bill_to_index = next((i for i, line in enumerate(lines) if 'bill to' in line.lower()), len(lines))
            vendor_text = '\n'.join(lines[:bill_to_index])
            
            for pattern in vendor_patterns:
                match = re.search(pattern, vendor_text, re.MULTILINE)
                if match:
                    vendor = match.group(1).strip()
                    excluded_terms = ['Invoice', 'Bill to', 'RECEIPT', 'Receipt', 'Order', 'Total', 'Payment', 'Date', 'Number', 'Customer']
                    is_valid = (vendor and len(vendor) > 3 and not any(term in vendor for term in excluded_terms) and not vendor.isupper())
                    if is_valid:
                        extracted['vendor_name'] = vendor
                        break
            
            # 5. Currency (Unchanged)
            currency_patterns = [
                r'[$₹€£¥]\s*([\d,]+\.?\d{2})',
                r'([\d,]+\.?\d{2})\s*[$₹€£¥]',
                r'([\d,]+\.?\d{2})\s*(USD|INR|EUR|GBP|AED|SGD|JPY|CNY)',
                r'(USD|INR|EUR|GBP|AED|SGD|JPY|CNY)\s*([\d,]+\.?\d{2})',
            ]
            for pattern in currency_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    currency_part = match.group(0)
                    symbol_to_code = {'$': 'USD', '₹': 'INR', '€': 'EUR', '£': 'GBP', '¥': 'JPY'}
                    currency_codes = ['USD', 'INR', 'EUR', 'GBP', 'AED', 'SGD', 'JPY', 'CNY']
                    
                    for code in currency_codes:
                        if code in currency_part.upper():
                            extracted['currency'] = code
                            break
                    if 'currency' not in extracted:
                        for symbol, code in symbol_to_code.items():
                            if symbol in currency_part:
                                extracted['currency'] = code
                                break
                    if 'currency' in extracted:
                        print(f"   💲 Detected currency: {extracted['currency']}")
                        break
            
            # 6. Customer Name (Unchanged)
            customer_patterns = [
                r'Founder\s+([A-Z]+(?:\s+[A-Z]+)*\s+(?:PRIVATE LIMITED|LIMITED|LLC|INC|CORP))',
                r'Bill\s+to[:\s]+([A-Z][A-Za-z\s]+(?:PRIVATE LIMITED|LIMITED|LLC|INC|CORP))',
                r'Ship\s+to[:\s]+([A-Z][A-Za-z\s]+(?:PRIVATE LIMITED|LIMITED|LLC|INC|CORP))',
            ]
            for pattern in customer_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    customer = match.group(1).strip()
                    customer = ' '.join(customer.split())
                    if len(customer) > 5:
                        extracted['customer_name'] = customer
                        print(f"   🎯 Found customer: {customer}")
                        break
            
            # 7. Tax & Vertical Block Logic
            tax_amount = 0.0
            
            # A. Table Pattern
            table_tax_patterns = [
                r'\|\s*GST\s*\|\s*[₹$€]?\s*([\d,]+\.?\d{0,2})',
                r'\|\s+GST\s+\|\s+[₹$€]?\s*([\d,]+\.?\d{0,2})',
                r'GST\s+\|\s+[₹$€]?\s*([\d,]+\.?\d{0,2})',
            ]
            for pattern in table_tax_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        tax_amount = float(match.group(1).replace(',', ''))
                        extracted['tax_amount'] = tax_amount
                        print(f" Found GST in table: ₹{tax_amount:.2f}")
                        break
                    except: pass
            
            # B. Key-Value Pattern
            if tax_amount == 0.0:
                text_tax_patterns = [
                    r'GST[:\s]+[₹$€]?\s*([\d,]+\.?\d{2})',
                    r'IGST[:\s]+[₹$€]?\s*([\d,]+\.?\d{2})',
                    r'Tax[:\s]+[₹$€]?\s*([\d,]+\.?\d{2})',
                ]
                for pattern in text_tax_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        try:
                            tax_amount = float(match.group(1).replace(',', ''))
                            extracted['tax_amount'] = tax_amount
                            print(f"   ✅ Found tax: ₹{tax_amount:.2f}")
                            break
                        except: pass
            
            # C. Vertical Block Pattern (Also fixes Total Amount!)
            # Look for 3 numbers stacked vertically
            number_block_pattern = r'([₹$€]?\s*[\d,]+\.\d{2})\s*\n\s*([₹$€]?\s*[\d,]+\.\d{2})\s*\n\s*([₹$€]?\s*[\d,]+\.\d{2})'
            matches = list(re.finditer(number_block_pattern, text))
            
            if matches:
                last_match = matches[-1] # Usually the totals block is at the bottom
                try:
                    v1 = float(last_match.group(1).replace(',', '').replace('₹','').replace('$',''))
                    v2 = float(last_match.group(2).replace(',', '').replace('₹','').replace('$',''))
                    v3 = float(last_match.group(3).replace(',', '').replace('₹','').replace('$',''))
                    
                    # Case 1: Subtotal + Tax = Total
                    # v1=Sub, v2=Tax, v3=Total
                    if abs((v1 + v2) - v3) < 1.0:
                        extracted['tax_amount'] = v2
                        extracted['total_amount'] = v3  # Overwrite with confirmed total
                        tax_amount = v2
                        print(f"   ✅ Calculated vertical block: Sub={v1}, Tax={v2}, Total={v3}")
                    
                    # Case 2: Reverse (Tax + Sub = Total)
                    # v2=Sub, v1=Tax, v3=Total (unlikely but possible)
                    elif abs((v2 + v1) - v3) < 1.0:
                        extracted['tax_amount'] = v1
                        extracted['total_amount'] = v3
                        tax_amount = v1
                        print(f"   ✅ Calculated vertical block (rev): Tax={v1}, Sub={v2}, Total={v3}")
                        
                except Exception as e:
                    pass

            # D. Fallback Calculation
            if tax_amount == 0.0 and 'total_amount' in extracted:
                subtotal_match = re.search(r'Sub\s+Total\s+\|\s+[₹$€]?\s*([\d,]+\.?\d{0,2})', text)
                if subtotal_match:
                    try:
                        subtotal = float(subtotal_match.group(1).replace(',', ''))
                        calc_tax = extracted['total_amount'] - subtotal
                        if calc_tax > 0:
                            extracted['tax_amount'] = calc_tax
                            print(f"   ✅ Calculated tax (Grand - Sub): ₹{calc_tax:.2f}")
                    except: pass

            if 'tax_amount' not in extracted or extracted['tax_amount'] == 0.0:
                print(f"   💰 Tax not found, defaulting to 0.0")
            
            # 8. LINE ITEM EXTRACTION - NEW!
            print(f"\n📦 Extracting line items...")
            line_items = self._extract_line_items(text, doc_type)
            if line_items:
                extracted['line_items'] = line_items
                print(f"   ✅ Extracted {len(line_items)} line items")
                
                # Validate line item totals against invoice total
                line_total = sum(item.get('amount', 0) for item in line_items)
                invoice_total = extracted.get('total_amount', 0)
                
                if invoice_total > 0:
                    diff = abs(line_total - invoice_total)
                    if diff < 1.0:  # Allow small rounding differences
                        print(f"   ✅ Line items total matches invoice total: ₹{line_total:.2f}")
                    else:
                        print(f"   ⚠️ Line items total (₹{line_total:.2f}) doesn't match invoice total (₹{invoice_total:.2f})")
                        # Don't remove line items, just log the discrepancy
                else:
                    print(f"   ⚠️ Cannot validate line items - no invoice total found")
            else:
                print(f"   ⚠️ No line items found")
        
        return extracted
    
    def _find_value(self, data: Any, paths: List[str]) -> Optional[Any]:
        """Find value in nested dict using possible paths"""
        for path in paths:
            value = self._get_nested(data, path)
            if value is not None:
                return value
        return None
    
    def _get_nested(self, data: Any, path: str) -> Optional[Any]:
        """Get value from nested dict using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current


# ============================================================================
# MASTER DATA MANAGER
# ============================================================================

class MasterDataManager:
    """
    Manages vendor, customer, and other master data
    Auto-creates or matches based on extracted information
    FIXED VERSION - Actually creates database records
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_or_create_vendor(self, vendor_name: str, company_id: str, extracted_data: Dict = None) -> str:
        """
        Get existing vendor or create new one
        
        Args:
            vendor_name: Name of the vendor
            company_id: Company ID
            extracted_data: Optional additional vendor data
            
        Returns:
            vendor_id (UUID string)
        """
        if not vendor_name or not company_id:
            print(f"   âš ï¸ Missing vendor_name or company_id")
            return None
        
        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        try:
            # Try to find existing vendor (case-insensitive match)
            cursor.execute("""
                SELECT id FROM vendors 
                WHERE company_id = %s 
                AND LOWER(vendor_name) = LOWER(%s)
                LIMIT 1
            """, (company_id, vendor_name))
            
            row = cursor.fetchone()
            
            if row:
                vendor_id = row['id']
                print(f"   ðŸ“‡ Found existing vendor: {vendor_name} ({vendor_id})")
            else:
                # Create new vendor
                vendor_id = str(uuid.uuid4())
                
                # Extract additional data if available
                vendor_code = None
                if extracted_data:
                    vendor_code = extracted_data.get('vendor_code')
                
                cursor.execute("""
                    INSERT INTO vendors (
                        id, company_id, vendor_name, vendor_code, is_active, created_at
                    ) VALUES (%s, %s, %s, %s, %s, NOW())
                """, (vendor_id, company_id, vendor_name, vendor_code, True))
                
                self.db.conn.commit()
                print(f"   ðŸ“‡ Created new vendor: {vendor_name} ({vendor_id})")
            
            return vendor_id
            
        except Exception as e:
            print(f"   âŒ Error creating/getting vendor: {e}")
            self.db.conn.rollback()
            return None
        finally:
            cursor.close()
    
    def get_or_create_customer(self, customer_name: str, company_id: str, extracted_data: Dict = None) -> str:
        """
        Get existing customer or create new one
        
        Args:
            customer_name: Name of the customer
            company_id: Company ID
            extracted_data: Optional additional customer data
            
        Returns:
            customer_id (UUID string)
        """
        if not customer_name or not company_id:
            print(f"   âš ï¸ Missing customer_name or company_id")
            return None
        
        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        try:
            # Try to find existing customer (case-insensitive match)
            cursor.execute("""
                SELECT id FROM customers 
                WHERE company_id = %s 
                AND LOWER(customer_name) = LOWER(%s)
                LIMIT 1
            """, (company_id, customer_name))
            
            row = cursor.fetchone()
            
            if row:
                customer_id = row['id']
                print(f"   ðŸ“‡ Found existing customer: {customer_name} ({customer_id})")
            else:
                # Create new customer
                customer_id = str(uuid.uuid4())
                
                # Extract additional data if available
                customer_code = None
                if extracted_data:
                    customer_code = extracted_data.get('customer_code')
                
                cursor.execute("""
                    INSERT INTO customers (
                        id, company_id, customer_name, customer_code, is_active, created_at
                    ) VALUES (%s, %s, %s, %s, %s, NOW())
                """, (customer_id, company_id, customer_name, customer_code, True))
                
                self.db.conn.commit()
                print(f"   ðŸ“‡ Created new customer: {customer_name} ({customer_id})")
            
            return customer_id
            
        except Exception as e:
            print(f"   âŒ Error creating/getting customer: {e}")
            self.db.conn.rollback()
            return None
        finally:
            cursor.close()
    
    def get_or_create_bank_account(self, account_number: str, company_id: str) -> str:
        """Get existing bank account or create new one"""
        # Placeholder - implement if needed
        return f"bank_account_{account_number}"
    
    # âœ… ALIAS METHODS for backward compatibility
    # These match the calling convention used in document_processing_service.py
    
    def create_or_get_vendor(self, company_id: str, vendor_name: str, extracted_data: Dict = None) -> str:
        """
        Alias for get_or_create_vendor with swapped parameter order
        This matches the calling convention in document_processing_service.py
        """
        return self.get_or_create_vendor(vendor_name, company_id, extracted_data)
    
    def create_or_get_customer(self, company_id: str, customer_name: str, extracted_data: Dict = None) -> str:
        """
        Alias for get_or_create_customer with swapped parameter order
        This matches the calling convention in document_processing_service.py
        """
        return self.get_or_create_customer(customer_name, company_id, extracted_data)