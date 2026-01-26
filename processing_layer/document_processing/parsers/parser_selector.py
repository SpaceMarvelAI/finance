"""
Intelligent Parser Selector
Automatically detects file type and selects appropriate parser
"""

from typing import Dict, Any, Optional
from pathlib import Path
import magic  # python-magic for file type detection


try:
    from processing_layer.document_processing.parsers.csv_parser import CSVParser
    from processing_layer.document_processing.parsers.universal_docling_parser import UniversalDoclingParser
except:
    # Fallback imports for different directory structures
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from csv_parser import CSVParser
    from universal_docling_parser import UniversalDoclingParser


class ParserSelector:
    """
    Intelligent parser selector
    
    Features:
    - Auto-detects file type (CSV vs other formats)
    - Routes CSV files to pandas-based CSVParser
    - Routes other files to Docling
    - Validates file before parsing
    - Provides parser recommendations
    """
    
    # File type categories
    CSV_EXTENSIONS = ['.csv', '.tsv', '.txt']
    DOCLING_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.xlsx', '.xls', '.html', '.md', '.png', '.jpg', '.jpeg']
    
    def __init__(self):
        """Initialize parser selector with both parsers"""
        self.csv_parser = CSVParser()
        self.docling_parser = UniversalDoclingParser()
        
        # Track parser usage
        self.usage_stats = {
            'csv': 0,
            'docling': 0,
            'errors': 0
        }
    
    def detect_file_type(self, file_path: str) -> Dict[str, Any]:
        """
        Detect file type and characteristics
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with:
                - extension: File extension
                - mime_type: MIME type (if detectable)
                - recommended_parser: 'csv' or 'docling'
                - can_parse: Boolean
                - warnings: List of warnings
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                'extension': None,
                'mime_type': None,
                'recommended_parser': None,
                'can_parse': False,
                'warnings': [f"File not found: {file_path}"]
            }
        
        # Get extension
        extension = file_path.suffix.lower()
        
        # Detect MIME type (if python-magic is available)
        mime_type = self._detect_mime_type(file_path)
        
        # Determine parser
        recommended_parser = None
        can_parse = False
        warnings = []
        
        if extension in self.CSV_EXTENSIONS:
            recommended_parser = 'csv'
            can_parse = True
            
            # Additional check for CSV
            if not self._looks_like_csv(file_path):
                warnings.append("File extension is CSV but content may not be CSV format")
        
        elif extension in self.DOCLING_EXTENSIONS:
            recommended_parser = 'docling'
            can_parse = True
        
        else:
            warnings.append(f"Unsupported file extension: {extension}")
            
            # Try to guess from MIME type
            if mime_type:
                if 'csv' in mime_type or 'text/plain' in mime_type:
                    recommended_parser = 'csv'
                    can_parse = True
                    warnings.append("Guessed CSV from MIME type, but extension is unusual")
                elif any(x in mime_type for x in ['pdf', 'word', 'excel', 'powerpoint']):
                    recommended_parser = 'docling'
                    can_parse = True
                    warnings.append("Guessed document type from MIME type, but extension is unusual")
        
        return {
            'extension': extension,
            'mime_type': mime_type,
            'recommended_parser': recommended_parser,
            'can_parse': can_parse,
            'warnings': warnings,
            'file_size_mb': round(file_path.stat().st_size / (1024 * 1024), 2)
        }
    
    def _detect_mime_type(self, file_path: Path) -> Optional[str]:
        """
        Detect MIME type using python-magic
        Falls back gracefully if not available
        """
        try:
            mime = magic.Magic(mime=True)
            return mime.from_file(str(file_path))
        except:
            # python-magic not available or error
            return None
    
    def _looks_like_csv(self, file_path: Path) -> bool:
        """
        Check if file content looks like CSV
        Quick heuristic check
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline() for _ in range(3)]
            
            # Check for common CSV characteristics
            if not first_lines:
                return False
            
            # Count commas/semicolons in first line
            first_line = first_lines[0]
            comma_count = first_line.count(',')
            semicolon_count = first_line.count(';')
            
            # Should have multiple separators
            if comma_count > 1 or semicolon_count > 1:
                # Check if subsequent lines have similar separator counts
                if len(first_lines) > 1:
                    second_line = first_lines[1]
                    if comma_count > 1 and abs(second_line.count(',') - comma_count) <= 2:
                        return True
                    if semicolon_count > 1 and abs(second_line.count(';') - semicolon_count) <= 2:
                        return True
                else:
                    return True
            
            return False
            
        except:
            return True  # Assume it's CSV if we can't check
    
    def select_parser(self, file_path: str) -> str:
        """
        Select appropriate parser for file
        
        Args:
            file_path: Path to file
            
        Returns:
            Parser name: 'csv' or 'docling'
        """
        detection = self.detect_file_type(file_path)
        
        if not detection['can_parse']:
            raise ValueError(
                f"Cannot parse file: {file_path}. "
                f"Warnings: {', '.join(detection['warnings'])}"
            )
        
        return detection['recommended_parser']
    
    def parse(self, file_path: str, parser_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse file with automatically selected parser
        
        Args:
            file_path: Path to file
            parser_override: Optional manual parser selection ('csv' or 'docling')
            
        Returns:
            Parsed data dictionary with:
                - text: Extracted text
                - raw_dict: Structured data
                - metadata: File metadata
                - parser_used: Which parser was used
                - detection_info: File type detection results
        """
        # Detect file type
        detection = self.detect_file_type(file_path)
        
        # Use override or recommended parser
        if parser_override:
            if parser_override not in ['csv', 'docling']:
                raise ValueError(f"Invalid parser override: {parser_override}")
            parser_to_use = parser_override
        else:
            if not detection['can_parse']:
                raise ValueError(
                    f"Cannot parse file: {file_path}. "
                    f"Warnings: {', '.join(detection['warnings'])}"
                )
            parser_to_use = detection['recommended_parser']
        
        # Parse with selected parser
        try:
            if parser_to_use == 'csv':
                result = self.csv_parser.parse(file_path)
                self.usage_stats['csv'] += 1
            else:
                result = self.docling_parser.parse(file_path)
                self.usage_stats['docling'] += 1
            
            # Add parser info to result
            result['parser_used'] = parser_to_use
            result['detection_info'] = detection
            
            return result
            
        except Exception as e:
            self.usage_stats['errors'] += 1
            raise Exception(f"Parsing failed with {parser_to_use} parser: {str(e)}")
    
    def validate_before_parse(self, file_path: str) -> Dict[str, Any]:
        """
        Validate file before attempting to parse
        
        Args:
            file_path: Path to file
            
        Returns:
            Validation results with recommendations
        """
        file_path = Path(file_path)
        
        errors = []
        warnings = []
        recommendations = []
        
        # Check 1: File exists
        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
            return {
                'is_valid': False,
                'errors': errors,
                'warnings': warnings,
                'recommendations': recommendations
            }
        
        # Check 2: File size
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > 50:
            errors.append(f"File too large: {size_mb:.1f}MB (max 50MB)")
        elif size_mb > 20:
            warnings.append(f"Large file: {size_mb:.1f}MB (may be slow to process)")
        
        # Check 3: File type detection
        detection = self.detect_file_type(str(file_path))
        
        if not detection['can_parse']:
            errors.append(f"Unsupported file type: {detection['extension']}")
            recommendations.append("Supported formats: CSV, PDF, Excel, Word, PowerPoint, Images")
        
        if detection['warnings']:
            warnings.extend(detection['warnings'])
        
        # Check 4: Specific validation for CSV
        if detection['recommended_parser'] == 'csv':
            csv_validation = self.csv_parser.validate(str(file_path))
            if not csv_validation['is_valid']:
                errors.extend(csv_validation['errors'])
            warnings.extend(csv_validation['warnings'])
            
            if 'quality_scores' in csv_validation:
                quality = csv_validation['quality_scores'].get('overall', 0)
                if quality < 50:
                    warnings.append(f"CSV quality is low ({quality:.1f}%). Check for missing data.")
                    recommendations.append("Consider cleaning the CSV file before processing")
        
        # Check 5: File permissions
        if not file_path.is_file():
            errors.append(f"Path is not a file: {file_path}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'recommendations': recommendations,
            'detection': detection,
            'file_size_mb': round(size_mb, 2)
        }
    
    def get_parser_info(self) -> Dict[str, Any]:
        """Get information about available parsers"""
        return {
            'available_parsers': ['csv', 'docling'],
            'csv_parser': {
                'name': 'CSVParser',
                'supported_extensions': self.CSV_EXTENSIONS,
                'features': [
                    'Auto-detect delimiter',
                    'Auto-detect encoding',
                    'Data validation',
                    'Quality scoring',
                    'Financial column detection'
                ]
            },
            'docling_parser': {
                'name': 'UniversalDoclingParser',
                'supported_extensions': self.DOCLING_EXTENSIONS,
                'features': [
                    'PDF parsing (text and scanned)',
                    'Excel/Word/PowerPoint',
                    'Table extraction',
                    'Image extraction',
                    'Markdown export'
                ]
            },
            'usage_stats': self.usage_stats
        }