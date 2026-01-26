"""
Database Initialization Script
Creates tables and sets up initial data
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_layer.database.session import db_session
from data_layer.models.database_models import Company
from shared.config.logging_config import get_logger
import uuid


logger = get_logger(__name__)


def initialize_database():
    """Initialize database tables"""
    logger.info("Starting database initialization...")
    
    try:
        # Create all tables
        db_session.create_tables()
        logger.info("Database tables created successfully")
        
        # Create default company for testing
        create_default_company()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


def create_default_company():
    """Create a default company for testing"""
    try:
        with db_session.get_session() as session:
            # Check if default company exists
            existing = session.query(Company).filter(Company.name == "Test Company").first()
            
            if not existing:
                default_company = Company(
                    id=str(uuid.uuid4()),
                    name="Test Company",
                    tax_id="TEST123456",
                    primary_color="#1976D2",
                    secondary_color="#424242",
                    currency="USD"
                )
                
                session.add(default_company)
                session.commit()
                
                logger.info(f"Default company created with ID: {default_company.id}")
            else:
                logger.info("Default company already exists")
                
    except Exception as e:
        logger.error(f"Failed to create default company: {str(e)}")
        raise


def reset_database():
    """Reset database (drop and recreate all tables)"""
    logger.warning("Resetting database - ALL DATA WILL BE LOST")
    
    try:
        # Drop all tables
        db_session.drop_tables()
        
        # Recreate tables
        db_session.create_tables()
        
        # Create default company
        create_default_company()
        
        logger.info("Database reset completed")
        
    except Exception as e:
        logger.error(f"Database reset failed: {str(e)}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (WARNING: deletes all data)"
    )
    
    args = parser.parse_args()
    
    if args.reset:
        confirm = input("Are you sure you want to reset the database? (yes/no): ")
        if confirm.lower() == "yes":
            reset_database()
        else:
            logger.info("Database reset cancelled")
    else:
        initialize_database()