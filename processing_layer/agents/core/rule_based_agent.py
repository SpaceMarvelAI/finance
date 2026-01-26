"""
Rule-Based Agent
Applies configurable business rules to data
"""

from typing import Dict, Any, List, Optional
from processing_layer.agents.core.base_agent import BaseAgent, register_agent
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


@register_agent
class RuleBasedAgent(BaseAgent):
    """
    Rule-Based Agent
    
    Evaluates configurable rules without hardcoded logic
    Rules stored in database/configuration
    
    Rules Schema:
    {
        "rules": [
            {
                "name": "Rule name",
                "condition": {
                    "field": "field_name",
                    "operator": ">|<|=|in|contains",
                    "value": any
                },
                "action": "action_name",
                "priority": "low|medium|high|critical"
            }
        ]
    }
    """
    
    def __init__(self, rules_config: Optional[Dict] = None):
        """
        Initialize with rules configuration
        
        Args:
            rules_config: Rules configuration
        """
        super().__init__("RuleBasedAgent")
        self.rules = rules_config or {}
    
    def execute(self, input_data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate rules on input data
        
        Args:
            input_data: Data to evaluate (single item or list)
            params: Runtime parameters including rules
            
        Returns:
            {
                "status": "success",
                "rules_evaluated": int,
                "rules_matched": int,
                "results": [...]
            }
        """
        params = params or {}
        
        # Get rules (from params or instance config)
        rules = params.get('rules', self.rules.get('rules', []))
        
        if not rules:
            return {
                'status': 'error',
                'error': 'No rules provided'
            }
        
        self._log_decision(
            "Evaluating business rules",
            f"Total rules: {len(rules)}"
        )
        
        results = []
        
        try:
            for rule in rules:
                result = self._evaluate_rule(rule, input_data)
                results.append(result)
                
                if result['matched']:
                    self._log_decision(
                        f"Rule matched: {rule.get('name')}",
                        f"Action: {result.get('action')}, Matched: {result.get('matched_count', 1)}"
                    )
            
            matched_count = len([r for r in results if r['matched']])
            
            return {
                'status': 'success',
                'rules_evaluated': len(rules),
                'rules_matched': matched_count,
                'results': results,
                'execution_history': self.get_execution_history()
            }
            
        except Exception as e:
            logger.error(f"Rule evaluation failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'execution_history': self.get_execution_history()
            }
    
    def _evaluate_rule(self, rule: Dict, data: Any) -> Dict:
        """
        Evaluate a single rule against data
        
        Args:
            rule: Rule definition
            data: Data to evaluate
            
        Returns:
            {
                "rule": "rule_name",
                "matched": bool,
                "action": "action_name",
                "matched_items": [...]
            }
        """
        rule_name = rule.get('name', 'Unnamed rule')
        condition = rule.get('condition', {})
        action = rule.get('action')
        
        # Handle list data
        if isinstance(data, list):
            matched_items = [
                item for item in data 
                if self._check_condition(condition, item)
            ]
            
            matched = len(matched_items) > 0
            
            return {
                'rule': rule_name,
                'matched': matched,
                'matched_count': len(matched_items),
                'action': action if matched else None,
                'priority': rule.get('priority'),
                'matched_items': matched_items[:10]  # Limit to 10 for performance
            }
        
        # Handle single item
        else:
            matched = self._check_condition(condition, data)
            
            return {
                'rule': rule_name,
                'matched': matched,
                'matched_count': 1 if matched else 0,
                'action': action if matched else None,
                'priority': rule.get('priority')
            }
    
    def _check_condition(self, condition: Dict, item: Any) -> bool:
        """
        Check if condition is met for an item
        
        Args:
            condition: Condition definition
            item: Item to check
            
        Returns:
            True if condition met
        """
        if not isinstance(item, dict):
            return False
        
        # Handle complex conditions (AND/OR)
        if 'and' in condition:
            return all(self._check_condition(c, item) for c in condition['and'])
        
        if 'or' in condition:
            return any(self._check_condition(c, item) for c in condition['or'])
        
        # Simple condition
        field = condition.get('field')
        operator = condition.get('operator', '=')
        value = condition.get('value')
        
        if not field:
            return False
        
        item_value = item.get(field)
        
        # Handle None values
        if item_value is None:
            return operator == '=' and value is None
        
        # Evaluate based on operator
        try:
            if operator == '=':
                return item_value == value
            
            elif operator == '!=':
                return item_value != value
            
            elif operator == '>':
                return float(item_value) > float(value)
            
            elif operator == '<':
                return float(item_value) < float(value)
            
            elif operator == '>=':
                return float(item_value) >= float(value)
            
            elif operator == '<=':
                return float(item_value) <= float(value)
            
            elif operator == 'contains':
                return str(value).lower() in str(item_value).lower()
            
            elif operator == 'not_contains':
                return str(value).lower() not in str(item_value).lower()
            
            elif operator == 'in':
                if isinstance(value, list):
                    return item_value in value
                return False
            
            elif operator == 'not_in':
                if isinstance(value, list):
                    return item_value not in value
                return True
            
            elif operator == 'startswith':
                return str(item_value).startswith(str(value))
            
            elif operator == 'endswith':
                return str(item_value).endswith(str(value))
            
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Condition evaluation error: {e}")
            return False