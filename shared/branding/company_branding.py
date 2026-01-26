# Compatibility function for legacy imports
def get_company_info(user_id: str = None) -> dict:
    """Return example or default company branding info (for compatibility)"""
    # In a real implementation, this would fetch from CompanyBrandingManager
    return {
        "company_name": "Example Corp",
        "logo_url": "",
        "primary_color": "#1976D2",
        "secondary_color": "#424242",
        "accent_color": "#FFC107"
    }
"""
Company Branding Manager
Handles company logo, name, and color customization
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import json
from datetime import datetime

from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class CompanyBrandingManager:
    """
    Company Branding Manager
    
    Manages:
    - Company logo (image)
    - Company name
    - Brand colors (primary, secondary, accent)
    - Theme settings
    
    Stores per user/company
    """
    
    def __init__(self, storage_dir: str = "./data/branding"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.logos_dir = self.storage_dir / "logos"
        self.logos_dir.mkdir(exist_ok=True)
        
        self.config_file = self.storage_dir / "branding_config.json"
        
        self.logger = logger
        
        # Load existing branding configs
        self.brandings = self._load_brandings()
    
    def create_branding(
        self,
        user_id: str,
        company_name: str,
        logo_path: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        accent_color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create company branding profile
        
        Args:
            user_id: User/company identifier
            company_name: Company name
            logo_path: Path to logo image
            primary_color: Primary brand color (hex)
            secondary_color: Secondary color (hex)
            accent_color: Accent color (hex)
            
        Returns:
            Branding configuration
        """
        
        # Auto-generate colors if not provided
        if not primary_color:
            primary_color = self._generate_color_from_name(company_name)
        
        if not secondary_color:
            secondary_color = self._lighten_color(primary_color)
        
        if not accent_color:
            accent_color = self._complementary_color(primary_color)
        
        # Process logo if provided
        logo_filename = None
        if logo_path and Path(logo_path).exists():
            logo_filename = self._process_logo(user_id, logo_path)
        
        # Create branding config
        branding = {
            "user_id": user_id,
            "company_name": company_name,
            "logo_filename": logo_filename,
            "colors": {
                "primary": primary_color,
                "secondary": secondary_color,
                "accent": accent_color,
                "text": "#000000",
                "background": "#FFFFFF"
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Save
        self.brandings[user_id] = branding
        self._save_brandings()
        
        self.logger.info(f"Created branding for {company_name} (user: {user_id})")
        
        return branding
    
    def update_branding(
        self,
        user_id: str,
        company_name: Optional[str] = None,
        logo_path: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        accent_color: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update existing branding"""
        
        if user_id not in self.brandings:
            raise ValueError(f"No branding found for user: {user_id}")
        
        branding = self.brandings[user_id]
        
        # Update fields
        if company_name:
            branding["company_name"] = company_name
        
        if logo_path and Path(logo_path).exists():
            branding["logo_filename"] = self._process_logo(user_id, logo_path)
        
        if primary_color:
            branding["colors"]["primary"] = primary_color
        
        if secondary_color:
            branding["colors"]["secondary"] = secondary_color
        
        if accent_color:
            branding["colors"]["accent"] = accent_color
        
        branding["updated_at"] = datetime.now().isoformat()
        
        # Save
        self._save_brandings()
        
        self.logger.info(f"Updated branding for user: {user_id}")
        
        return branding
    
    def get_branding(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get branding for user"""
        return self.brandings.get(user_id)
    
    def get_logo_path(self, user_id: str) -> Optional[Path]:
        """Get full path to logo file"""
        branding = self.get_branding(user_id)
        
        if not branding or not branding.get("logo_filename"):
            return None
        
        logo_path = self.logos_dir / branding["logo_filename"]
        
        if logo_path.exists():
            return logo_path
        
        return None
    
    def _process_logo(self, user_id: str, logo_path: str) -> str:
        """
        Process and save logo
        - Resize to standard size
        - Convert to PNG
        - Save with user_id prefix
        """
        
        try:
            # Open image
            img = Image.open(logo_path)
            
            # Resize to max 200x100 (maintain aspect ratio)
            max_width = 200
            max_height = 100
            
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Convert to RGBA (supports transparency)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Save
            filename = f"{user_id}_logo.png"
            save_path = self.logos_dir / filename
            img.save(save_path, "PNG")
            
            self.logger.info(f"Logo processed and saved: {filename}")
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Failed to process logo: {e}")
            return None
    
    def _generate_color_from_name(self, name: str) -> str:
        """Generate color from company name (deterministic)"""
        
        # Hash company name
        hash_val = abs(hash(name))
        
        # Generate RGB values
        r = (hash_val % 180) + 50  # 50-230
        g = ((hash_val // 256) % 180) + 50
        b = ((hash_val // 65536) % 180) + 50
        
        # Convert to hex
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def _lighten_color(self, hex_color: str, factor: float = 0.3) -> str:
        """Lighten a hex color"""
        
        # Remove #
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Lighten
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        
        # Back to hex
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def _complementary_color(self, hex_color: str) -> str:
        """Get complementary color"""
        
        hex_color = hex_color.lstrip('#')
        
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Complementary
        r = 255 - r
        g = 255 - g
        b = 255 - b
        
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def _load_brandings(self) -> Dict[str, Dict]:
        """Load branding configurations"""
        
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load brandings: {e}")
            return {}
    
    def _save_brandings(self):
        """Save branding configurations"""
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.brandings, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save brandings: {e}")
    
    def list_brandings(self) -> Dict[str, str]:
        """List all configured brandings"""
        
        return {
            user_id: branding["company_name"]
            for user_id, branding in self.brandings.items()
        }