"""
Database Initialization Script
Creates user_settings table in PostgreSQL
"""

import psycopg2
from shared.config.logging_config import get_logger

logger = get_logger(__name__)


def init_user_settings_table():
    """
    Initialize user_settings table in PostgreSQL
    
    Run this once to create the table
    """
    
    # Database configuration
    db_config = {
        "host": "localhost",
        "database": "financial_automation",
        "user": "postgres",
        "password": "postgres"
    }
    
    # SQL to create table
    create_table_sql = """
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
    
    -- Create index on user_id for fast lookups
    CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);
    
    -- Create index on company_name for searches
    CREATE INDEX IF NOT EXISTS idx_user_settings_company_name ON user_settings(company_name);
    """
    
    try:
        # Connect to database
        logger.info("Connecting to PostgreSQL...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Create table
        logger.info("Creating user_settings table...")
        cursor.execute(create_table_sql)
        conn.commit()
        
        # Verify table exists
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_settings'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        logger.info(f" user_settings table created successfully!")
        logger.info(f"   Columns: {len(columns)}")
        
        for col_name, col_type in columns[:5]:
            logger.info(f"   - {col_name}: {col_type}")
        
        logger.info("   ... and more")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f" Failed to create user_settings table: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_default_user():
    """
    Create default user for testing
    
    Creates 'spacemarvel' user with company name
    """
    
    from shared.tools.user_settings import get_settings_manager
    
    settings_mgr = get_settings_manager()
    
    try:
        # Check if user already exists
        existing = settings_mgr.get_user_settings("spacemarvel")
        
        if existing:
            logger.info(" Default user 'spacemarvel' already exists")
            logger.info(f"   Company: {existing['company_name']}")
            return True
        
        # Create new user
        logger.info("Creating default user 'spacemarvel'...")
        
        user_settings = settings_mgr.create_user(
            user_id="spacemarvel",
            company_name="METASPACE MARVEL AI PRIVATE LIMITED",
            email="contact@spacemarvel.ai",
            logo_path="/data/branding/logos/spacemarvel.png",
            primary_color="#1a73e8",
            secondary_color="#34a853",
            accent_color="#fbbc04",
            address_line1="123 Innovation Street",
            city="Bangalore",
            state="Karnataka",
            country="India",
            postal_code="560001",
            default_currency="INR",
            sla_days=30
        )
        
        logger.info(" Default user created successfully!")
        logger.info(f"   User ID: {user_settings['user_id']}")
        logger.info(f"   Company: {user_settings['company_name']}")
        
        return True
        
    except Exception as e:
        logger.error(f" Failed to create default user: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_setup():
    """
    Verify the setup is complete
    
    Checks:
    1. Table exists
    2. Default user exists
    3. Can read user settings
    """
    
    from shared.tools.user_settings import get_settings_manager
    
    logger.info("\n" + "="*60)
    logger.info("VERIFYING USER SETTINGS SETUP")
    logger.info("="*60)
    
    try:
        settings_mgr = get_settings_manager()
        
        # Test 1: Get user settings
        settings = settings_mgr.get_user_settings("spacemarvel")
        
        if settings:
            logger.info(" Test 1: Read user settings - PASSED")
            logger.info(f"   Company: {settings['company_name']}")
        else:
            logger.error(" Test 1: Read user settings - FAILED")
            return False
        
        # Test 2: Get company name (used for categorization)
        company_name = settings_mgr.get_company_name("spacemarvel")
        
        if company_name:
            logger.info(" Test 2: Get company name - PASSED")
            logger.info(f"   Name: {company_name}")
        else:
            logger.error(" Test 2: Get company name - FAILED")
            return False
        
        # Test 3: Get branding (used for reports)
        branding = settings_mgr.get_branding("spacemarvel")
        
        if branding:
            logger.info(" Test 3: Get branding - PASSED")
            logger.info(f"   Logo: {branding.get('logo_path')}")
            logger.info(f"   Primary color: {branding['colors']['primary']}")
        else:
            logger.error(" Test 3: Get branding - FAILED")
            return False
        
        logger.info("\n" + "="*60)
        logger.info(" ALL TESTS PASSED - SETUP COMPLETE!")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f" Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    """
    Run this script to initialize the database
    
    Usage:
        python3 init_user_settings_db.py
    """
    
    print("\n" + "="*60)
    print("USER SETTINGS DATABASE INITIALIZATION")
    print("="*60 + "\n")
    
    # Step 1: Create table
    print("Step 1: Creating user_settings table...")
    if not init_user_settings_table():
        print(" Failed to create table. Exiting.")
        exit(1)
    
    print("\n" + "-"*60 + "\n")
    
    # Step 2: Create default user
    print("Step 2: Creating default user...")
    if not create_default_user():
        print(" Failed to create default user. Exiting.")
        exit(1)
    
    print("\n" + "-"*60 + "\n")
    
    # Step 3: Verify setup
    print("Step 3: Verifying setup...")
    if not verify_setup():
        print(" Verification failed. Exiting.")
        exit(1)
    
    print("\n" + "="*60)
    print(" DATABASE INITIALIZATION COMPLETE!")
    print("="*60)
    print("\nYou can now:")
    print("1. Start the API: python3 api.py")
    print("2. Upload documents: They will auto-categorize using company name")
    print("3. Generate reports: They will use branding from user settings")
    print("\nTo update settings:")
    print("  curl -X PUT http://localhost:8000/users/spacemarvel/settings \\")
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"company_name": "NEW NAME"}\'')
    print()