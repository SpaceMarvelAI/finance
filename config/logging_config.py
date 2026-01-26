"""
Logging Configuration for Financial Automation System
Provides structured logging throughout the application
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


class LoggerSetup:
    """Configure application-wide logging"""
    
    @staticmethod
    def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
        """
        Set up a logger with both file and console handlers
        
        Args:
            name: Logger name (usually module name)
            level: Logging level
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # File handler
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"financial_automation_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance
    
    Usage:
        from shared.config.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Processing started")
    """
    return LoggerSetup.setup_logger(name)