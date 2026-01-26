"""
Aggregation Nodes - FIXED
Handles grouping, filtering, sorting, and summarization
"""

from typing import Dict, Any, List
from processing_layer.workflows.nodes.base_node import BaseNode, register_node


@register_node
class GroupingNode(BaseNode):
    """
    Grouping Node
    Groups data by specified field with subtotals
    """
    
    name = "Grouping"
    category = "aggregation"
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "description": "Groups records by specified field and calculates subtotals",
            "category": self.category,
            "input_schema": {
                "invoices": {"type": "array", "required": True},
                "group_by": {"type": "string", "description": "Field to group by"}
            },
            "output_schema": {
                "groups": {
                    "type": "array",
                    "description": "Array of groups with records and subtotals"
                }
            }
        }
    
    def run(self, input_data, params=None):
        """
        Group data by field
        
        Args:
            input_data: List of records or dict with 'invoices' key
            params: {group_by: field_name}
        """
        params = params or {}
        
        # Handle different input formats
        if isinstance(input_data, dict):
            records = input_data.get('invoices', [])
        elif isinstance(input_data, list):
            records = input_data
        else:
            return {'groups': [], 'total_records': 0}
        
        if not records:
            return {'groups': [], 'total_records': 0}
        
        group_by = params.get('group_by', 'aging_bucket')
        
        # Group records
        groups = {}
        for record in records:
            key = record.get(group_by, 'Unknown')
            
            if key not in groups:
                groups[key] = {
                    'group_name': key,
                    'records': [],
                    'count': 0,
                    'total_amount': 0,
                    'total_outstanding': 0
                }
            
            groups[key]['records'].append(record)
            groups[key]['count'] += 1
            groups[key]['total_amount'] += float(record.get('inr_amount', 0))
            groups[key]['total_outstanding'] += float(record.get('outstanding', 0))
        
        # Convert to list and sort
        groups_list = list(groups.values())
        
        # Sort by group name (for aging buckets, use custom order)
        if group_by == 'aging_bucket':
            bucket_order = {'0-30': 1, '31-60': 2, '61-90': 3, '90+': 4, 'Unknown': 5}
            groups_list.sort(key=lambda g: bucket_order.get(g['group_name'], 999))
        else:
            groups_list.sort(key=lambda g: g['group_name'])
        
        return {
            'groups': groups_list,
            'total_records': len(records),
            'total_groups': len(groups_list)
        }


@register_node
class SummaryNode(BaseNode):
    """
    Summary Node
    Calculates summary statistics
    """
    
    name = "Summary"
    category = "aggregation"
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "description": "Calculates summary statistics (total, average, min, max)",
            "category": self.category,
            "input_schema": {
                "data": {"type": "any", "required": True}
            },
            "output_schema": {
                "summary": {"type": "object", "description": "Summary statistics"}
            }
        }
    
    def run(self, input_data, params=None):
        """
        Calculate summary statistics
        
        Args:
            input_data: List of records, dict with groups, or dict with invoices
        """
        params = params or {}
        amount_field = params.get('amount_field', 'inr_amount')
        
        # Handle different input formats
        records = []
        
        if isinstance(input_data, dict):
            # If it has groups (from GroupingNode)
            if 'groups' in input_data:
                # Already has group summaries, just aggregate them
                groups = input_data['groups']
                total_amount = sum(g.get('total_amount', 0) for g in groups)
                total_outstanding = sum(g.get('total_outstanding', 0) for g in groups)
                total_records = sum(g.get('count', 0) for g in groups)
                
                return {
                    'summary': {
                        'total_records': total_records,
                        'total_amount': total_amount,
                        'total_outstanding': total_outstanding,
                        'average_amount': total_amount / total_records if total_records > 0 else 0,
                        'total_groups': len(groups)
                    },
                    'groups': groups  # Pass through groups
                }
            
            # If it has invoices
            elif 'invoices' in input_data:
                records = input_data['invoices']
            else:
                # Might be the result itself
                records = []
        
        elif isinstance(input_data, list):
            records = input_data
        else:
            records = []
        
        if not records:
            return {
                'summary': {
                    'total_records': 0,
                    'total_amount': 0,
                    'total_outstanding': 0,
                    'average_amount': 0
                }
            }
        
        # Calculate statistics
        amounts = [float(r.get(amount_field, 0)) for r in records]
        outstanding_amounts = [float(r.get('outstanding', 0)) for r in records]
        
        summary = {
            'total_records': len(records),
            'total_amount': sum(amounts),
            'total_outstanding': sum(outstanding_amounts),
            'average_amount': sum(amounts) / len(amounts) if amounts else 0,
            'min_amount': min(amounts) if amounts else 0,
            'max_amount': max(amounts) if amounts else 0,
            'average_outstanding': sum(outstanding_amounts) / len(outstanding_amounts) if outstanding_amounts else 0
        }
        
        return {
            'summary': summary,
            'invoices': records  # Pass through records
        }


