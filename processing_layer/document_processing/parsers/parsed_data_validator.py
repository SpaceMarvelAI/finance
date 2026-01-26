"""
Parsed Data Validation Layer
Validates that extracted/parsed text is correct and complete
"""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime


class ParsedDataValidator:
    """
    Comprehensive validation layer for parsed financial documents
    
    Features:
    - Structural validation (has required fields)
    - Content validation (data makes sense)
    - Financial validation (amounts, dates, etc.)
    - Quality scoring
    - Automated correction suggestions
    """
    
    # Required fields for financial documents
    REQUIRED_FIELDS = {
        'invoice': [
            'document_number', 'document_date', 'total_amount',
            ('vendor_name', 'customer_name')  # At least one of these
        ],
        'purchase': ['document_number', 'document_date', 'vendor_name', 'total_amount'],
        'sales': ['document_number', 'document_date', 'customer_name', 'total_amount']
    }
    
    # Expected data patterns
    PATTERNS = {
        'invoice_number': r'^[A-Z0-9\-\/]+$',
        'date': r'\d{4}-\d{2}-\d{2}',
        'amount': r'^\d+\.?\d*$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^\+?[\d\s\-\(\)]{10,}$',
        'gst': r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[Z]{1}[A-Z\d]{1}$'  # Indian GST
    }
    
    def __init__(self):
        """Initialize validator"""
        self.validation_history = []
    
    def validate(
        self,
        parsed_data: Dict[str, Any],
        document_type: Optional[str] = None,
        strict: bool = False
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of parsed data
        
        Args:
            parsed_data: Data from parser (text, raw_dict, metadata)
            document_type: Expected document type ('invoice', 'purchase', 'sales')
            strict: If True, validation fails on warnings
            
        Returns:
            Validation results with:
                - is_valid: Boolean
                - errors: Critical issues
                - warnings: Non-critical issues
                - quality_score: 0-100 score
                - suggestions: Improvement recommendations
        """
        errors = []
        warnings = []
        suggestions = []
        scores = {}
        
        # Validation 1: Structure check
        structure_result = self._validate_structure(parsed_data)
        errors.extend(structure_result['errors'])
        warnings.extend(structure_result['warnings'])
        scores['structure'] = structure_result['score']
        
        # Validation 2: Content completeness
        content_result = self._validate_content_completeness(parsed_data)
        errors.extend(content_result['errors'])
        warnings.extend(content_result['warnings'])
        scores['completeness'] = content_result['score']
        
        # Validation 3: Text quality
        text_result = self._validate_text_quality(parsed_data)
        warnings.extend(text_result['warnings'])
        suggestions.extend(text_result['suggestions'])
        scores['text_quality'] = text_result['score']
        
        # Validation 4: Financial data validation
        if 'raw_dict' in parsed_data and parsed_data['raw_dict']:
            financial_result = self._validate_financial_data(parsed_data['raw_dict'])
            errors.extend(financial_result['errors'])
            warnings.extend(financial_result['warnings'])
            scores['financial_data'] = financial_result['score']
        else:
            scores['financial_data'] = 0
            warnings.append("No structured data available for financial validation")
        
        # Validation 5: Document type specific
        if document_type:
            type_result = self._validate_document_type(parsed_data, document_type)
            errors.extend(type_result['errors'])
            warnings.extend(type_result['warnings'])
            suggestions.extend(type_result['suggestions'])
        
        # Calculate overall quality score
        overall_score = sum(scores.values()) / len(scores) if scores else 0
        
        # Determine if valid
        is_valid = len(errors) == 0
        if strict:
            is_valid = is_valid and len(warnings) == 0
        
        result = {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions,
            'quality_score': round(overall_score, 2),
            'category_scores': scores,
            'validation_timestamp': datetime.now().isoformat()
        }
        
        # Store in history
        self.validation_history.append(result)
        
        return result
    
    def _validate_structure(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate basic structure of parsed data"""
        errors = []
        warnings = []
        score = 100
        
        # Check required keys
        required_keys = ['text', 'metadata', 'format']
        missing_keys = [k for k in required_keys if k not in parsed_data]
        
        if missing_keys:
            errors.append(f"Missing required keys: {', '.join(missing_keys)}")
            score -= 30 * len(missing_keys)
        
        # Check text content
        if 'text' in parsed_data:
            text = parsed_data['text']
            if not text or len(text.strip()) < 10:
                errors.append("Extracted text is empty or too short")
                score -= 50
        
        # Check metadata
        if 'metadata' in parsed_data:
            metadata = parsed_data['metadata']
            if not isinstance(metadata, dict):
                warnings.append("Metadata is not a dictionary")
                score -= 10
            elif not metadata:
                warnings.append("Metadata is empty")
                score -= 10
        
        return {
            'errors': errors,
            'warnings': warnings,
            'score': max(0, score)
        }
    
    def _validate_content_completeness(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content completeness"""
        errors = []
        warnings = []
        score = 100
        
        text = parsed_data.get('text', '')
        
        # Check text length
        if len(text) < 100:
            warnings.append("Text content is very short (< 100 characters)")
            score -= 20
        
        # Check for common financial document elements
        financial_indicators = [
            'invoice', 'bill', 'amount', 'total', 'date',
            'vendor', 'customer', 'payment', 'tax'
        ]
        
        found_indicators = sum(1 for indicator in financial_indicators if indicator.lower() in text.lower())
        
        if found_indicators < 2:
            warnings.append("Document doesn't contain common financial terms")
            score -= 30
        elif found_indicators < 4:
            warnings.append("Document has few financial indicators")
            score -= 10
        
        # Check for numeric data
        if not re.search(r'\d+\.?\d*', text):
            errors.append("No numeric data found in text")
            score -= 40
        
        # Check for date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{2}-\d{2}-\d{4}'   # DD-MM-YYYY
        ]
        
        has_date = any(re.search(pattern, text) for pattern in date_patterns)
        if not has_date:
            warnings.append("No date pattern found in text")
            score -= 15
        
        return {
            'errors': errors,
            'warnings': warnings,
            'score': max(0, score)
        }
    
    def _validate_text_quality(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate text extraction quality"""
        warnings = []
        suggestions = []
        score = 100
        
        text = parsed_data.get('text', '')
        
        # Check for OCR artifacts
        ocr_artifacts = [
            (r'[|]{3,}', 'Multiple pipe characters (OCR artifact)'),
            (r'[_]{5,}', 'Multiple underscores (OCR artifact)'),
            (r'\s{5,}', 'Excessive whitespace'),
            (r'[^\x00-\x7F]{10,}', 'Many non-ASCII characters (possible OCR errors)')
        ]
        
        for pattern, message in ocr_artifacts:
            if re.search(pattern, text):
                warnings.append(message)
                suggestions.append(f"Consider re-scanning or using better OCR: {message}")
                score -= 10
        
        # Check for fragmented text
        if len(text.split('\n')) / max(len(text.split()), 1) > 0.5:
            warnings.append("Text appears highly fragmented")
            suggestions.append("Document may need better formatting or OCR")
            score -= 15
        
        # Check for readable content ratio
        words = text.split()
        if words:
            readable_words = sum(1 for word in words if len(word) > 2 and word.isalpha())
            readable_ratio = readable_words / len(words)
            
            if readable_ratio < 0.3:
                warnings.append(f"Low readable content ratio: {readable_ratio:.1%}")
                score -= 20
        
        return {
            'warnings': warnings,
            'suggestions': suggestions,
            'score': max(0, score)
        }
    
    def _validate_financial_data(self, raw_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Validate financial data fields"""
        errors = []
        warnings = []
        score = 100
        
        # Common financial fields to check
        field_checks = {
            'document_number': (lambda x: len(str(x)) > 0, "Document number is empty"),
            'document_date': (lambda x: self._is_valid_date(x), "Document date is invalid"),
            'total_amount': (lambda x: self._is_valid_amount(x), "Total amount is invalid"),
            'vendor_name': (lambda x: len(str(x)) > 1, "Vendor name is too short"),
            'customer_name': (lambda x: len(str(x)) > 1, "Customer name is too short")
        }
        
        for field, (validator, error_msg) in field_checks.items():
            if field in raw_dict:
                try:
                    if not validator(raw_dict[field]):
                        warnings.append(error_msg)
                        score -= 10
                except:
                    warnings.append(f"Could not validate {field}")
                    score -= 5
        
        # Check for amounts
        amount_fields = [k for k in raw_dict.keys() if 'amount' in k.lower() or 'total' in k.lower()]
        
        if amount_fields:
            for field in amount_fields:
                value = raw_dict[field]
                if not self._is_valid_amount(value):
                    warnings.append(f"Invalid amount in field '{field}': {value}")
                    score -= 10
        else:
            warnings.append("No amount fields found in data")
            score -= 20
        
        return {
            'errors': errors,
            'warnings': warnings,
            'score': max(0, score)
        }
    
    def _validate_document_type(
        self,
        parsed_data: Dict[str, Any],
        document_type: str
    ) -> Dict[str, Any]:
        """Validate document against expected type"""
        errors = []
        warnings = []
        suggestions = []
        
        required_fields = self.REQUIRED_FIELDS.get(document_type, [])
        raw_dict = parsed_data.get('raw_dict', {})
        
        for field in required_fields:
            if isinstance(field, tuple):
                # At least one of these fields should exist
                if not any(f in raw_dict for f in field):
                    errors.append(f"Missing required field (need one of): {', '.join(field)}")
                    suggestions.append(f"Document should have at least one of: {', '.join(field)}")
            else:
                # This specific field should exist
                if field not in raw_dict:
                    errors.append(f"Missing required field: {field}")
                    suggestions.append(f"Document should contain '{field}'")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions
        }
    
    def _is_valid_date(self, value: Any) -> bool:
        """Check if value is a valid date"""
        if not value:
            return False
        
        date_str = str(value)
        
        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d',
            '%d.%m.%Y'
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except:
                continue
        
        return False
    
    def _is_valid_amount(self, value: Any) -> bool:
        """Check if value is a valid amount"""
        if value is None:
            return False
        
        try:
            # Try to convert to float
            amount = float(str(value).replace(',', '').replace('₹', '').replace('$', '').strip())
            return amount >= 0
        except:
            return False
    
    def suggest_corrections(self, parsed_data: Dict[str, Any]) -> List[str]:
        """
        Suggest corrections for parsed data
        
        Args:
            parsed_data: Parsed data to analyze
            
        Returns:
            List of correction suggestions
        """
        validation = self.validate(parsed_data)
        
        corrections = []
        
        # Based on quality score
        if validation['quality_score'] < 50:
            corrections.append("CRITICAL: Re-scan or re-upload document with better quality")
        elif validation['quality_score'] < 70:
            corrections.append("Document quality is low. Consider using a clearer source")
        
        # Based on specific issues
        if validation['errors']:
            corrections.append(f"Fix {len(validation['errors'])} critical errors before processing")
        
        if validation['warnings']:
            corrections.extend([f"WARNING: {w}" for w in validation['warnings'][:3]])
        
        # Add suggestions
        corrections.extend(validation.get('suggestions', []))
        
        return corrections
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validations performed"""
        if not self.validation_history:
            return {
                'total_validations': 0,
                'average_quality_score': 0,
                'success_rate': 0
            }
        
        total = len(self.validation_history)
        successful = sum(1 for v in self.validation_history if v['is_valid'])
        avg_score = sum(v['quality_score'] for v in self.validation_history) / total
        
        return {
            'total_validations': total,
            'successful_validations': successful,
            'failed_validations': total - successful,
            'success_rate': round((successful / total) * 100, 2),
            'average_quality_score': round(avg_score, 2),
            'latest_validation': self.validation_history[-1]
        }