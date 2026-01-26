"""
USER SETTINGS & COMPANY CONFIGURATION SYSTEM

Everything comes from user account settings - NO hardcoding!
"""

# =============================================================================
# DATABASE SCHEMA
# =============================================================================

CREATE_USER_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    
    -- Company Information
    company_name TEXT NOT NULL,
    company_legal_name TEXT,
    tax_id TEXT,
    
    -- Address
    address_line1 TEXT,
    address_line2 TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    postal_code TEXT,
    
    -- Contact
    email TEXT,
    phone TEXT,
    website TEXT,
    
    -- Branding
    logo_path TEXT,
    primary_color TEXT DEFAULT '#1a73e8',
    secondary_color TEXT DEFAULT '#34a853',
    accent_color TEXT DEFAULT '#fbbc04',
    
    -- Settings
    default_currency TEXT DEFAULT 'INR',
    date_format TEXT DEFAULT 'MM/DD/YYYY',
    sla_days INTEGER DEFAULT 30,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_id ON user_settings(user_id);
"""

# =============================================================================
# PYTHON CLASS
# =============================================================================

from typing import Dict, Any, Optional
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from shared.config.logging_config import get_logger

logger = get_logger(__name__)


class UserSettingsManager:
    """
    Manages user account settings and company configuration
    
    All company-specific data comes from here:
    - Company name (for categorization)
    - Logo & colors (for reports)
    - Default settings (currency, SLA, etc.)
    """
    
    def __init__(self, db_config: Dict[str, str] = None):
        """
        Initialize settings manager
        
        Args:
            db_config: Database connection config
        """
        self.db_config = db_config or {
            "host": "localhost",
            "database": "financial_automation",
            "user": "postgres",
            "password": "postgres"
        }
        
        self.logger = logger
        self._init_database()
    
    def _init_database(self):
        """Initialize user settings table"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute(CREATE_USER_SETTINGS_TABLE)
            conn.commit()
            cursor.close()
            conn.close()
            self.logger.info("User settings table initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize user settings table: {e}")
    
    def create_user(
        self,
        user_id: str,
        company_name: str,
        email: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create new user account with settings
        
        Args:
            user_id: Unique user ID
            company_name: Company name (used for categorization!)
            email: User email
            **kwargs: Additional settings (logo_path, colors, address, etc.)
            
        Returns:
            Created user settings
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build insert query dynamically
            fields = ["user_id", "company_name"]
            values = [user_id, company_name]
            
            if email:
                fields.append("email")
                values.append(email)
            
            # Add optional fields
            for key, value in kwargs.items():
                if value is not None:
                    fields.append(key)
                    values.append(value)
            
            placeholders = ", ".join(["%s"] * len(values))
            fields_str = ", ".join(fields)
            
            query = f"""
                INSERT INTO user_settings ({fields_str})
                VALUES ({placeholders})
                RETURNING *
            """
            
            cursor.execute(query, values)
            user_settings = dict(cursor.fetchone())
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"User created: {user_id} - {company_name}")
            return user_settings
            
        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            raise
    
    def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user settings
        
        Args:
            user_id: User ID
            
        Returns:
            User settings dict or None
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                "SELECT * FROM user_settings WHERE user_id = %s",
                (user_id,)
            )
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get user settings: {e}")
            return None
    
    def update_user_settings(
        self,
        user_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Update user settings
        
        Args:
            user_id: User ID
            **kwargs: Fields to update
            
        Returns:
            Updated settings or None
        """
        try:
            if not kwargs:
                return self.get_user_settings(user_id)
            
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build update query
            set_clauses = []
            values = []
            
            for key, value in kwargs.items():
                set_clauses.append(f"{key} = %s")
                values.append(value)
            
            values.append(user_id)
            
            query = f"""
                UPDATE user_settings
                SET {", ".join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                RETURNING *
            """
            
            cursor.execute(query, values)
            result = dict(cursor.fetchone())
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"User settings updated: {user_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to update user settings: {e}")
            return None
    
    def get_company_name(self, user_id: str) -> str:
        """
        Get company name for categorization
        
        This is THE company name used to determine:
        - If seller = this name → SALES
        - If buyer = this name → PURCHASE
        
        Args:
            user_id: User ID
            
        Returns:
            Company name
        """
        settings = self.get_user_settings(user_id)
        if settings:
            return settings.get("company_name", "")
        return ""
    
    def get_branding(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get branding configuration for reports
        
        Returns:
            Branding dict with logo, colors, etc.
        """
        settings = self.get_user_settings(user_id)
        if not settings:
            return None
        
        return {
            "company_name": settings.get("company_name"),
            "logo_path": settings.get("logo_path"),
            "colors": {
                "primary": settings.get("primary_color", "#1a73e8"),
                "secondary": settings.get("secondary_color", "#34a853"),
                "accent": settings.get("accent_color", "#fbbc04")
            }
        }
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user settings"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM user_settings WHERE user_id = %s",
                (user_id,)
            )
            
            deleted = cursor.rowcount > 0
            conn.commit()
            cursor.close()
            conn.close()
            
            if deleted:
                self.logger.info(f"User deleted: {user_id}")
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"Failed to delete user: {e}")
            return False


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_settings_manager_instance = None


def get_settings_manager() -> UserSettingsManager:
    """Get or create settings manager (singleton)"""
    global _settings_manager_instance
    if _settings_manager_instance is None:
        _settings_manager_instance = UserSettingsManager()
    return _settings_manager_instance
