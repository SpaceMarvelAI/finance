"""
Currency Converter and Manager
Handles multiple currencies and converts to INR for reporting
"""

from typing import Dict, Optional
from datetime import datetime, date
from decimal import Decimal
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class CurrencyConverter:
    """
    Currency Converter with Exchange Rates
    
    Converts various currencies to INR (Indian Rupees) for standardized reporting
    """
    
    # Exchange rates to INR (as of December 2025)
    # Update these periodically or fetch from API
    EXCHANGE_RATES = {
        "INR": 1.0,      # Indian Rupee (base)
        "USD": 83.50,    # US Dollar
        "EUR": 91.20,    # Euro
        "GBP": 106.50,   # British Pound
        "AED": 22.75,    # UAE Dirham
        "SGD": 62.30,    # Singapore Dollar
        "JPY": 0.56,     # Japanese Yen
        "CNY": 11.55,    # Chinese Yuan
        "AUD": 54.20,    # Australian Dollar
        "CAD": 59.80,    # Canadian Dollar
        "CHF": 95.40,    # Swiss Franc
        "SAR": 22.25,    # Saudi Riyal
        "KWD": 272.50,   # Kuwaiti Dinar
        "QAR": 22.95,    # Qatari Riyal
        "OMR": 217.20,   # Omani Rial
        "BHD": 221.50,   # Bahraini Dinar
    }
    
    # Currency symbols mapping
    CURRENCY_SYMBOLS = {
        "₹": "INR",
        "Rs": "INR",
        "Rs.": "INR",
        "$": "USD",
        "USD": "USD",
        "US$": "USD",
        "€": "EUR",
        "EUR": "EUR",
        "£": "GBP",
        "GBP": "GBP",
        "AED": "AED",
        "Dhs": "AED",
        "SGD": "SGD",
        "S$": "SGD",
        "¥": "JPY",
        "JPY": "JPY",
        "CN¥": "CNY",
        "CNY": "CNY",
        "A$": "AUD",
        "AUD": "AUD",
        "C$": "CAD",
        "CAD": "CAD",
        "CHF": "CHF",
        "Fr": "CHF",
        "SAR": "SAR",
        "SR": "SAR",
        "KWD": "KWD",
        "QAR": "QAR",
        "OMR": "OMR",
        "BHD": "BHD",
    }
    
    def __init__(self, base_currency: str = "INR"):
        """
        Initialize converter
        
        Args:
            base_currency: Base currency for reporting (default: INR)
        """
        self.base_currency = base_currency
        self.logger = logger
        
        self.logger.info(f"Currency converter initialized with base: {base_currency}")
    
    def detect_currency(self, currency_string: str) -> str:
        """
        Detect currency from string
        
        Args:
            currency_string: Currency symbol or code (e.g., "$", "USD", "₹")
            
        Returns:
            Currency code (e.g., "USD", "INR")
        """
        if not currency_string:
            return "INR"  # Default to INR
        
        currency_string = currency_string.strip()
        
        # Direct lookup
        if currency_string in self.CURRENCY_SYMBOLS:
            return self.CURRENCY_SYMBOLS[currency_string]
        
        # Try uppercase
        currency_upper = currency_string.upper()
        if currency_upper in self.CURRENCY_SYMBOLS:
            return self.CURRENCY_SYMBOLS[currency_upper]
        
        # Check if it's already a valid currency code
        if currency_upper in self.EXCHANGE_RATES:
            return currency_upper
        
        # Default to INR if unknown
        self.logger.warning(f"Unknown currency: {currency_string}, defaulting to INR")
        return "INR"
    
    def convert_to_inr(self, amount: float, from_currency: str) -> float:
        """
        Convert amount from any currency to INR
        
        Args:
            amount: Amount in source currency
            from_currency: Source currency code or symbol
            
        Returns:
            Amount in INR
        """
        if not amount:
            return 0.0
        
        # Detect currency
        currency_code = self.detect_currency(from_currency)
        
        # Already in INR
        if currency_code == "INR":
            return float(amount)
        
        # Get exchange rate
        rate = self.EXCHANGE_RATES.get(currency_code)
        
        if not rate:
            self.logger.warning(f"No exchange rate for {currency_code}, using 1:1")
            return float(amount)
        
        # Convert
        inr_amount = float(amount) * rate
        
        self.logger.info(f"Converted {amount} {currency_code} to ₹{inr_amount:.2f} INR")
        
        return inr_amount
    
    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        Convert between any two currencies
        
        Args:
            amount: Amount in source currency
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Amount in target currency
        """
        # Convert to INR first
        inr_amount = self.convert_to_inr(amount, from_currency)
        
        # If target is INR, we're done
        if to_currency == "INR":
            return inr_amount
        
        # Convert from INR to target
        target_rate = self.EXCHANGE_RATES.get(to_currency, 1.0)
        target_amount = inr_amount / target_rate
        
        return target_amount
    
    def format_inr(self, amount: float) -> str:
        """
        Format amount as Indian Rupees with proper formatting
        
        Args:
            amount: Amount in INR
            
        Returns:
            Formatted string (e.g., "₹1,23,456.78")
        """
        if not amount:
            return "₹0.00"
        
        # Indian number formatting: 1,23,45,678.90
        amount_str = f"{amount:,.2f}"
        
        # Split into parts
        parts = amount_str.split(".")
        integer_part = parts[0].replace(",", "")
        decimal_part = parts[1] if len(parts) > 1 else "00"
        
        # Format with Indian grouping
        if len(integer_part) <= 3:
            formatted = integer_part
        else:
            # Last 3 digits
            last_three = integer_part[-3:]
            remaining = integer_part[:-3]
            
            # Group remaining in pairs from right
            groups = []
            while remaining:
                groups.insert(0, remaining[-2:])
                remaining = remaining[:-2]
            
            formatted = ",".join(groups) + "," + last_three
        
        return f"₹{formatted}.{decimal_part}"
    
    def get_currency_name(self, currency_code: str) -> str:
        """Get full currency name"""
        names = {
            "INR": "Indian Rupee",
            "USD": "US Dollar",
            "EUR": "Euro",
            "GBP": "British Pound",
            "AED": "UAE Dirham",
            "SGD": "Singapore Dollar",
            "JPY": "Japanese Yen",
            "CNY": "Chinese Yuan",
            "AUD": "Australian Dollar",
            "CAD": "Canadian Dollar",
            "CHF": "Swiss Franc",
            "SAR": "Saudi Riyal",
            "KWD": "Kuwaiti Dinar",
            "QAR": "Qatari Riyal",
            "OMR": "Omani Rial",
            "BHD": "Bahraini Dinar",
        }
        return names.get(currency_code, currency_code)
    
    def update_rates(self, rates: Dict[str, float]):
        """
        Update exchange rates
        
        Args:
            rates: Dictionary of currency codes to INR rates
        """
        self.EXCHANGE_RATES.update(rates)
        self.logger.info(f"Updated {len(rates)} exchange rates")
    
    def get_rate(self, currency_code: str) -> Optional[float]:
        """Get exchange rate for a currency"""
        return self.EXCHANGE_RATES.get(currency_code)


# Global converter instance
_converter_instance = None


def get_currency_converter() -> CurrencyConverter:
    """Get or create currency converter instance (singleton)"""
    global _converter_instance
    if _converter_instance is None:
        _converter_instance = CurrencyConverter()
    return _converter_instance