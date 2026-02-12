"""
Branding Loader Node
Loads company branding from database for use in report templates
"""

from typing import Dict, Any
from processing_layer.workflows.nodes.base_node import BaseNode, register_node
from data_layer.database.database_manager import get_database


@register_node
class BrandingLoaderNode(BaseNode):
    """
    Loads company branding from database
    Provides branding configuration for report templates
    """
    
    name = "Branding Loader"
    category = "output"
    description = "Loads company logo, colors, and branding settings from database"
    
    input_schema = {
        "company_id": {"type": "string", "required": True}
    }
    
    output_schema = {
        "branding": {"type": "object", "description": "Company branding configuration"},
        "company_name": {"type": "string", "description": "Company name"},
        "logo_path": {"type": "string", "description": "Path to company logo"},
        "colors": {"type": "object", "description": "Brand colors"},
        "currency": {"type": "string", "description": "Default currency"}
    }
    
    ALLOWED_PARAMS = ["company_id"]
    
    def __init__(self):
        super().__init__()
        self.db = get_database()
    
    def run(self, input_data: Any, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Load company branding from database
        
        Args:
            input_data: Not used (branding is loaded by company_id)
            params: {company_id}
            
        Returns:
            Branding configuration
        """
        params = params or {}
        company_id = params.get('company_id')
        
        if not company_id:
            raise ValueError("Company ID is required")
        
        try:
            branding = self.load_branding_from_db(company_id)
            
            self.logger.info(f"Loaded branding for company: {branding['company_name']}")
            
            return {
                'branding': branding,
                'company_name': branding['company_name'],
                'logo_path': branding['logo_path'],
                'colors': branding['colors'],
                'currency': branding['currency']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load branding: {e}")
            raise ValueError(f"Could not load branding for company {company_id}")
    
    def load_branding_from_db(self, company_id: str) -> Dict[str, Any]:
        """
        Load branding configuration from database
        
        Args:
            company_id: Company identifier
            
        Returns:
            Branding configuration
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT 
                    name,
                    logo_url,
                    primary_color,
                    secondary_color,
                    accent_color,
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
                        'accent': result[4]  # From company setup API
                    },
                    'currency': result[5]  # From company setup API
                }
                return branding
            else:
                raise ValueError(f"No company found with ID: {company_id}")
                
        except Exception as e:
            self.logger.error(f"Database error loading branding: {e}")
            raise e
    
    def get_branding_for_company(self, company_id: str) -> Dict[str, Any]:
        """
        Get branding configuration for a company
        
        Args:
            company_id: Company identifier
            
        Returns:
            Branding configuration
        """
        return self.load_branding_from_db(company_id)
    
    def validate_branding(self, branding: Dict[str, Any]) -> bool:
        """
        Validate branding configuration
        
        Args:
            branding: Branding configuration
            
        Returns:
            True if valid
        """
        required_fields = ['company_name', 'colors', 'currency']
        
        for field in required_fields:
            if field not in branding:
                self.logger.error(f"Missing required branding field: {field}")
                return False
        
        # Validate colors
        colors = branding.get('colors', {})
        color_fields = ['primary', 'secondary', 'accent']
        
        for color_field in color_fields:
            if color_field not in colors:
                self.logger.warning(f"Missing color field: {color_field}")
                # Don't fail validation, just warn - templates can use defaults
        
        return True