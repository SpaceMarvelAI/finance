import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Force load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Connecting to: {DATABASE_URL}")

def fix_company_schema():
    # SQL to add the missing column
    sql = """
    ALTER TABLE companies 
    ADD COLUMN IF NOT EXISTS company_aliases TEXT[];
    """
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("🔧 Patching 'companies' table...")
        cursor.execute(sql)
        conn.commit()
        
        print("✅ SUCCESS: Added 'company_aliases' column!")
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_company_schema()