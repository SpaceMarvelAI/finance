"""
Universal Document Parser using Docling
Handles PDF, Excel, CSV, Word, PowerPoint, and images
"""

from typing import Dict, Any
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat

from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class UniversalDoclingParser:
    """
    Universal parser using Docling for all document types
    
    Supported formats:
    - PDF (digital and scanned)
    - Excel (.xlsx, .xls)
    - Word (.docx)
    - PowerPoint (.pptx)
    - Images (.png, .jpg, .jpeg)
    - HTML
    - Markdown
    """
    
    # Docling supported formats
    SUPPORTED_FORMATS = {
        ".pdf": InputFormat.PDF,
        ".docx": InputFormat.DOCX,
        ".pptx": InputFormat.PPTX,
        ".html": InputFormat.HTML,
        ".htm": InputFormat.HTML,
        ".md": InputFormat.MD,
        ".png": InputFormat.IMAGE,
        ".jpg": InputFormat.IMAGE,
        ".jpeg": InputFormat.IMAGE,
        ".xlsx": InputFormat.XLSX,  # Docling can handle Excel
        ".xls": InputFormat.XLSX,
    }
    
    def __init__(self):
        """Initialize Docling converter"""
        try:
            self.converter = DocumentConverter()
            logger.info("Universal Docling parser initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Docling: {e}")
            raise
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file can be parsed by Docling"""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_FORMATS
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse any supported document format
        
        Args:
            file_path: Path to document
            
        Returns:
            Dictionary with:
                - text: Extracted text content
                - raw_dict: Raw document structure
                - metadata: Document metadata
                - format: File format
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = file_path.suffix.lower()
        
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {ext}. "
                f"Supported: {list(self.SUPPORTED_FORMATS.keys())}"
            )
        
        try:
            logger.info(f"Parsing {ext} file: {file_path.name}")
            
            # Convert document
            result = self.converter.convert(str(file_path))
            
            # Export to markdown for consistent structure
            try:
                markdown_text = result.document.export_to_markdown()
            except Exception as e:
                logger.warning(f"Markdown export failed: {e}, using alternative")
                markdown_text = self._extract_text_fallback(result.document)
            
            # Get raw structure
            try:
                raw_dict = result.document.model_dump()
            except Exception as e:
                logger.warning(f"Model dump failed: {e}, using minimal dict")
                raw_dict = {"pages": []}
            
            # Extract metadata
            metadata = self._extract_metadata(raw_dict, ext)
            
            logger.info(
                f"Parsed successfully: {len(markdown_text)} chars, "
                f"{metadata.get('num_pages', 0)} pages"
            )
            
            return {
                "text": markdown_text,
                "raw_dict": raw_dict,
                "metadata": metadata,
                "format": ext
            }
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path.name}: {e}")
            raise
    
    def _extract_text_fallback(self, document) -> str:
        """Fallback text extraction if markdown export fails"""
        text = ""
        try:
            if hasattr(document, 'pages'):
                for page in document.pages:
                    if hasattr(page, 'text'):
                        text += page.text + "\n"
            else:
                text = str(document)
        except:
            text = str(document)
        return text
    
    def _extract_metadata(self, raw_dict: dict, file_format: str) -> Dict[str, Any]:
        """Extract metadata from document structure"""
        
        pages = raw_dict.get("pages", [])
        
        # Count pages safely
        num_pages = len(pages) if isinstance(pages, list) else 0
        
        # Check for tables and images
        has_tables = False
        has_images = False
        table_count = 0
        image_count = 0
        
        if isinstance(pages, list):
            for page in pages:
                if isinstance(page, dict):
                    items = page.get("items", [])
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                item_type = item.get("type", "")
                                if item_type == "table":
                                    has_tables = True
                                    table_count += 1
                                elif item_type == "image":
                                    has_images = True
                                    image_count += 1
        
        return {
            "num_pages": num_pages,
            "has_tables": has_tables,
            "has_images": has_images,
            "table_count": table_count,
            "image_count": image_count,
            "format": file_format,
            "parser": "docling"
        }
    
    def extract_tables(self, file_path: str) -> list:
        """
        Extract tables from document
        
        Args:
            file_path: Path to document
            
        Returns:
            List of tables as dictionaries
        """
        parsed = self.parse(file_path)
        raw_dict = parsed["raw_dict"]
        
        tables = []
        pages = raw_dict.get("pages", [])
        
        if isinstance(pages, list):
            for page in pages:
                if isinstance(page, dict):
                    items = page.get("items", [])
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and item.get("type") == "table":
                                tables.append(item)
        
        logger.info(f"Extracted {len(tables)} tables")
        return tables