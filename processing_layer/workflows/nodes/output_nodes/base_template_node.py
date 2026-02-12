"""
Base Template Node
Base class for all report template nodes with branding support
Uses company branding from database setup API
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod
from datetime import datetime
from processing_layer.workflows.nodes.base_node import BaseNode, register_node
from data_layer.database.database_manager import get_database


@register_node
class BaseTemplateNode(BaseNode):
    """
    Base class for all report templates
    Provides common functionality for loading branding and validating data
    """
    
    name = "Base Template"
    category = "output"
    description = "Base class for report templates with branding support"
    
    input_schema = {
        "data": {"type": "any", "required": True},
        "company_id": {"type": "string", "required": True}
    }
    
    output_schema = {
        "file_path": {"type": "string", "description": "Path to generated report file"},
        "branding_applied": {"type": "boolean", "description": "Whether branding was applied"}
    }
    
    ALLOWED_PARAMS = ["company_id", "output_format", "include_charts", "template_style"]
    
    def __init__(self):
        super().__init__()
        self.db = get_database()
    
    def load_branding(self, company_id: str) -> Dict[str, Any]:
        """
        Load company branding from database
        Uses the company setup API data
        
        Args:
            company_id: Company identifier
            
        Returns:
            Branding configuration from database
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT 
                    name,
                    logo_url,
                    primary_color,
                    secondary_color,
                    currency
                FROM companies 
                WHERE id = %s
            """, (company_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                branding = {
                    'company_name': result[0],
                    'logo_path': result[1],
                    'colors': {
                        'primary': result[2],  # From company setup API
                        'secondary': result[3],  # From company setup API
                        'accent': '#FFC107'  # Default accent color
                    },
                    'currency': result[4]  # From company setup API
                }
                self.logger.info(f"Loaded branding for company: {branding['company_name']}")
                return branding
            else:
                self.logger.warning(f"No branding found for company: {company_id}")
                return self._get_default_branding()
                
        except Exception as e:
            self.logger.error(f"Failed to load branding: {e}")
            return self._get_default_branding()
    
    def _get_default_branding(self) -> Dict[str, Any]:
        """Get default branding when company branding is not available"""
        # These are minimal fallbacks - the system should always have company branding
        # from the company setup API
        return {
            'company_name': 'Financial Automation System',
            'logo_path': None,
            'colors': {
                'primary': None,  # Will use template defaults
                'secondary': None,
                'accent': None
            },
            'currency': 'INR'
        }
    
    def apply_branding(self, document, branding: Dict[str, Any]):
        """
        Apply branding to document (abstract method)
        
        Args:
            document: Document object (Excel workbook, PDF, etc.)
            branding: Branding configuration from database
        """
        raise NotImplementedError("Subclasses must implement apply_branding")
    
    def validate_data(self, data: Any) -> bool:
        """
        Validate data before rendering - override base validation to handle raw invoice data
        """
        if not data:
            self.logger.error("No data provided for template")
            return False
        
        # For raw invoice data (list of dicts), basic validation is sufficient
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return True
        
        # For formatted report data, check for required structure
        if isinstance(data, dict) and 'invoices' in data:
            return True
        
        self.logger.error("Invalid data format - expected list of invoices or dict with invoices")
        return False
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for this template type"""
        return ['data', 'company_id']
    
    def add_company_header(self, document, branding: Dict[str, Any], report_title: str):
        """
        Add company header with logo and title
        
        Args:
            document: Document object
            branding: Branding configuration from database
            report_title: Title of the report
        """
        # This will be implemented by subclasses
        pass
    
    def add_footer(self, document, branding: Dict[str, Any]):
        """Add footer with company info and page numbers"""
        # This will be implemented by subclasses
        pass
    
    def format_currency(self, amount: float, currency: str = None) -> str:
        """Format currency with appropriate symbol and formatting"""
        currency = currency or 'INR'
        
        if currency == 'INR':
            return f"₹{amount:,.2f}"
        elif currency == 'USD':
            return f"${amount:,.2f}"
        elif currency == 'EUR':
            return f"€{amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"
    
    def format_date(self, date_obj) -> str:
        """Format date consistently"""
        if isinstance(date_obj, str):
            return date_obj
        elif hasattr(date_obj, 'strftime'):
            return date_obj.strftime('%Y-%m-%d')
        else:
            return str(date_obj)
    
    def get_report_metadata(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get report metadata for file naming and tracking"""
        return {
            'report_type': params.get('report_type', 'report'),
            'generated_at': datetime.now().isoformat(),
            'company_id': params.get('company_id'),
            'output_format': params.get('output_format', 'excel'),
            'include_charts': params.get('include_charts', True)
        }
    
    def run(self, input_data: Any, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Base run method - should be overridden by subclasses
        
        Args:
            input_data: Report data
            params: Configuration parameters
            
        Returns:
            File path and metadata
        """
        params = params or {}
        company_id = params.get('company_id')
        
        if not company_id:
            raise ValueError("Company ID is required for branding")
        
        # Load branding from database (company setup API data)
        branding = self.load_branding(company_id)
        
        # Validate data using custom validation method
        if not self.validate_data(input_data):
            raise ValueError("Invalid data provided")
        
        # Subclasses should implement the actual template rendering
        return {
            'file_path': '',
            'branding_applied': True,
            'branding': branding
        }
