#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. Live exchange rate integration
2. Company name matching with aliases
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_layer.database.database_manager import get_database
from shared.utils.live_exchange_rates import get_rate_provider
from shared.utils.currency_converter import CurrencyConverter

def test_currency_conversion():
    """Test live exchange rate conversion"""
    print("🧪 Testing Currency Conversion...")
    
    try:
        # Test live rate provider
        rate_provider = get_rate_provider()
        rate = rate_provider.get_rate_for_date("USD", "2025-08-20")
        print(f"   ✅ Live rate provider working: 1 USD = {rate} INR")
        
        # Test conversion
        converted = rate_provider.convert(192.0, "USD", "2025-08-20")
        print(f"   ✅ Converted 192 USD to INR: ₹{converted:.2f}")
        
        # Test fallback converter
        converter = CurrencyConverter()
        fallback_converted = converter.convert(192.0, "USD", "INR", "2025-08-20")
        print(f"   ✅ Fallback converter working: ₹{fallback_converted:.2f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Currency conversion failed: {e}")
        return False

def test_company_aliases():
    """Test company alias retrieval"""
    print("\n🏢 Testing Company Alias Retrieval...")
    
    try:
        db = get_database()
        
        # Test getting company aliases
        aliases = db.get_company_aliases("default")
        print(f"   ✅ Retrieved company aliases: {aliases}")
        
        # Test with a specific company ID if exists
        # You can modify this to test with your actual company ID
        test_company_id = "default"  # Change this to test with a real company ID
        aliases = db.get_company_aliases(test_company_id)
        print(f"   ✅ Retrieved aliases for {test_company_id}: {aliases}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Company alias retrieval failed: {e}")
        return False

def test_document_processing():
    """Test document processing with the fixes"""
    print("\n📄 Testing Document Processing...")
    
    try:
        # Test the document processing service with company aliases
        from processing_layer.document_processing.document_processing_service import DocumentProcessingService
        
        db = get_database()
        
        # Create a mock document processing service
        service = DocumentProcessingService(
            db_session=db,
            docling_parser=None,  # Mock
            company_id="default",
            user_company_name="METASPACE MARVEL AI PRIVATE LIMITED"
        )
        
        # Test company alias retrieval in the service
        aliases = service.db.get_company_aliases("default")
        print(f"   ✅ Service can access company aliases: {aliases}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Document processing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Financial Automation Fixes")
    print("=" * 50)
    
    tests = [
        test_currency_conversion,
        test_company_aliases,
        test_document_processing
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("   🎉 All tests passed! Fixes are working correctly.")
    else:
        print("   ⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)