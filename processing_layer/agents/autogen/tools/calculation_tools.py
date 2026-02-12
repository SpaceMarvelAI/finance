"""
Calculation Tools
Specialized tools for mathematical and financial calculations used by AutoGen agents
"""

from typing import Dict, Any, Optional, List, Union
import math
import statistics
import pandas as pd
import numpy as np
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class CalculationTools:
    """
    Calculation Tools
    
    Provides mathematical and financial calculation capabilities for AutoGen agents.
    Includes statistical analysis, financial ratios, and complex mathematical operations.
    """
    
    def __init__(self):
        # Initialize calculation tools
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize calculation tools"""
        try:
            logger.info("Calculation tools initialized")
        except Exception as e:
            logger.error(f"Error initializing calculation tools: {str(e)}")
            raise
    
    def calculate_financial_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate financial ratios from financial data
        
        Args:
            financial_data: Dictionary containing financial data
            
        Returns:
            Calculated financial ratios
        """
        try:
            ratios = {}
            
            # Liquidity ratios
            if 'current_assets' in financial_data and 'current_liabilities' in financial_data:
                current_assets = financial_data['current_assets']
                current_liabilities = financial_data['current_liabilities']
                
                ratios['current_ratio'] = current_assets / current_liabilities if current_liabilities != 0 else 0
                ratios['quick_ratio'] = (current_assets - financial_data.get('inventory', 0)) / current_liabilities if current_liabilities != 0 else 0
            
            # Profitability ratios
            if 'net_income' in financial_data and 'revenue' in financial_data:
                net_income = financial_data['net_income']
                revenue = financial_data['revenue']
                
                ratios['profit_margin'] = net_income / revenue if revenue != 0 else 0
                ratios['return_on_assets'] = net_income / financial_data.get('total_assets', 1) if financial_data.get('total_assets', 1) != 0 else 0
            
            # Efficiency ratios
            if 'revenue' in financial_data and 'total_assets' in financial_data:
                ratios['asset_turnover'] = financial_data['revenue'] / financial_data['total_assets'] if financial_data['total_assets'] != 0 else 0
            
            # Leverage ratios
            if 'total_debt' in financial_data and 'total_equity' in financial_data:
                ratios['debt_to_equity'] = financial_data['total_debt'] / financial_data['total_equity'] if financial_data['total_equity'] != 0 else 0
            
            logger.info(f"Calculated {len(ratios)} financial ratios")
            
            return {
                'status': 'success',
                'financial_data': financial_data,
                'ratios': ratios,
                'calculation_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error calculating financial ratios: {str(e)}")
            return {
                'status': 'error',
                'financial_data': financial_data,
                'error': str(e)
            }
    
    def perform_statistical_analysis(self, data: List[Union[int, float]]) -> Dict[str, Any]:
        """
        Perform statistical analysis on numerical data
        
        Args:
            data: List of numerical data
            
        Returns:
            Statistical analysis results
        """
        try:
            if not data:
                return {
                    'status': 'error',
                    'data': data,
                    'error': 'Empty data list'
                }
            
            # Basic statistics
            mean_val = statistics.mean(data)
            median_val = statistics.median(data)
            std_dev = statistics.stdev(data) if len(data) > 1 else 0
            variance = statistics.variance(data) if len(data) > 1 else 0
            
            # Additional statistics
            minimum = min(data)
            maximum = max(data)
            range_val = maximum - minimum
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            
            # Skewness and kurtosis
            skewness = self._calculate_skewness(data)
            kurtosis = self._calculate_kurtosis(data)
            
            stats = {
                'count': len(data),
                'mean': mean_val,
                'median': median_val,
                'mode': statistics.mode(data) if len(set(data)) < len(data) else None,
                'std_dev': std_dev,
                'variance': variance,
                'minimum': minimum,
                'maximum': maximum,
                'range': range_val,
                'quartile_1': q1,
                'quartile_3': q3,
                'interquartile_range': iqr,
                'skewness': skewness,
                'kurtosis': kurtosis
            }
            
            logger.info(f"Performed statistical analysis on {len(data)} data points")
            
            return {
                'status': 'success',
                'data': data,
                'statistics': stats,
                'analysis_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error performing statistical analysis: {str(e)}")
            return {
                'status': 'error',
                'data': data,
                'error': str(e)
            }
    
    def calculate_aggregations(self, data: List[Dict[str, Any]], 
                              aggregations: Dict[str, str],
                              group_by: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calculate aggregations on structured data
        
        Args:
            data: List of dictionaries containing data
            aggregations: Dictionary of column aggregations
            group_by: Columns to group by
            
        Returns:
            Aggregation results
        """
        try:
            if not data:
                return {
                    'status': 'error',
                    'data': data,
                    'aggregations': aggregations,
                    'error': 'Empty data list'
                }
            
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(data)
            
            if group_by:
                # Group by specified columns
                grouped = df.groupby(group_by)
                results = {}
                
                for column, function in aggregations.items():
                    if column in df.columns:
                        if function.upper() == 'SUM':
                            results[column] = grouped[column].sum().to_dict()
                        elif function.upper() == 'COUNT':
                            results[column] = grouped[column].count().to_dict()
                        elif function.upper() == 'MEAN':
                            results[column] = grouped[column].mean().to_dict()
                        elif function.upper() == 'MAX':
                            results[column] = grouped[column].max().to_dict()
                        elif function.upper() == 'MIN':
                            results[column] = grouped[column].min().to_dict()
                        elif function.upper() == 'STD':
                            results[column] = grouped[column].std().to_dict()
                        else:
                            results[column] = {group: 'Unknown function' for group in grouped.groups.keys()}
            else:
                # No grouping, aggregate entire dataset
                results = {}
                
                for column, function in aggregations.items():
                    if column in df.columns:
                        if function.upper() == 'SUM':
                            results[column] = df[column].sum()
                        elif function.upper() == 'COUNT':
                            results[column] = df[column].count()
                        elif function.upper() == 'MEAN':
                            results[column] = df[column].mean()
                        elif function.upper() == 'MAX':
                            results[column] = df[column].max()
                        elif function.upper() == 'MIN':
                            results[column] = df[column].min()
                        elif function.upper() == 'STD':
                            results[column] = df[column].std()
                        else:
                            results[column] = f'Unknown function: {function}'
            
            logger.info(f"Calculated {len(aggregations)} aggregations")
            
            return {
                'status': 'success',
                'data': data,
                'aggregations': aggregations,
                'group_by': group_by,
                'results': results,
                'aggregation_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error calculating aggregations: {str(e)}")
            return {
                'status': 'error',
                'data': data,
                'aggregations': aggregations,
                'group_by': group_by,
                'error': str(e)
            }
    
    def calculate_trends(self, time_series_data: List[Dict[str, Any]], 
                        date_column: str, value_column: str) -> Dict[str, Any]:
        """
        Calculate trends in time series data
        
        Args:
            time_series_data: List of dictionaries with time series data
            date_column: Name of the date column
            value_column: Name of the value column
            
        Returns:
            Trend analysis results
        """
        try:
            if not time_series_data:
                return {
                    'status': 'error',
                    'time_series_data': time_series_data,
                    'error': 'Empty data list'
                }
            
            # Convert to DataFrame and sort by date
            df = pd.DataFrame(time_series_data)
            df[date_column] = pd.to_datetime(df[date_column])
            df = df.sort_values(date_column)
            
            values = df[value_column].tolist()
            dates = df[date_column].tolist()
            
            # Calculate basic trend metrics
            start_value = values[0]
            end_value = values[-1]
            total_change = end_value - start_value
            percent_change = (total_change / start_value) * 100 if start_value != 0 else 0
            
            # Calculate moving averages
            moving_avg_7 = df[value_column].rolling(window=min(7, len(values))).mean().tolist()
            moving_avg_30 = df[value_column].rolling(window=min(30, len(values))).mean().tolist()
            
            # Calculate trend direction
            trend_direction = 'up' if total_change > 0 else 'down' if total_change < 0 else 'flat'
            
            # Calculate volatility (standard deviation of daily changes)
            if len(values) > 1:
                daily_changes = [values[i] - values[i-1] for i in range(1, len(values))]
                volatility = statistics.stdev(daily_changes) if len(daily_changes) > 1 else 0
            else:
                volatility = 0
            
            trends = {
                'start_value': start_value,
                'end_value': end_value,
                'total_change': total_change,
                'percent_change': percent_change,
                'trend_direction': trend_direction,
                'volatility': volatility,
                'moving_average_7': moving_avg_7[-1] if moving_avg_7 else None,
                'moving_average_30': moving_avg_30[-1] if moving_avg_30 else None,
                'data_points': len(values)
            }
            
            logger.info(f"Calculated trends for {len(values)} data points")
            
            return {
                'status': 'success',
                'time_series_data': time_series_data,
                'date_column': date_column,
                'value_column': value_column,
                'trends': trends,
                'trend_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error calculating trends: {str(e)}")
            return {
                'status': 'error',
                'time_series_data': time_series_data,
                'date_column': date_column,
                'value_column': value_column,
                'error': str(e)
            }
    
    def calculate_compound_interest(self, principal: float, rate: float, 
                                   time: float, compounds_per_year: int = 1) -> Dict[str, Any]:
        """
        Calculate compound interest
        
        Args:
            principal: Initial principal amount
            rate: Annual interest rate (as decimal)
            time: Time period in years
            compounds_per_year: Number of times interest is compounded per year
            
        Returns:
            Compound interest calculation results
        """
        try:
            # Compound interest formula: A = P(1 + r/n)^(nt)
            amount = principal * (1 + rate / compounds_per_year) ** (compounds_per_year * time)
            interest = amount - principal
            
            results = {
                'principal': principal,
                'rate': rate,
                'time': time,
                'compounds_per_year': compounds_per_year,
                'final_amount': amount,
                'total_interest': interest,
                'effective_rate': (amount / principal) ** (1 / time) - 1 if time > 0 else 0
            }
            
            logger.info(f"Calculated compound interest: {amount}")
            
            return {
                'status': 'success',
                'calculation_type': 'compound_interest',
                'results': results,
                'calculation_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error calculating compound interest: {str(e)}")
            return {
                'status': 'error',
                'principal': principal,
                'rate': rate,
                'time': time,
                'compounds_per_year': compounds_per_year,
                'error': str(e)
            }
    
    def calculate_depreciation(self, cost: float, salvage_value: float, 
                              useful_life: int, method: str = 'straight_line') -> Dict[str, Any]:
        """
        Calculate asset depreciation
        
        Args:
            cost: Initial cost of the asset
            salvage_value: Estimated salvage value
            useful_life: Useful life in years
            method: Depreciation method ('straight_line', 'declining_balance', 'sum_of_years')
            
        Returns:
            Depreciation calculation results
        """
        try:
            results = {
                'cost': cost,
                'salvage_value': salvage_value,
                'useful_life': useful_life,
                'method': method,
                'depreciation_schedule': []
            }
            
            if method == 'straight_line':
                annual_depreciation = (cost - salvage_value) / useful_life
                for year in range(1, useful_life + 1):
                    results['depreciation_schedule'].append({
                        'year': year,
                        'depreciation': annual_depreciation,
                        'book_value': cost - (annual_depreciation * year)
                    })
            
            elif method == 'declining_balance':
                rate = 2 / useful_life  # Double declining balance
                book_value = cost
                for year in range(1, useful_life + 1):
                    depreciation = book_value * rate
                    # Don't depreciate below salvage value
                    if book_value - depreciation < salvage_value:
                        depreciation = book_value - salvage_value
                    book_value -= depreciation
                    results['depreciation_schedule'].append({
                        'year': year,
                        'depreciation': depreciation,
                        'book_value': book_value
                    })
            
            elif method == 'sum_of_years':
                sum_years = sum(range(1, useful_life + 1))
                remaining_life = useful_life
                book_value = cost
                for year in range(1, useful_life + 1):
                    depreciation = (remaining_life / sum_years) * (cost - salvage_value)
                    book_value -= depreciation
                    results['depreciation_schedule'].append({
                        'year': year,
                        'depreciation': depreciation,
                        'book_value': book_value
                    })
                    remaining_life -= 1
            
            logger.info(f"Calculated depreciation using {method} method")
            
            return {
                'status': 'success',
                'calculation_type': 'depreciation',
                'results': results,
                'calculation_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error calculating depreciation: {str(e)}")
            return {
                'status': 'error',
                'cost': cost,
                'salvage_value': salvage_value,
                'useful_life': useful_life,
                'method': method,
                'error': str(e)
            }
    
    def _calculate_skewness(self, data: List[Union[int, float]]) -> float:
        """Calculate skewness of data"""
        try:
            mean_val = statistics.mean(data)
            std_dev = statistics.stdev(data) if len(data) > 1 else 1
            n = len(data)
            
            if std_dev == 0:
                return 0
            
            skewness = sum(((x - mean_val) / std_dev) ** 3 for x in data) * (n / ((n - 1) * (n - 2)))
            return skewness
        except:
            return 0
    
    def _calculate_kurtosis(self, data: List[Union[int, float]]) -> float:
        """Calculate kurtosis of data"""
        try:
            mean_val = statistics.mean(data)
            std_dev = statistics.stdev(data) if len(data) > 1 else 1
            n = len(data)
            
            if std_dev == 0:
                return 0
            
            kurtosis = sum(((x - mean_val) / std_dev) ** 4 for x in data) * (n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))
            kurtosis -= (3 * (n - 1) ** 2) / ((n - 2) * (n - 3))
            return kurtosis
        except:
            return 0
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().isoformat()