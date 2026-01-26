#!/usr/bin/env python3
"""
Debug script to test document extraction patterns
"""

import re
import json

def test_extraction():
    # November invoice text content
    text = """SpaceMarvel AI 
Unit 101, Oxford Towers, 139, HAL Old Airport Rd, H.A.L II Stage,
Bangalore North, Bengaluru,
Karnataka, India, 560008
Invoice Num926415000001019033
Issued Date
01-11-2025 
Due Date14-11-2025
INVOICE
Authority Signature
 Sub Total         ₹ 2,15,238.15     
 GST        ₹ 38,742.87     
    
Grand Total ₹ 2,53,981.02
 
Bill To:
BrandOla 
RTC 2, T.T.C. Industrial Area, MIDC Industrial Area, Rabale, Navi Mumbai, 
Maharashtra, India, 
400701
 
 
 
Terms & Conditions
Bank Details:
Account Name :
METASPACE MARVEL AI PRIVATE LIMITED
Account No. :
036005018088
IFSC Code :
ICIC0000360
Bank Name :
ICICI Bank
GST : 29AASCM2299L1ZG
Product NameList PriceQtyAmount
BrandOla's AI Platform & Planogram₹ 2,00,000.001₹ 2,00,000.00
Google Cloud Console (1 Sep – 31 Oct 2025)₹ 15,238.151₹ 15,238.15"""

    print("🔍 Testing November Invoice Extraction")
    print("=" * 50)
    
    # Test Grand Total patterns
    grand_patterns = [
        r'Grand\s+Total[:\s]+[$₹€]?\s*([\d,]+\.?\d{0,2})',
        r'Grand\s+Total\s+[$₹€]?\s*([\d,]+\.?\d{0,2})',
        r'Grand\s+Total\s+\|\s*[$₹€]?\s*([\d,]+\.?\d{0,2})',
    ]
    
    print("Testing Grand Total patterns:")
    for i, pattern in enumerate(grand_patterns, 1):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"  ✅ Pattern {i}: {pattern}")
            print(f"     Matched: '{match.group(0)}' -> Amount: '{match.group(1)}'")
        else:
            print(f"  ❌ Pattern {i}: {pattern}")
    
    # Test Sub Total patterns
    subtotal_patterns = [
        r'Sub\s+Total\s+\|\s*₹?\s*([\d,]+\.?\d{0,2})',
        r'Sub\s+Total\s+₹?\s*([\d,]+\.?\d{0,2})',
        r'Sub\s+Total[:\s]*₹?\s*([\d,]+\.?\d{0,2})',
    ]
    
    print("\nTesting Sub Total patterns:")
    for i, pattern in enumerate(subtotal_patterns, 1):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"  ✅ Pattern {i}: {pattern}")
            print(f"     Matched: '{match.group(0)}' -> Amount: '{match.group(1)}'")
        else:
            print(f"  ❌ Pattern {i}: {pattern}")
    
    # Test GST patterns
    gst_patterns = [
        r'GST[:\s]+₹?\s*([\d,]+\.?\d{2})',
        r'GST\s+₹?\s*([\d,]+\.?\d{2})',
        r'GST\s+([\d,]+\.?\d{2})',
    ]
    
    print("\nTesting GST patterns:")
    for i, pattern in enumerate(gst_patterns, 1):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"  ✅ Pattern {i}: {pattern}")
            print(f"     Matched: '{match.group(0)}' -> Amount: '{match.group(1)}'")
        else:
            print(f"  ❌ Pattern {i}: {pattern}")
    
    # Test invoice number patterns
    number_patterns = [
        r'Invoice\s+Number[:\s]+([A-Z0-9-]+)',
        r'Invoice\s+No\.?[:\s]+([A-Z0-9-]+)',
        r'Order\s+Number[:\s]+(\d+)',
        r'Order\s*#[:\s]*(\d+)',
        r'(?:INV|ORD|REC)[:\s#-]+([A-Z0-9-]+)',
        r'#\s*([A-Z]{2,}\d{3,})',
    ]
    
    print("\nTesting Invoice Number patterns:")
    for i, pattern in enumerate(number_patterns, 1):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"  ✅ Pattern {i}: {pattern}")
            print(f"     Matched: '{match.group(0)}' -> Number: '{match.group(1)}'")
        else:
            print(f"  ❌ Pattern {i}: {pattern}")
    
    # Test vendor name patterns
    vendor_patterns = [
        r'([A-Z][A-Za-z\s&,\.]+(?:Inc\.|LLC|Ltd\.|Limited|Corp\.|Corporation|Company))',
        r'##\s+([A-Z][A-Za-z\s&,\.]+(?:Inc\.|LLC|Ltd\.|Limited|Corp\.))',
        r'##\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    ]
    
    print("\nTesting Vendor Name patterns:")
    for i, pattern in enumerate(vendor_patterns, 1):
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            print(f"  ✅ Pattern {i}: {pattern}")
            print(f"     Matched: '{match.group(0)}' -> Name: '{match.group(1)}'")
        else:
            print(f"  ❌ Pattern {i}: {pattern}")

if __name__ == "__main__":
    test_extraction()