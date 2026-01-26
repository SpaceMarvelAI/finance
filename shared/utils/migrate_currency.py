"""
Database Migration - Add Currency Support
Adds currency fields to documents table
"""

import psycopg2
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_add_currency_fields(host="localhost", database="financial_automation", 
                                  user="postgres", password="postgres"):
    """
    Add currency fields to documents table
    
    New fields:
    - original_currency: Currency of the document (USD, EUR, GBP, etc.)
    - original_amount: Amount in original currency
    - inr_amount: Converted amount in INR
    - exchange_rate: Exchange rate used for conversion
    """
    
    logger.info("Starting currency fields migration...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        
        cursor = conn.cursor()
        
        # Add currency columns
        logger.info("Adding currency columns...")
        
        cursor.execute("""
            ALTER TABLE documents 
            ADD COLUMN IF NOT EXISTS original_currency TEXT DEFAULT 'INR',
            ADD COLUMN IF NOT EXISTS original_amount DECIMAL(15, 2) DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS inr_amount DECIMAL(15, 2) DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS exchange_rate DECIMAL(10, 4) DEFAULT 1.0
        """)
        
        # Update existing records - set INR amounts for existing data
        logger.info("Updating existing records...")
        
        cursor.execute("""
            UPDATE documents 
            SET original_currency = 'INR',
                original_amount = grand_total,
                inr_amount = grand_total,
                exchange_rate = 1.0
            WHERE original_currency IS NULL OR original_currency = ''
        """)
        
        conn.commit()
        
        logger.info("✓ Currency migration completed successfully")
        logger.info(f"  - Added: original_currency, original_amount, inr_amount, exchange_rate")
        
        # Show updated schema
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'documents' 
            AND column_name LIKE '%currency%' OR column_name LIKE '%inr%' OR column_name LIKE '%rate%'
        """)
        
        columns = cursor.fetchall()
        logger.info("New currency columns:")
        for col in columns:
            logger.info(f"  - {col[0]}: {col[1]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    # Run migration
    import sys
    
    # Get password from command line or use default
    password = sys.argv[1] if len(sys.argv) > 1 else "postgres"
    
    success = migrate_add_currency_fields(password=password)
    
    if success:
        print(" Migration completed successfully!")
    else:
        print(" Migration failed!")