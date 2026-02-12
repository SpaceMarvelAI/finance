"""
Validation Tools
Specialized tools for data validation and quality checks used by AutoGen agents
"""

from typing import Dict, Any, Optional, List, Union
import re
import json
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class ValidationTools:
    """
    Validation Tools
    
    Provides data validation and quality check capabilities for AutoGen agents.
    Includes format validation, range checks, and business rule validation.
    """
    
    def __init__(self):
        # Initialize validation tools
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize validation tools"""
        try:
            logger.info("Validation tools initialized")
        except Exception as e:
            logger.error(f"Error initializing validation tools: {str(e)}")
            raise
    
    def validate_data_format(self, data: Any, validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data format according to specified rules
        
        Args:
            data: Data to validate
            validation_rules: Validation rules to apply
            
        Returns:
            Validation results
        """
        try:
            validation_results = {}
            
            # Type validation
            if 'type' in validation_rules:
                expected_type = validation_rules['type']
                actual_type = type(data).__name__
                
                if self._validate_type(data, expected_type):
                    validation_results['type'] = {'status': 'pass', 'expected': expected_type, 'actual': actual_type}
                else:
                    validation_results['type'] = {
                        'status': 'fail', 
                        'message': f'Expected type {expected_type}, got {actual_type}',
                        'expected': expected_type, 
                        'actual': actual_type
                    }
            
            # Format validation (for strings)
            if isinstance(data, str) and 'format' in validation_rules:
                format_rules = validation_rules['format']
                
                if 'pattern' in format_rules:
                    pattern = format_rules['pattern']
                    if re.match(pattern, data):
                        validation_results['format'] = {'status': 'pass', 'pattern': pattern}
                    else:
                        validation_results['format'] = {
                            'status': 'fail',
                            'message': f'Data does not match pattern: {pattern}',
                            'pattern': pattern
                        }
                
                if 'min_length' in format_rules:
                    min_length = format_rules['min_length']
                    if len(data) >= min_length:
                        validation_results['min_length'] = {'status': 'pass', 'min_length': min_length}
                    else:
                        validation_results['min_length'] = {
                            'status': 'fail',
                            'message': f'Data length {len(data)} is less than minimum {min_length}',
                            'min_length': min_length
                        }
                
                if 'max_length' in format_rules:
                    max_length = format_rules['max_length']
                    if len(data) <= max_length:
                        validation_results['max_length'] = {'status': 'pass', 'max_length': max_length}
                    else:
                        validation_results['max_length'] = {
                            'status': 'fail',
                            'message': f'Data length {len(data)} exceeds maximum {max_length}',
                            'max_length': max_length
                        }
            
            # Range validation (for numbers)
            if isinstance(data, (int, float)) and 'range' in validation_rules:
                range_rules = validation_rules['range']
                min_val = range_rules.get('min')
                max_val = range_rules.get('max')
                
                if min_val is not None and data < min_val:
                    validation_results['range'] = {
                        'status': 'fail',
                        'message': f'Value {data} is less than minimum {min_val}',
                        'min': min_val,
                        'max': max_val
                    }
                elif max_val is not None and data > max_val:
                    validation_results['range'] = {
                        'status': 'fail',
                        'message': f'Value {data} exceeds maximum {max_val}',
                        'min': min_val,
                        'max': max_val
                    }
                else:
                    validation_results['range'] = {'status': 'pass', 'min': min_val, 'max': max_val}
            
            # Enum validation
            if 'enum' in validation_rules:
                enum_values = validation_rules['enum']
                if data in enum_values:
                    validation_results['enum'] = {'status': 'pass', 'allowed_values': enum_values}
                else:
                    validation_results['enum'] = {
                        'status': 'fail',
                        'message': f'Value {data} is not in allowed values: {enum_values}',
                        'allowed_values': enum_values
                    }
            
            # Required field validation
            if 'required' in validation_rules and validation_rules['required']:
                if data is not None and data != '':
                    validation_results['required'] = {'status': 'pass'}
                else:
                    validation_results['required'] = {
                        'status': 'fail',
                        'message': 'Field is required but value is null or empty'
                    }
            
            # Overall validation status
            all_passed = all(result['status'] == 'pass' for result in validation_results.values())
            
            logger.info(f"Validated data format: {'PASS' if all_passed else 'FAIL'}")
            
            return {
                'status': 'success',
                'data': data,
                'validation_rules': validation_rules,
                'validation_results': validation_results,
                'overall_status': 'pass' if all_passed else 'fail',
                'validation_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error validating data format: {str(e)}")
            return {
                'status': 'error',
                'data': data,
                'validation_rules': validation_rules,
                'error': str(e)
            }
    
    def validate_business_rules(self, data: Dict[str, Any], business_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate data against business rules
        
        Args:
            data: Data to validate
            business_rules: List of business rules to apply
            
        Returns:
            Validation results
        """
        try:
            validation_results = {}
            
            for i, rule in enumerate(business_rules):
                rule_name = rule.get('name', f'business_rule_{i}')
                rule_type = rule.get('type')
                rule_params = rule.get('params', {})
                
                try:
                    if rule_type == 'conditional':
                        # Conditional validation
                        condition = rule_params.get('condition', '')
                        message = rule_params.get('message', f'Condition failed: {condition}')
                        
                        if self._evaluate_condition(data, condition):
                            validation_results[rule_name] = {'status': 'pass', 'condition': condition}
                        else:
                            validation_results[rule_name] = {
                                'status': 'fail',
                                'message': message,
                                'condition': condition
                            }
                    
                    elif rule_type == 'cross_field':
                        # Cross-field validation
                        field1 = rule_params.get('field1')
                        field2 = rule_params.get('field2')
                        operator = rule_params.get('operator', '=')
                        
                        if field1 in data and field2 in data:
                            if self._compare_fields(data[field1], data[field2], operator):
                                validation_results[rule_name] = {
                                    'status': 'pass',
                                    'field1': field1,
                                    'field2': field2,
                                    'operator': operator
                                }
                            else:
                                validation_results[rule_name] = {
                                    'status': 'fail',
                                    'message': f'Cross-field validation failed: {field1} {operator} {field2}',
                                    'field1': field1,
                                    'field2': field2,
                                    'operator': operator
                                }
                    
                    elif rule_type == 'custom':
                        # Custom validation function
                        function_name = rule_params.get('function')
                        if function_name:
                            result = self._execute_custom_validation(data, function_name, rule_params)
                            validation_results[rule_name] = result
                    
                    else:
                        validation_results[rule_name] = {
                            'status': 'unknown',
                            'message': f'Unknown rule type: {rule_type}'
                        }
                
                except Exception as e:
                    validation_results[rule_name] = {
                        'status': 'error',
                        'message': str(e)
                    }
            
            # Overall validation status
            all_passed = all(result['status'] == 'pass' for result in validation_results.values())
            
            logger.info(f"Validated business rules: {'PASS' if all_passed else 'FAIL'}")
            
            return {
                'status': 'success',
                'data': data,
                'business_rules': business_rules,
                'validation_results': validation_results,
                'overall_status': 'pass' if all_passed else 'fail',
                'validation_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error validating business rules: {str(e)}")
            return {
                'status': 'error',
                'data': data,
                'business_rules': business_rules,
                'error': str(e)
            }
    
    def validate_data_quality(self, data: List[Dict[str, Any]], quality_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data quality metrics
        
        Args:
            data: List of data records to validate
            quality_rules: Quality rules to apply
            
        Returns:
            Quality validation results
        """
        try:
            quality_results = {}
            
            if not data:
                return {
                    'status': 'error',
                    'data': data,
                    'quality_rules': quality_rules,
                    'error': 'Empty data list'
                }
            
            # Completeness validation
            if 'completeness' in quality_rules:
                completeness_rules = quality_rules['completeness']
                required_fields = completeness_rules.get('required_fields', [])
                
                completeness_score = self._calculate_completeness_score(data, required_fields)
                quality_results['completeness'] = {
                    'score': completeness_score,
                    'required_fields': required_fields,
                    'status': 'pass' if completeness_score >= completeness_rules.get('threshold', 0.8) else 'fail'
                }
            
            # Uniqueness validation
            if 'uniqueness' in quality_rules:
                uniqueness_rules = quality_rules['uniqueness']
                unique_fields = uniqueness_rules.get('unique_fields', [])
                
                uniqueness_score = self._calculate_uniqueness_score(data, unique_fields)
                quality_results['uniqueness'] = {
                    'score': uniqueness_score,
                    'unique_fields': unique_fields,
                    'status': 'pass' if uniqueness_score >= uniqueness_rules.get('threshold', 0.95) else 'fail'
                }
            
            # Consistency validation
            if 'consistency' in quality_rules:
                consistency_rules = quality_rules['consistency']
                consistency_score = self._calculate_consistency_score(data, consistency_rules)
                quality_results['consistency'] = {
                    'score': consistency_score,
                    'status': 'pass' if consistency_score >= consistency_rules.get('threshold', 0.9) else 'fail'
                }
            
            # Accuracy validation
            if 'accuracy' in quality_rules:
                accuracy_rules = quality_rules['accuracy']
                accuracy_score = self._calculate_accuracy_score(data, accuracy_rules)
                quality_results['accuracy'] = {
                    'score': accuracy_score,
                    'status': 'pass' if accuracy_score >= accuracy_rules.get('threshold', 0.95) else 'fail'
                }
            
            # Overall quality score
            scores = [result['score'] for result in quality_results.values() if 'score' in result]
            overall_score = sum(scores) / len(scores) if scores else 0
            overall_status = 'pass' if overall_score >= quality_rules.get('overall_threshold', 0.85) else 'fail'
            
            logger.info(f"Validated data quality: Score={overall_score:.2f}, Status={overall_status}")
            
            return {
                'status': 'success',
                'data': data,
                'quality_rules': quality_rules,
                'quality_results': quality_results,
                'overall_score': overall_score,
                'overall_status': overall_status,
                'validation_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error validating data quality: {str(e)}")
            return {
                'status': 'error',
                'data': data,
                'quality_rules': quality_rules,
                'error': str(e)
            }
    
    def validate_json_schema(self, data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data against JSON schema
        
        Args:
            data: Data to validate
            schema: JSON schema to validate against
            
        Returns:
            Schema validation results
        """
        try:
            import jsonschema
            from jsonschema import validate
            
            # Validate data against schema
            validate(instance=data, schema=schema)
            
            logger.info("JSON schema validation: PASS")
            
            return {
                'status': 'success',
                'data': data,
                'schema': schema,
                'validation_results': {'schema_valid': True},
                'validation_time': self._get_current_timestamp()
            }
            
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"JSON schema validation failed: {str(e)}")
            return {
                'status': 'error',
                'data': data,
                'schema': schema,
                'error': str(e),
                'validation_results': {'schema_valid': False, 'error': str(e)}
            }
        except Exception as e:
            logger.error(f"Error validating JSON schema: {str(e)}")
            return {
                'status': 'error',
                'data': data,
                'schema': schema,
                'error': str(e)
            }
    
    def _validate_type(self, data: Any, expected_type: str) -> bool:
        """Validate data type"""
        type_mapping = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'array': list,
            'object': dict,
            'number': (int, float)
        }
        
        expected_python_type = type_mapping.get(expected_type.lower())
        if expected_python_type:
            return isinstance(data, expected_python_type)
        return False
    
    def _evaluate_condition(self, data: Dict[str, Any], condition: str) -> bool:
        """Evaluate conditional expression"""
        try:
            # Simple condition evaluation (in production, use a safer evaluation method)
            # This is a basic implementation - in production, use ast.literal_eval or similar
            if ' and ' in condition:
                parts = condition.split(' and ')
                return all(self._evaluate_condition(data, part.strip()) for part in parts)
            elif ' or ' in condition:
                parts = condition.split(' or ')
                return any(self._evaluate_condition(data, part.strip()) for part in parts)
            elif ' == ' in condition:
                field, value = condition.split(' == ')
                field = field.strip()
                value = value.strip().strip('"\'')
                return data.get(field) == value
            elif ' != ' in condition:
                field, value = condition.split(' != ')
                field = field.strip()
                value = value.strip().strip('"\'')
                return data.get(field) != value
            else:
                return False
        except:
            return False
    
    def _compare_fields(self, value1: Any, value2: Any, operator: str) -> bool:
        """Compare two field values"""
        try:
            if operator == '=':
                return value1 == value2
            elif operator == '!=':
                return value1 != value2
            elif operator == '>':
                return value1 > value2
            elif operator == '<':
                return value1 < value2
            elif operator == '>=':
                return value1 >= value2
            elif operator == '<=':
                return value1 <= value2
            else:
                return False
        except:
            return False
    
    def _execute_custom_validation(self, data: Dict[str, Any], function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom validation function"""
        try:
            # This would typically call a registered custom validation function
            # For now, return a placeholder result
            return {
                'status': 'pass',
                'function': function_name,
                'params': params
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'function': function_name,
                'params': params
            }
    
    def _calculate_completeness_score(self, data: List[Dict[str, Any]], required_fields: List[str]) -> float:
        """Calculate data completeness score"""
        if not data or not required_fields:
            return 1.0
        
        total_required = len(data) * len(required_fields)
        missing_count = 0
        
        for record in data:
            for field in required_fields:
                if field not in record or record[field] is None or record[field] == '':
                    missing_count += 1
        
        completeness = 1.0 - (missing_count / total_required)
        return max(0.0, min(1.0, completeness))
    
    def _calculate_uniqueness_score(self, data: List[Dict[str, Any]], unique_fields: List[str]) -> float:
        """Calculate data uniqueness score"""
        if not data or not unique_fields:
            return 1.0
        
        total_records = len(data)
        if total_records <= 1:
            return 1.0
        
        # Create unique keys based on specified fields
        unique_keys = set()
        for record in data:
            key_parts = [str(record.get(field, '')) for field in unique_fields]
            unique_keys.add('|'.join(key_parts))
        
        uniqueness = len(unique_keys) / total_records
        return uniqueness
    
    def _calculate_consistency_score(self, data: List[Dict[str, Any]], consistency_rules: Dict[str, Any]) -> float:
        """Calculate data consistency score"""
        if not data:
            return 1.0
        
        total_checks = 0
        passed_checks = 0
        
        # Check format consistency for specified fields
        if 'format_fields' in consistency_rules:
            format_fields = consistency_rules['format_fields']
            for field in format_fields:
                if field in consistency_rules['format_rules']:
                    pattern = consistency_rules['format_rules'][field]
                    for record in data:
                        if field in record and record[field]:
                            total_checks += 1
                            if re.match(pattern, str(record[field])):
                                passed_checks += 1
        
        # Check value consistency for specified fields
        if 'value_fields' in consistency_rules:
            value_fields = consistency_rules['value_fields']
            for field in value_fields:
                if field in consistency_rules['allowed_values']:
                    allowed_values = consistency_rules['allowed_values'][field]
                    for record in data:
                        if field in record and record[field]:
                            total_checks += 1
                            if record[field] in allowed_values:
                                passed_checks += 1
        
        consistency = passed_checks / total_checks if total_checks > 0 else 1.0
        return consistency
    
    def _calculate_accuracy_score(self, data: List[Dict[str, Any]], accuracy_rules: Dict[str, Any]) -> float:
        """Calculate data accuracy score"""
        if not data:
            return 1.0
        
        total_checks = 0
        passed_checks = 0
        
        # Check range accuracy for numeric fields
        if 'range_fields' in accuracy_rules:
            range_fields = accuracy_rules['range_fields']
            for field in range_fields:
                if field in accuracy_rules['range_rules']:
                    rules = accuracy_rules['range_rules'][field]
                    min_val = rules.get('min')
                    max_val = rules.get('max')
                    
                    for record in data:
                        if field in record and record[field] is not None:
                            total_checks += 1
                            value = record[field]
                            if (min_val is None or value >= min_val) and (max_val is None or value <= max_val):
                                passed_checks += 1
        
        # Check reference accuracy (foreign key validation)
        if 'reference_fields' in accuracy_rules:
            reference_fields = accuracy_rules['reference_fields']
            for field in reference_fields:
                if field in accuracy_rules['reference_rules']:
                    valid_values = accuracy_rules['reference_rules'][field]
                    for record in data:
                        if field in record and record[field]:
                            total_checks += 1
                            if record[field] in valid_values:
                                passed_checks += 1
        
        accuracy = passed_checks / total_checks if total_checks > 0 else 1.0
        return accuracy
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().isoformat()