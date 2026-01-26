"""
Live Exchange Rate Fetcher
Fetches real exchange rates based on invoice date
Falls back to static rates if API unavailable
"""

import requests
from datetime import datetime, date, timedelta
from typing import Dict, Optional
from decimal import Decimal
import json
from pathlib import Path
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class LiveExchangeRateProvider:
    """
    Fetches live exchange rates from multiple sources
    
    Sources (in priority order):
    1. exchangerate-api.com (Free, 1500 requests/month)
    2. frankfurter.app (Free, no limits, European Central Bank data)
    3. Static fallback rates
    """
    
    # Static fallback rates (updated Dec 2025)
    FALLBACK_RATES = {
        "INR": 1.0,
        "USD": 83.50,
        "EUR": 91.20,
        "GBP": 106.50,
        "AED": 22.75,
        "SGD": 62.30,
        "JPY": 0.56,
        "CNY": 11.55,
        "AUD": 54.20,
        "CAD": 59.80,
        "CHF": 95.40,
        "SAR": 22.25,
        "KWD": 272.50,
        "QAR": 22.95,
        "OMR": 217.20,
        "BHD": 221.50,
    }
    
    def __init__(self, cache_dir: str = "./data/exchange_rates"):
        """
        Initialize exchange rate provider
        
        Args:
            cache_dir: Directory to cache exchange rates
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logger
        
        # Cache for rates (in-memory)
        self.rate_cache: Dict[str, Dict[str, float]] = {}
        
        self.logger.info("Live exchange rate provider initialized")
    
    def get_rate_for_date(self, 
                          currency: str, 
                          invoice_date: Optional[str] = None,
                          base_currency: str = "INR") -> float:
        """
        Get exchange rate for a specific date
        
        Args:
            currency: Currency code (USD, GBP, EUR, etc.) or Currency enum
            invoice_date: Invoice date (YYYY-MM-DD or ISO format)
            base_currency: Base currency (default: INR)
            
        Returns:
            Exchange rate (currency to base_currency)
        """
        
        # Convert Currency enum to string if needed
        if hasattr(currency, 'value'):
            # It's an enum like Currency.USD
            currency = str(currency.value)
        elif hasattr(currency, 'name'):
            # It's an enum, get the name
            currency = str(currency.name)
        else:
            # It's already a string
            currency = str(currency)
        
        # Remove any "Currency." prefix if present
        if currency.startswith("Currency."):
            currency = currency.replace("Currency.", "")
        
        self.logger.info(f"Normalized currency: {currency}")
        
        # Parse date
        if invoice_date:
            try:
                if isinstance(invoice_date, str):
                    # Try multiple date formats
                    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y"]:
                        try:
                            target_date = datetime.strptime(invoice_date, fmt).date()
                            break
                        except:
                            continue
                    else:
                        # Try ISO format
                        target_date = datetime.fromisoformat(invoice_date.replace('Z', '+00:00')).date()
                elif isinstance(invoice_date, date):
                    target_date = invoice_date
                else:
                    target_date = date.today()
            except:
                self.logger.warning(f"Could not parse date: {invoice_date}, using today")
                target_date = date.today()
        else:
            target_date = date.today()
        
        self.logger.info(f"Getting exchange rate for {currency} on {target_date}")
        
        # Check cache first
        cache_key = f"{currency}_{target_date.isoformat()}"
        if cache_key in self.rate_cache:
            rate = self.rate_cache[cache_key]
            self.logger.info(f"Using cached rate: 1 {currency} = ₹{rate:.4f}")
            return rate
        
        # Try to fetch live rate
        rate = None
        
        # Method 1: Frankfurter (Free, reliable)
        rate = self._fetch_from_frankfurter(currency, target_date)
        
        # Method 2: exchangerate-api.com (backup)
        if rate is None:
            rate = self._fetch_from_exchangerate_api(currency, target_date)
        
        # Method 3: Fallback to static rates
        if rate is None:
            rate = self.FALLBACK_RATES.get(currency)
            if rate:
                self.logger.warning(f"Using fallback rate for {currency}: ₹{rate:.4f}")
            else:
                self.logger.error(f"No rate found for {currency}, defaulting to 1.0")
                rate = 1.0
        
        # Cache the rate
        self.rate_cache[cache_key] = rate
        
        # Save to disk cache
        self._save_to_cache(currency, target_date, rate)
        
        return rate
    
    def _fetch_from_frankfurter(self, currency: str, target_date: date) -> Optional[float]:
        """
        Fetch rate from Frankfurter API (European Central Bank data)
        Free, no API key needed
        """
        try:
            # Frankfurter uses EUR as base, we need to convert to INR
            # Get EUR to target currency
            # Get EUR to INR
            
            # Check if date is too recent (API has 1-day delay)
            if target_date >= date.today():
                target_date = date.today() - timedelta(days=1)
            
            url = f"https://api.frankfurter.app/{target_date.isoformat()}"
            params = {
                "from": currency,
                "to": "INR"
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                rate = data.get("rates", {}).get("INR")
                
                if rate:
                    self.logger.info(f"✓ Frankfurter: 1 {currency} = ₹{rate:.4f} on {target_date}")
                    return float(rate)
            
            self.logger.warning(f"Frankfurter API failed: {response.status_code}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Frankfurter API error: {e}")
            return None
    
    def _fetch_from_exchangerate_api(self, currency: str, target_date: date) -> Optional[float]:
        """
        Fetch rate from exchangerate-api.com
        Free tier: 1500 requests/month
        """
        try:
            # This API requires historical dates to be within last 5 years
            # Format: YYYY-MM-DD
            
            # For free tier, use latest rates (no historical without API key)
            url = f"https://api.exchangerate-api.com/v4/latest/{currency}"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                rate = data.get("rates", {}).get("INR")
                
                if rate:
                    self.logger.info(f"✓ ExchangeRate-API: 1 {currency} = ₹{rate:.4f}")
                    return float(rate)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"ExchangeRate-API error: {e}")
            return None
    
    def _save_to_cache(self, currency: str, target_date: date, rate: float):
        """Save rate to disk cache"""
        try:
            cache_file = self.cache_dir / f"{currency}_{target_date.isoformat()}.json"
            
            cache_data = {
                "currency": currency,
                "date": target_date.isoformat(),
                "rate_to_inr": rate,
                "cached_at": datetime.now().isoformat()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
        except Exception as e:
            self.logger.warning(f"Failed to save cache: {e}")
    
    def _load_from_cache(self, currency: str, target_date: date) -> Optional[float]:
        """Load rate from disk cache"""
        try:
            cache_file = self.cache_dir / f"{currency}_{target_date.isoformat()}.json"
            
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
                rate = cache_data.get("rate_to_inr")
                if rate:
                    self.logger.info(f"Loaded from disk cache: 1 {currency} = ₹{rate:.4f}")
                    return float(rate)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to load cache: {e}")
            return None
    
    def get_latest_rate(self, currency: str) -> float:
        """Get latest rate (today's date)"""
        return self.get_rate_for_date(currency, date.today().isoformat())
    
    def convert(self, 
                amount: float, 
                from_currency: str, 
                invoice_date: Optional[str] = None) -> float:
        """
        Convert amount to INR using historical rate
        
        Args:
            amount: Amount in source currency
            from_currency: Source currency code or Currency enum
            invoice_date: Date of invoice (for historical rate)
            
        Returns:
            Amount in INR
        """
        
        # Convert Currency enum to string if needed
        if hasattr(from_currency, 'value'):
            from_currency = str(from_currency.value)
        elif hasattr(from_currency, 'name'):
            from_currency = str(from_currency.name)
        else:
            from_currency = str(from_currency)
        
        # Remove any "Currency." prefix
        if from_currency.startswith("Currency."):
            from_currency = from_currency.replace("Currency.", "")
        
        if from_currency == "INR":
            return float(amount)
        
        rate = self.get_rate_for_date(from_currency, invoice_date)
        inr_amount = float(amount) * rate
        
        self.logger.info(f"Converted: {amount} {from_currency} × {rate:.4f} = ₹{inr_amount:.2f}")
        
        return inr_amount


# Global instance
_rate_provider_instance = None


def get_rate_provider() -> LiveExchangeRateProvider:
    """Get or create rate provider instance (singleton)"""
    global _rate_provider_instance
    if _rate_provider_instance is None:
        _rate_provider_instance = LiveExchangeRateProvider()
    return _rate_provider_instance