@register_node
class FilterNode(BaseNode):
    """
    Filter Node
    Filters records based on conditions
    """
    
    name = "Filter"
    category = "aggregation"
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "description": "Filters records based on conditions",
            "category": self.category,
            "input_schema": {
                "records": {"type": "array", "required": True},
                "conditions": {"type": "array", "description": "Filter conditions"}
            },
            "output_schema": {
                "records": {"type": "array", "description": "Filtered records"}
            }
        }
    
    def run(self, input_data, params=None):
        """
        Filter records based on conditions
        
        Args:
            input_data: List of records or dict with records
            params: {conditions: [{field, operator, value}]}
        """
        params = params or {}
        
        # Handle different input formats
        if isinstance(input_data, dict):
            records = input_data.get('invoices', input_data.get('records', []))
        elif isinstance(input_data, list):
            records = input_data
        else:
            return []
        
        if not records:
            return []
        
        conditions = params.get('conditions', [])
        if not conditions:
            return records
        
        # Apply filters
        filtered = []
        for record in records:
            if self._matches_conditions(record, conditions):
                filtered.append(record)
        
        return filtered
    
    def _matches_conditions(self, record: Dict, conditions: List[Dict]) -> bool:
        """Check if record matches all conditions"""
        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')
            
            record_value = record.get(field)
            
            if operator == '>=':
                if not (record_value >= value):
                    return False
            elif operator == '<=':
                if not (record_value <= value):
                    return False
            elif operator == '>':
                if not (record_value > value):
                    return False
            elif operator == '<':
                if not (record_value < value):
                    return False
            elif operator == '==':
                if not (record_value == value):
                    return False
            elif operator == '!=':
                if not (record_value != value):
                    return False
            elif operator == 'in':
                if record_value not in value:
                    return False
        
        return True


@register_node
class SortNode(BaseNode):
    """
    Sort Node
    Sorts records by specified fields
    """
    
    name = "Sort"
    category = "aggregation"
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "description": "Sorts records by specified fields",
            "category": self.category,
            "input_schema": {
                "records": {"type": "array", "required": True},
                "sort_by": {"type": "array", "description": "Sort fields"}
            },
            "output_schema": {
                "records": {"type": "array", "description": "Sorted records"}
            }
        }
    
    def run(self, input_data, params=None):
        """
        Sort records
        
        Args:
            input_data: List of records or dict with records
            params: {sort_by: [{field, order: 'asc'|'desc'}]}
        """
        params = params or {}
        
        # Handle different input formats
        if isinstance(input_data, dict):
            records = input_data.get('invoices', input_data.get('records', []))
        elif isinstance(input_data, list):
            records = input_data
        else:
            return []
        
        if not records:
            return []
        
        sort_by = params.get('sort_by', [{'field': 'document_date', 'order': 'desc'}])
        
        # Sort
        sorted_records = records.copy()
        for sort_config in reversed(sort_by):
            field = sort_config.get('field')
            order = sort_config.get('order', 'asc')
            reverse = (order == 'desc')
            
            sorted_records.sort(
                key=lambda r: r.get(field, '') or '',
                reverse=reverse
            )
        
        return sorted_records