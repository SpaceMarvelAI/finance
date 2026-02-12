"""
File Tools
Specialized tools for file operations used by AutoGen agents
"""

from typing import Dict, Any, Optional, List, Union
import os
import json
import csv
import pandas as pd
from pathlib import Path
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class FileTools:
    """
    File Tools
    
    Provides file operations for AutoGen agents including reading,
    writing, and processing various file formats.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or os.getcwd()
        
        # Initialize file tools
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize file tools"""
        try:
            # Ensure base path exists
            Path(self.base_path).mkdir(parents=True, exist_ok=True)
            
            logger.info(f"File tools initialized with base path: {self.base_path}")
            
        except Exception as e:
            logger.error(f"Error initializing file tools: {str(e)}")
            raise
    
    def read_file(self, file_path: str, file_format: Optional[str] = None) -> Dict[str, Any]:
        """
        Read a file from the filesystem
        
        Args:
            file_path: Path to the file
            file_format: Format of the file (auto-detected if not provided)
            
        Returns:
            File content
        """
        try:
            # Determine file format
            if not file_format:
                file_format = self._detect_file_format(file_path)
            
            # Read file based on format
            if file_format in ['json', 'jsonl']:
                content = self._read_json_file(file_path)
            elif file_format in ['csv', 'tsv']:
                content = self._read_csv_file(file_path, file_format)
            elif file_format in ['xlsx', 'xls']:
                content = self._read_excel_file(file_path)
            elif file_format in ['txt', 'log']:
                content = self._read_text_file(file_path)
            else:
                content = self._read_binary_file(file_path)
            
            logger.info(f"Read file: {file_path}")
            
            return {
                'status': 'success',
                'file_path': file_path,
                'file_format': file_format,
                'content': content,
                'file_size': self._get_file_size(file_path),
                'read_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return {
                'status': 'error',
                'file_path': file_path,
                'file_format': file_format,
                'error': str(e)
            }
    
    def write_file(self, file_path: str, content: Any, 
                  file_format: Optional[str] = None) -> Dict[str, Any]:
        """
        Write content to a file
        
        Args:
            file_path: Path to the file
            content: Content to write
            file_format: Format of the file (auto-detected if not provided)
            
        Returns:
            Write operation result
        """
        try:
            # Determine file format
            if not file_format:
                file_format = self._detect_file_format(file_path)
            
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write file based on format
            if file_format in ['json', 'jsonl']:
                self._write_json_file(file_path, content, file_format)
            elif file_format in ['csv', 'tsv']:
                self._write_csv_file(file_path, content, file_format)
            elif file_format in ['xlsx', 'xls']:
                self._write_excel_file(file_path, content)
            elif file_format in ['txt', 'log']:
                self._write_text_file(file_path, content)
            else:
                self._write_binary_file(file_path, content)
            
            logger.info(f"Wrote file: {file_path}")
            
            return {
                'status': 'success',
                'file_path': file_path,
                'file_format': file_format,
                'content_type': type(content).__name__,
                'file_size': self._get_file_size(file_path),
                'write_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {str(e)}")
            return {
                'status': 'error',
                'file_path': file_path,
                'file_format': file_format,
                'error': str(e)
            }
    
    def list_files(self, directory: str, pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        List files in a directory
        
        Args:
            directory: Directory to list files from
            pattern: File pattern to match (e.g., "*.csv")
            
        Returns:
            List of files
        """
        try:
            # Ensure directory exists
            if not os.path.exists(directory):
                return {
                    'status': 'error',
                    'directory': directory,
                    'error': 'Directory does not exist'
                }
            
            # List files
            files = []
            for file_path in Path(directory).rglob(pattern or '*'):
                if file_path.is_file():
                    files.append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime
                    })
            
            logger.info(f"Listed {len(files)} files in {directory}")
            
            return {
                'status': 'success',
                'directory': directory,
                'pattern': pattern,
                'files': files,
                'file_count': len(files),
                'list_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {str(e)}")
            return {
                'status': 'error',
                'directory': directory,
                'pattern': pattern,
                'error': str(e)
            }
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete a file
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            Delete operation result
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {
                    'status': 'error',
                    'file_path': file_path,
                    'error': 'File does not exist'
                }
            
            # Delete file
            os.remove(file_path)
            
            logger.info(f"Deleted file: {file_path}")
            
            return {
                'status': 'success',
                'file_path': file_path,
                'delete_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return {
                'status': 'error',
                'file_path': file_path,
                'error': str(e)
            }
    
    def validate_file(self, file_path: str, validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a file against specified rules
        
        Args:
            file_path: Path to the file to validate
            validation_rules: Validation rules to apply
            
        Returns:
            Validation results
        """
        try:
            # Read file content
            file_result = self.read_file(file_path)
            
            if file_result['status'] != 'success':
                return file_result
            
            content = file_result['content']
            
            # Apply validation rules
            validation_results = {}
            
            # File size validation
            if 'max_size' in validation_rules:
                max_size = validation_rules['max_size']
                if file_result['file_size'] > max_size:
                    validation_results['file_size'] = {
                        'status': 'fail',
                        'message': f'File size {file_result["file_size"]} exceeds maximum {max_size}'
                    }
                else:
                    validation_results['file_size'] = {'status': 'pass'}
            
            # Content validation
            if 'required_fields' in validation_rules:
                required_fields = validation_rules['required_fields']
                missing_fields = []
                
                if isinstance(content, dict):
                    for field in required_fields:
                        if field not in content:
                            missing_fields.append(field)
                
                if missing_fields:
                    validation_results['required_fields'] = {
                        'status': 'fail',
                        'missing_fields': missing_fields
                    }
                else:
                    validation_results['required_fields'] = {'status': 'pass'}
            
            # Format validation
            if 'format' in validation_rules:
                expected_format = validation_rules['format']
                actual_format = file_result['file_format']
                
                if actual_format != expected_format:
                    validation_results['format'] = {
                        'status': 'fail',
                        'message': f'Expected format {expected_format}, got {actual_format}'
                    }
                else:
                    validation_results['format'] = {'status': 'pass'}
            
            # Custom validation
            if 'custom_rules' in validation_rules:
                custom_results = self._apply_custom_validation(content, validation_rules['custom_rules'])
                validation_results.update(custom_results)
            
            # Overall validation status
            all_passed = all(result['status'] == 'pass' for result in validation_results.values())
            
            logger.info(f"Validated file {file_path}: {'PASS' if all_passed else 'FAIL'}")
            
            return {
                'status': 'success',
                'file_path': file_path,
                'validation_results': validation_results,
                'overall_status': 'pass' if all_passed else 'fail',
                'validation_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error validating file {file_path}: {str(e)}")
            return {
                'status': 'error',
                'file_path': file_path,
                'validation_rules': validation_rules,
                'error': str(e)
            }
    
    def _detect_file_format(self, file_path: str) -> str:
        """Detect file format from extension"""
        try:
            extension = Path(file_path).suffix.lower().lstrip('.')
            
            # Map extensions to formats
            format_mapping = {
                'json': 'json',
                'jsonl': 'jsonl',
                'csv': 'csv',
                'tsv': 'tsv',
                'xlsx': 'xlsx',
                'xls': 'xls',
                'txt': 'txt',
                'log': 'log',
                'pdf': 'pdf',
                'png': 'png',
                'jpg': 'jpg',
                'jpeg': 'jpeg',
                'gif': 'gif'
            }
            
            return format_mapping.get(extension, 'unknown')
            
        except Exception as e:
            logger.error(f"Error detecting file format for {file_path}: {str(e)}")
            return 'unknown'
    
    def _read_json_file(self, file_path: str) -> Any:
        """Read JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.jsonl'):
                    return [json.loads(line) for line in f]
                else:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {str(e)}")
            raise
    
    def _read_csv_file(self, file_path: str, file_format: str) -> Any:
        """Read CSV file"""
        try:
            delimiter = '\t' if file_format == 'tsv' else ','
            return pd.read_csv(file_path, delimiter=delimiter).to_dict('records')
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {str(e)}")
            raise
    
    def _read_excel_file(self, file_path: str) -> Any:
        """Read Excel file"""
        try:
            return pd.read_excel(file_path).to_dict('records')
        except Exception as e:
            logger.error(f"Error reading Excel file {file_path}: {str(e)}")
            raise
    
    def _read_text_file(self, file_path: str) -> Any:
        """Read text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {str(e)}")
            raise
    
    def _read_binary_file(self, file_path: str) -> Any:
        """Read binary file"""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading binary file {file_path}: {str(e)}")
            raise
    
    def _write_json_file(self, file_path: str, content: Any, file_format: str):
        """Write JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_format == 'jsonl':
                    for item in content:
                        json.dump(item, f)
                        f.write('\n')
                else:
                    json.dump(content, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing JSON file {file_path}: {str(e)}")
            raise
    
    def _write_csv_file(self, file_path: str, content: Any, file_format: str):
        """Write CSV file"""
        try:
            delimiter = '\t' if file_format == 'tsv' else ','
            if isinstance(content, list) and content:
                df = pd.DataFrame(content)
                df.to_csv(file_path, index=False, sep=delimiter)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('')
        except Exception as e:
            logger.error(f"Error writing CSV file {file_path}: {str(e)}")
            raise
    
    def _write_excel_file(self, file_path: str, content: Any):
        """Write Excel file"""
        try:
            if isinstance(content, list) and content:
                df = pd.DataFrame(content)
                df.to_excel(file_path, index=False)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('')
        except Exception as e:
            logger.error(f"Error writing Excel file {file_path}: {str(e)}")
            raise
    
    def _write_text_file(self, file_path: str, content: Any):
        """Write text file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(content))
        except Exception as e:
            logger.error(f"Error writing text file {file_path}: {str(e)}")
            raise
    
    def _write_binary_file(self, file_path: str, content: Any):
        """Write binary file"""
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Error writing binary file {file_path}: {str(e)}")
            raise
    
    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Error getting file size for {file_path}: {str(e)}")
            return 0
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def _apply_custom_validation(self, content: Any, custom_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply custom validation rules"""
        results = {}
        
        for i, rule in enumerate(custom_rules):
            rule_name = rule.get('name', f'custom_rule_{i}')
            rule_type = rule.get('type')
            rule_params = rule.get('params', {})
            
            try:
                if rule_type == 'function':
                    # Apply custom function
                    func = rule_params.get('function')
                    if callable(func):
                        result = func(content, **rule_params)
                        results[rule_name] = {
                            'status': 'pass' if result else 'fail',
                            'message': rule_params.get('message', '')
                        }
                elif rule_type == 'regex':
                    # Apply regex pattern
                    import re
                    pattern = rule_params.get('pattern', '')
                    if re.search(pattern, str(content)):
                        results[rule_name] = {'status': 'pass'}
                    else:
                        results[rule_name] = {
                            'status': 'fail',
                            'message': f'Content does not match pattern: {pattern}'
                        }
                elif rule_type == 'range':
                    # Apply range check
                    min_val = rule_params.get('min')
                    max_val = rule_params.get('max')
                    if min_val <= len(str(content)) <= max_val:
                        results[rule_name] = {'status': 'pass'}
                    else:
                        results[rule_name] = {
                            'status': 'fail',
                            'message': f'Content length {len(str(content))} not in range [{min_val}, {max_val}]'
                        }
                else:
                    results[rule_name] = {
                        'status': 'unknown',
                        'message': f'Unknown rule type: {rule_type}'
                    }
            except Exception as e:
                results[rule_name] = {
                    'status': 'error',
                    'message': str(e)
                }
        
        return results