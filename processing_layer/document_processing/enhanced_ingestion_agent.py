"""
Enhanced Ingestion Agent with Intelligent Parsing and Detailed Logging
Automatically detects file type and routes to appropriate parser
"""

import sys
import os
from typing import Dict, Any
from pathlib import Path

# Add project to path
project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_path not in sys.path:
    sys.path.insert(0, project_path)


try:
    from processing_layer.agents.core.base_agent import BaseAgent
    from shared.config.logging_config import get_logger
except:
    # Fallback
    import logging
    def get_logger(name):
        return logging.getLogger(name)


# Import parsers with fallback

try:
    from processing_layer.document_processing.parsers.csv_parser import CSVParser
    CSV_PARSER_AVAILABLE = True
except ImportError:
    CSV_PARSER_AVAILABLE = False
    print("⚠️ CSVParser not available - CSV files will use Docling")


try:
    from processing_layer.document_processing.parsers.universal_docling_parser import UniversalDoclingParser
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("⚠️ Docling not available")


logger = get_logger(__name__)


class EnhancedIngestionAgent(BaseAgent):
    """
    Enhanced Ingestion Agent with Intelligent Parsing and Detailed Logging
    
    Key Features:
    1. Auto-detects file type (CSV vs PDF vs Excel, etc.)
    2. Routes CSV to pandas parser, others to Docling
    3. Validates parsed data quality
    4. Provides detailed feedback and suggestions
    5. **LOGS EVERYTHING** - What's being parsed, how, and results
    
    Workflow:
    File → Detect Type → Select Parser → Parse → Validate → Return
    """
    
    def __init__(self):
        super().__init__("EnhancedIngestionAgent")
        
        logger.info("="*80)
        logger.info("🚀 INITIALIZING ENHANCED INGESTION AGENT")
        logger.info("="*80)
        
        # Initialize parsers
        self.csv_parser = None
        self.docling_parser = None
        
        if CSV_PARSER_AVAILABLE:
            try:
                self.csv_parser = CSVParser()
                logger.info(" CSV Parser initialized successfully")
            except Exception as e:
                logger.error(f" Failed to initialize CSV Parser: {e}")
        else:
            logger.warning("⚠️ CSV Parser not available")
        
        if DOCLING_AVAILABLE:
            try:
                self.docling_parser = UniversalDoclingParser()
                logger.info(" Docling Parser initialized successfully")
            except Exception as e:
                logger.error(f" Failed to initialize Docling Parser: {e}")
        else:
            logger.warning("⚠️ Docling Parser not available")
        
        # Track statistics
        self.stats = {
            'total_files': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'csv_files': 0,
            'docling_files': 0,
            'average_quality_score': 0
        }
        
        logger.info(f"📊 Statistics tracking initialized")
        logger.info("="*80)
    
    def execute(self, state: dict) -> dict:
        """
        Execute enhanced ingestion with intelligent parsing
        
        Args:
            state: Workflow state
            
        Returns:
            State with parsed_data and validation results
        """
        logger.info("")
        logger.info("="*80)
        logger.info("🎯 STARTING ENHANCED INGESTION")
        logger.info("="*80)
        
        try:
            file_path = state.get("file_path")
            
            if not file_path:
                raise ValueError("No file_path in state")
            
            logger.info(f"📁 File Path: {file_path}")
            logger.info(f"📊 File Size: {self._get_file_size(file_path)}")
            
            # Step 1: Detect file type
            logger.info("")
            logger.info("─" * 80)
            logger.info("STEP 1: FILE TYPE DETECTION")
            logger.info("─" * 80)
            
            detection = self._detect_file_type(file_path)
            
            logger.info(f"📄 Extension: {detection['extension']}")
            logger.info(f"🔍 MIME Type: {detection.get('mime_type', 'Unknown')}")
            logger.info(f"🎯 Recommended Parser: {detection['parser'].upper()}")
            
            if detection['warnings']:
                for warning in detection['warnings']:
                    logger.warning(f"⚠️ {warning}")
            
            # Step 2: Select and initialize parser
            logger.info("")
            logger.info("─" * 80)
            logger.info("STEP 2: PARSER SELECTION")
            logger.info("─" * 80)
            
            parser = self._get_parser(detection['parser'])
            
            if not parser:
                raise ValueError(f"No parser available for type: {detection['parser']}")
            
            logger.info(f" Selected Parser: {parser.__class__.__name__}")
            
            # Step 3: Parse file
            logger.info("")
            logger.info("─" * 80)
            logger.info("STEP 3: PARSING FILE")
            logger.info("─" * 80)
            
            logger.info(f"⏳ Starting parse with {parser.__class__.__name__}...")
            
            import time
            start_time = time.time()
            
            parsed = parser.parse(file_path)
            
            parse_duration = time.time() - start_time
            
            logger.info(f" Parse completed in {parse_duration:.2f}s")
            logger.info("")
            logger.info("📊 PARSED DATA SUMMARY:")
            logger.info(f"   - Text Length: {len(parsed.get('text', ''))} characters")
            logger.info(f"   - Format: {parsed.get('format', 'unknown')}")
            
            if 'metadata' in parsed:
                metadata = parsed['metadata']
                logger.info(f"   - Pages/Rows: {metadata.get('num_pages', metadata.get('num_rows', 0))}")
                logger.info(f"   - Columns: {metadata.get('num_columns', 'N/A')}")
                logger.info(f"   - Has Tables: {metadata.get('has_tables', False)}")
                
                # Log sample data for CSV
                if detection['parser'] == 'csv' and 'columns' in metadata:
                    logger.info(f"   - Column Names: {', '.join(metadata['columns'][:5])}")
                    if len(metadata['columns']) > 5:
                        logger.info(f"     ... and {len(metadata['columns']) - 5} more")
            
            # Step 4: Validate parsed data
            logger.info("")
            logger.info("─" * 80)
            logger.info("STEP 4: DATA VALIDATION")
            logger.info("─" * 80)
            
            validation = self._validate_parsed_data(parsed)
            
            logger.info(f"📊 Quality Score: {validation['quality_score']}/100")
            
            if validation['errors']:
                logger.error(f" Errors Found: {len(validation['errors'])}")
                for error in validation['errors']:
                    logger.error(f"   - {error}")
            
            if validation['warnings']:
                logger.warning(f"⚠️ Warnings: {len(validation['warnings'])}")
                for warning in validation['warnings'][:3]:  # Show first 3
                    logger.warning(f"   - {warning}")
                if len(validation['warnings']) > 3:
                    logger.warning(f"   ... and {len(validation['warnings']) - 3} more warnings")
            
            if validation.get('suggestions'):
                logger.info("💡 Suggestions:")
                for suggestion in validation['suggestions'][:2]:
                    logger.info(f"   - {suggestion}")
            
            # Step 5: Format and store results
            logger.info("")
            logger.info("─" * 80)
            logger.info("STEP 5: PREPARING OUTPUT")
            logger.info("─" * 80)
            
            parsed_data = {
                "type": detection['extension'].replace('.', ''),
                "text": parsed["text"],
                "raw_dict": parsed.get("raw_dict", {}),
                "metadata": parsed.get("metadata", {}),
                "parser_used": detection['parser'],
                "detection_info": detection,
                "validation": validation,
                
                # Additional metadata
                "has_tables": parsed.get("metadata", {}).get("has_tables", False),
                "num_pages": parsed.get("metadata", {}).get("num_pages", 0),
                "num_rows": parsed.get("metadata", {}).get("num_rows", 0),
                "num_columns": parsed.get("metadata", {}).get("num_columns", 0),
                
                # Include dataframe for CSV files
                "dataframe": parsed.get("dataframe") if detection['parser'] == 'csv' else None
            }
            
            # Update state
            state["parsed_data"] = parsed_data
            state["file_type"] = detection['extension'].replace('.', '')
            state["parser_used"] = detection['parser']
            state["validation_errors"] = validation['errors']
            state["validation_warnings"] = validation['warnings']
            state["quality_score"] = validation['quality_score']
            state["parse_duration"] = parse_duration
            state["current_step"] = "ingestion_complete"
            
            # Update statistics
            self.stats['total_files'] += 1
            self.stats['successful_parses'] += 1
            if detection['parser'] == 'csv':
                self.stats['csv_files'] += 1
            else:
                self.stats['docling_files'] += 1
            
            # Update average quality score
            total_quality = self.stats['average_quality_score'] * (self.stats['total_files'] - 1)
            self.stats['average_quality_score'] = (total_quality + validation['quality_score']) / self.stats['total_files']
            
            logger.info(f" Output prepared successfully")
            logger.info(f"📦 State updated with parsed data")
            
            logger.info("")
            logger.info("="*80)
            logger.info(" INGESTION COMPLETED SUCCESSFULLY")
            logger.info("="*80)
            logger.info(f"⏱️ Total Duration: {parse_duration:.2f}s")
            logger.info(f"📊 Quality Score: {validation['quality_score']}/100")
            logger.info(f"🎯 Parser Used: {detection['parser'].upper()}")
            logger.info("="*80)
            logger.info("")
            
            return state
            
        except Exception as e:
            logger.error("")
            logger.error("="*80)
            logger.error(" INGESTION FAILED")
            logger.error("="*80)
            logger.error(f"Error: {str(e)}")
            logger.error("="*80)
            logger.error("")
            
            self.stats['total_files'] += 1
            self.stats['failed_parses'] += 1
            
            return self.handle_error(state, e)
    
    def _get_file_size(self, file_path: str) -> str:
        """Get human-readable file size"""
        try:
            size_bytes = Path(file_path).stat().st_size
            
            if size_bytes < 1024:
                return f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.2f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.2f} MB"
        except:
            return "Unknown"
    
    def _detect_file_type(self, file_path: str) -> Dict[str, Any]:
        """Detect file type and recommend parser"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        warnings = []
        
        # CSV extensions
        csv_extensions = ['.csv', '.tsv', '.txt']
        # Docling extensions
        docling_extensions = ['.pdf', '.docx', '.pptx', '.xlsx', '.xls', '.html', '.md', '.png', '.jpg', '.jpeg']
        
        if extension in csv_extensions:
            parser = 'csv'
            if not CSV_PARSER_AVAILABLE:
                warnings.append("CSV parser not available, will try Docling")
                parser = 'docling'
        
        elif extension in docling_extensions:
            parser = 'docling'
            if not DOCLING_AVAILABLE:
                warnings.append("Docling not available")
                parser = None
        
        else:
            warnings.append(f"Unknown file extension: {extension}")
            parser = None
        
        return {
            'extension': extension,
            'parser': parser,
            'warnings': warnings,
            'mime_type': self._detect_mime_type(file_path)
        }
    
    def _detect_mime_type(self, file_path: Path) -> str:
        """Detect MIME type"""
        try:
            import magic
            mime = magic.Magic(mime=True)
            return mime.from_file(str(file_path))
        except:
            return "Unknown"
    
    def _get_parser(self, parser_type: str):
        """Get parser instance"""
        if parser_type == 'csv':
            return self.csv_parser
        elif parser_type == 'docling':
            return self.docling_parser
        return None
    
    def _validate_parsed_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simple validation of parsed data"""
        errors = []
        warnings = []
        suggestions = []
        
        # Check text
        text = parsed_data.get('text', '')
        if not text or len(text) < 10:
            errors.append("Extracted text is empty or too short")
        
        # Check for financial indicators
        financial_terms = ['invoice', 'bill', 'amount', 'total', 'date', 'vendor', 'customer']
        found_terms = sum(1 for term in financial_terms if term.lower() in text.lower())
        
        if found_terms < 2:
            warnings.append("Few financial terms found in text")
        
        # Calculate quality score
        score = 100
        score -= len(errors) * 30
        score -= len(warnings) * 10
        score = max(0, min(100, score))
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions,
            'quality_score': score
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        return {
            **self.stats,
            'success_rate': round(
                (self.stats['successful_parses'] / self.stats['total_files'] * 100)
                if self.stats['total_files'] > 0 else 0,
                2
            )
        }