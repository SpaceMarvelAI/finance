"""
CSV Parser - Dedicated Parser for CSV Files
Docling doesn't handle CSV well, so we use pandas for CSV processing
"""

import pandas as pd
from typing import Dict, Any, List
from pathlib import Path
import csv


class CSVParser:
    """
    Dedicated CSV Parser using pandas
    
    Features:
    - Auto-detect delimiters (comma, semicolon, tab, pipe)
    - Auto-detect encoding (UTF-8, ISO-8859-1, Windows-1252)
    - Header detection
    - Data type inference
    - Validation and quality checks
    """
    
    COMMON_DELIMITERS = [',', ';', '\t', '|']
    COMMON_ENCODINGS = ['utf-8', 'iso-8859-1', 'windows-1252', 'latin1']
    
    def __init__(self):
        """Initialize CSV parser"""
        pass
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is CSV"""
        ext = Path(file_path).suffix.lower()
        return ext in ['.csv', '.tsv', '.txt']
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse CSV file with auto-detection
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Dictionary with:
                - text: Markdown representation
                - raw_dict: Structured data
                - metadata: File metadata
                - dataframe: pandas DataFrame
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Step 1: Auto-detect encoding and delimiter
            encoding = self._detect_encoding(file_path)
            delimiter = self._detect_delimiter(file_path, encoding)
            
            # Step 2: Read CSV with pandas
            df = pd.read_csv(
                file_path,
                delimiter=delimiter,
                encoding=encoding,
                skipinitialspace=True,
                on_bad_lines='skip'  # Skip malformed lines
            )
            
            # Step 3: Clean and validate
            df = self._clean_dataframe(df)
            
            # Step 4: Extract metadata
            metadata = self._extract_metadata(df, file_path)
            
            # Step 5: Convert to different formats
            text = self._to_markdown(df)
            raw_dict = self._to_dict(df)
            
            return {
                "text": text,
                "raw_dict": raw_dict,
                "metadata": metadata,
                "format": ".csv",
                "dataframe": df,  # Include pandas DataFrame for advanced operations
                "encoding": encoding,
                "delimiter": delimiter
            }
            
        except Exception as e:
            raise
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Auto-detect file encoding"""
        # Try each encoding
        for encoding in self.COMMON_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # Try to read first 1KB
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Fallback to utf-8
        return 'utf-8'
    
    def _detect_delimiter(self, file_path: Path, encoding: str) -> str:
        """Auto-detect CSV delimiter"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Read first few lines
                sample = f.read(4096)
            
            # Use csv.Sniffer to detect delimiter
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=''.join(self.COMMON_DELIMITERS))
            
            return dialect.delimiter
            
        except Exception as e:
            return ','
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize DataFrame"""
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Remove completely empty columns
        df = df.dropna(axis=1, how='all')
        
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip() if df[col].dtype == 'object' else df[col]
        
        # Clean column names
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.replace(r'\s+', '_', regex=True)
        df.columns = df.columns.str.lower()
        
        return df
    
    def _extract_metadata(self, df: pd.DataFrame, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from DataFrame"""
        return {
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "has_tables": True,  # CSV is essentially a table
            "table_count": 1,
            "format": ".csv",
            "parser": "pandas",
            "file_size_bytes": file_path.stat().st_size,
            "null_counts": df.isnull().sum().to_dict(),
            "sample_values": {
                col: df[col].dropna().head(3).tolist()
                for col in df.columns
            }
        }
    
    def _to_markdown(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to Markdown table"""
        # Limit to first 100 rows for markdown (avoid huge strings)
        if len(df) > 100:
            df_preview = df.head(100)
            markdown = df_preview.to_markdown(index=False)
            markdown += f"\n\n... ({len(df) - 100} more rows)"
        else:
            markdown = df.to_markdown(index=False)
        
        return markdown
    
    def _to_dict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Convert DataFrame to structured dictionary"""
        return {
            "columns": list(df.columns),
            "rows": df.to_dict('records'),
            "num_rows": len(df),
            "num_columns": len(df.columns)
        }
    
    def validate(self, file_path: str) -> Dict[str, Any]:
        """Validate CSV file quality"""
        errors = []
        warnings = []
        quality_scores = {}
        
        try:
            parsed = self.parse(file_path)
            df = parsed['dataframe']
            metadata = parsed['metadata']
            
            # Check 1: Minimum rows
            if len(df) < 2:
                errors.append("CSV has fewer than 2 rows (need header + data)")
            
            # Check 2: Empty columns
            empty_cols = [col for col, count in metadata['null_counts'].items() if count == len(df)]
            if empty_cols:
                warnings.append(f"Empty columns found: {', '.join(empty_cols)}")
            
            # Check 3: High null percentage
            for col, null_count in metadata['null_counts'].items():
                null_pct = (null_count / len(df)) * 100
                if null_pct > 50:
                    warnings.append(f"Column '{col}' has {null_pct:.1f}% null values")
            
            # Check 4: Duplicate rows
            dup_count = df.duplicated().sum()
            if dup_count > 0:
                dup_pct = (dup_count / len(df)) * 100
                warnings.append(f"Found {dup_count} duplicate rows ({dup_pct:.1f}%)")
            
            # Check 5: Column name quality
            if any(col.startswith('unnamed') or col.startswith('column') for col in df.columns):
                warnings.append("Some columns have auto-generated names (missing headers?)")
            
            # Calculate quality scores
            quality_scores = {
                "completeness": round((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 2),
                "uniqueness": round((1 - dup_count / len(df)) * 100, 2) if len(df) > 0 else 100,
                "consistency": 100.0  # Placeholder for future checks
            }
            
            # Overall quality
            overall_quality = sum(quality_scores.values()) / len(quality_scores)
            quality_scores['overall'] = round(overall_quality, 2)
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "quality_scores": quality_scores,
                "metadata": metadata
            }
            
        except Exception as e:
            errors.append(f"Failed to validate CSV: {str(e)}")
            return {
                "is_valid": False,
                "errors": errors,
                "warnings": warnings,
                "quality_scores": {}
            }
    
    def detect_financial_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Detect likely financial columns in CSV"""
        detected = {
            "invoice_number": [],
            "date": [],
            "vendor_customer": [],
            "amount": [],
            "tax": [],
            "status": []
        }
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Invoice number patterns
            if any(x in col_lower for x in ['invoice', 'inv_no', 'inv_num', 'bill_no']):
                detected['invoice_number'].append(col)
            
            # Date patterns
            elif any(x in col_lower for x in ['date', 'dt', 'dated']):
                detected['date'].append(col)
            
            # Vendor/Customer patterns
            elif any(x in col_lower for x in ['vendor', 'customer', 'supplier', 'party', 'name']):
                detected['vendor_customer'].append(col)
            
            # Amount patterns
            elif any(x in col_lower for x in ['amount', 'total', 'grand', 'value', 'price', 'sum']):
                detected['amount'].append(col)
            
            # Tax patterns
            elif any(x in col_lower for x in ['tax', 'gst', 'vat', 'cgst', 'sgst', 'igst']):
                detected['tax'].append(col)
            
            # Status patterns
            elif any(x in col_lower for x in ['status', 'state', 'paid', 'pending', 'overdue']):
                detected['status'].append(col)
        
        return detected