"""
Prompt Library System
Centralized repository of prompts for all 11 financial domains
Integrates with LLM Router for natural language report generation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class PromptCategory(Enum):
    """Prompt categories matching the 11 domains"""
    FINANCE = "FinanceLayer"
    AP = "APLayer"
    AR = "ARLayer"
    REPORT = "ReportLayer"
    ANALYSIS = "AnalysisLayer"
    RECONCILIATION = "ReconciliationLayer"
    COMPLIANCE = "ComplianceLayer"
    CASH_FLOW = "CashFlowLayer"
    TAX = "TaxLayer"
    BUDGET = "BudgetLayer"
    ALERT = "AlertLayer"


@dataclass
class PromptTemplate:
    """Prompt template with metadata"""
    id: str
    name: str
    category: PromptCategory
    description: str
    template: str
    required_variables: List[str]
    optional_variables: List[str]
    output_format: str
    report_type: str
    examples: List[str]


class PromptLibrary:
    """
    Centralized Prompt Library
    
    Manages all prompts for financial report generation
    Integrates with LLM Router for variable extraction and injection
    """
    
    def __init__(self):
        self.prompts: Dict[str, PromptTemplate] = {}
        self._initialize_prompts()
    
    def _initialize_prompts(self):
        """Initialize all prompt templates"""
        
        # ===== AP LAYER PROMPTS =====
        
        self.add_prompt(PromptTemplate(
            id="ap_aging_report",
            name="AP Aging Report",
            category=PromptCategory.AP,
            description="Generate accounts payable aging analysis",
            template="""
Generate a comprehensive AP Aging Report with the following requirements:

Time Period: {time_period}
Aging Buckets: {aging_buckets}
Vendor Filter: {vendor_filter}
Amount Threshold: {amount_threshold}
Status Filter: {status_filter}
Currency: {currency}

Report Requirements:
1. Group invoices by aging bucket (Current, 0-30, 31-60, 61-90, 90+ days)
2. Calculate total outstanding for each bucket
3. Show vendor-wise breakdown
4. Include invoice details: number, date, due date, amount, days overdue
5. Provide summary statistics (total payables, overdue amount, average days outstanding)
6. Highlight critical items (>90 days overdue or high-value invoices)

Output Format: {output_format}
Sort By: {sort_by}
            """,
            required_variables=["time_period"],
            optional_variables=["aging_buckets", "vendor_filter", "amount_threshold", 
                              "status_filter", "currency", "output_format", "sort_by"],
            output_format="excel",
            report_type="ap_aging",
            examples=[
                "Show me AP aging for last month",
                "Generate AP aging report for all vendors over $5000",
                "AP aging breakdown by 30-day buckets"
            ]
        ))
        
        self.add_prompt(PromptTemplate(
            id="ap_invoice_register",
            name="AP Invoice Register",
            category=PromptCategory.AP,
            description="Complete list of AP invoices with details",
            template="""
Generate AP Invoice Register with the following specifications:

Date Range: {date_from} to {date_to}
Vendor: {vendor}
Invoice Status: {status}
Amount Range: {amount_min} to {amount_max}
Payment Status: {payment_status}
GL Account: {gl_account}

Report Requirements:
1. List all invoices matching criteria
2. Include columns: Invoice Number, Date, Vendor, Amount, Status, Due Date, Payment Date
3. Calculate subtotals by vendor
4. Show payment history if available
5. Include invoice line items if requested
6. Flag duplicates if any

Output Format: {output_format}
Group By: {group_by}
Sort By: {sort_by}
            """,
            required_variables=["date_from", "date_to"],
            optional_variables=["vendor", "status", "amount_min", "amount_max", 
                              "payment_status", "gl_account", "output_format", 
                              "group_by", "sort_by"],
            output_format="excel",
            report_type="ap_register",
            examples=[
                "Show all AWS invoices from last month",
                "List unpaid invoices over $10,000",
                "AP register for Q4 2024"
            ]
        ))
        
        self.add_prompt(PromptTemplate(
            id="ap_overdue_sla",
            name="AP Overdue & SLA Report",
            category=PromptCategory.AP,
            description="Track overdue invoices and SLA violations",
            template="""
Generate AP Overdue & SLA Violation Report:

As Of Date: {as_of_date}
Overdue Threshold: {overdue_days} days
SLA Threshold: {sla_days} days
Vendor Filter: {vendor_filter}
Priority: {priority}
Amount Threshold: {amount_threshold}

Report Requirements:
1. List all overdue invoices (past due date)
2. Calculate days overdue for each invoice
3. Flag SLA violations (invoices not paid within agreed terms)
4. Show vendor-wise overdue summary
5. Calculate late payment penalties if applicable
6. Prioritize by amount and days overdue
7. Include payment commitment dates if available

Output Format: {output_format}
Alert Level: {alert_level}
            """,
            required_variables=["as_of_date"],
            optional_variables=["overdue_days", "sla_days", "vendor_filter", 
                              "priority", "amount_threshold", "output_format", "alert_level"],
            output_format="excel",
            report_type="ap_overdue",
            examples=[
                "Show overdue invoices over 30 days",
                "List SLA violations for critical vendors",
                "AP overdue report with penalties"
            ]
        ))
        
        # ===== AR LAYER PROMPTS =====
        
        self.add_prompt(PromptTemplate(
            id="ar_aging_report",
            name="AR Aging Report",
            category=PromptCategory.AR,
            description="Generate accounts receivable aging analysis",
            template="""
Generate comprehensive AR Aging Report:

Time Period: {time_period}
Aging Buckets: {aging_buckets}
Customer Filter: {customer_filter}
Amount Threshold: {amount_threshold}
Status Filter: {status_filter}
Currency: {currency}

Report Requirements:
1. Group receivables by aging bucket (Current, 0-30, 31-60, 61-90, 90+ days)
2. Calculate total receivables for each bucket
3. Show customer-wise breakdown
4. Include invoice details: number, date, due date, amount, days outstanding
5. Calculate DSO (Days Sales Outstanding)
6. Provide summary statistics and collection recommendations
7. Highlight bad debt risks (>90 days overdue)

Output Format: {output_format}
Sort By: {sort_by}
            """,
            required_variables=["time_period"],
            optional_variables=["aging_buckets", "customer_filter", "amount_threshold",
                              "status_filter", "currency", "output_format", "sort_by"],
            output_format="excel",
            report_type="ar_aging",
            examples=[
                "Show me AR aging for Q4",
                "Customer receivables over 60 days",
                "AR aging with DSO calculation"
            ]
        ))
        
        self.add_prompt(PromptTemplate(
            id="ar_invoice_register",
            name="AR Invoice Register",
            category=PromptCategory.AR,
            description="Complete list of AR invoices",
            template="""
Generate AR Invoice Register:

Date Range: {date_from} to {date_to}
Customer: {customer}
Invoice Status: {status}
Amount Range: {amount_min} to {amount_max}
Payment Status: {payment_status}
Sales Region: {region}

Report Requirements:
1. List all customer invoices matching criteria
2. Include columns: Invoice Number, Date, Customer, Amount, Status, Due Date, Payment Date
3. Calculate subtotals by customer
4. Show payment applications
5. Track partial payments
6. Include sales tax breakdown

Output Format: {output_format}
Group By: {group_by}
Sort By: {sort_by}
            """,
            required_variables=["date_from", "date_to"],
            optional_variables=["customer", "status", "amount_min", "amount_max",
                              "payment_status", "region", "output_format", 
                              "group_by", "sort_by"],
            output_format="excel",
            report_type="ar_register",
            examples=[
                "Show all invoices for Acme Corp",
                "List unpaid customer invoices",
                "AR register for January 2025"
            ]
        ))
        
        # ===== ANALYSIS LAYER PROMPTS =====
        
        self.add_prompt(PromptTemplate(
            id="revenue_trend_analysis",
            name="Revenue Trend Analysis",
            category=PromptCategory.ANALYSIS,
            description="Analyze revenue trends and patterns",
            template="""
Generate Revenue Trend Analysis:

Time Period: {time_period}
Comparison Type: {comparison_type}
Metrics: {metrics}
Breakdown By: {breakdown_by}
Include Forecast: {include_forecast}

Analysis Requirements:
1. Calculate revenue for each period (daily, weekly, monthly, quarterly)
2. Compare with previous period (MoM, QoQ, YoY)
3. Show percentage growth/decline
4. Break down by product, customer, region as requested
5. Identify trends and patterns
6. Highlight anomalies (spikes or drops)
7. Generate forecast for next period if requested
8. Include visualizations (line charts, bar charts)

Metrics to Include:
- Total Revenue
- Average Revenue per Customer
- Revenue Growth Rate
- Top Revenue Contributors
- Revenue by Category

Output Format: {output_format}
Include Charts: {include_charts}
            """,
            required_variables=["time_period"],
            optional_variables=["comparison_type", "metrics", "breakdown_by",
                              "include_forecast", "output_format", "include_charts"],
            output_format="excel",
            report_type="revenue_analysis",
            examples=[
                "Analyze revenue trends for Q4 year over year",
                "Show monthly revenue growth for 2024",
                "Revenue analysis by product category"
            ]
        ))
        
        self.add_prompt(PromptTemplate(
            id="expense_analysis",
            name="Expense Analysis",
            category=PromptCategory.ANALYSIS,
            description="Analyze spending patterns and trends",
            template="""
Generate Expense Analysis Report:

Time Period: {time_period}
Expense Category: {category}
Department: {department}
Vendor: {vendor}
Amount Threshold: {amount_threshold}
Comparison Type: {comparison_type}

Analysis Requirements:
1. Total expenses by category
2. Period-over-period comparison (MoM, QoQ, YoY)
3. Department-wise breakdown
4. Top spending vendors
5. Identify unusual spending patterns
6. Calculate average expense per transaction
7. Show budget vs actual if available
8. Highlight areas of overspending

Metrics to Include:
- Total Expenses
- Average Expense per Transaction
- Expense Growth Rate
- Top Expense Categories
- Vendor Concentration

Output Format: {output_format}
Include Charts: {include_charts}
            """,
            required_variables=["time_period"],
            optional_variables=["category", "department", "vendor", "amount_threshold",
                              "comparison_type", "output_format", "include_charts"],
            output_format="excel",
            report_type="expense_analysis",
            examples=[
                "Analyze software expenses for 2024",
                "Department spending trends Q4",
                "Vendor expense analysis with year over year comparison"
            ]
        ))
        
        # ===== RECONCILIATION LAYER PROMPTS =====
        
        self.add_prompt(PromptTemplate(
            id="bank_reconciliation",
            name="Bank Reconciliation Report",
            category=PromptCategory.RECONCILIATION,
            description="Reconcile bank statements with book records",
            template="""
Generate Bank Reconciliation Report:

Bank Account: {bank_account}
Statement Period: {statement_period}
Statement Date: {statement_date}
Opening Balance: {opening_balance}
Closing Balance: {closing_balance}

Reconciliation Requirements:
1. Match bank transactions with book entries
2. Identify unmatched transactions
3. List outstanding checks (issued but not cleared)
4. List deposits in transit (recorded but not in bank)
5. Calculate reconciled balance
6. Show reconciliation differences
7. Categorize unmatched items (timing differences, errors, missing entries)
8. Provide recommended actions for discrepancies

Report Sections:
- Bank Statement Summary
- Book Balance Summary
- Matched Transactions
- Unmatched Bank Transactions
- Unmatched Book Transactions
- Outstanding Items
- Reconciliation Adjustment

Output Format: {output_format}
            """,
            required_variables=["bank_account", "statement_period"],
            optional_variables=["statement_date", "opening_balance", "closing_balance",
                              "output_format"],
            output_format="excel",
            report_type="bank_reconciliation",
            examples=[
                "Reconcile bank statement for December 2024",
                "Bank rec for checking account",
                "Match bank transactions with book entries"
            ]
        ))
        
        # ===== CASH FLOW LAYER PROMPTS =====
        
        self.add_prompt(PromptTemplate(
            id="cash_flow_forecast",
            name="Cash Flow Forecast",
            category=PromptCategory.CASH_FLOW,
            description="Forecast cash inflows and outflows",
            template="""
Generate Cash Flow Forecast:

Forecast Period: {forecast_period}
Forecast Method: {forecast_method}
Include Scenarios: {include_scenarios}
Granularity: {granularity}

Forecast Requirements:
1. Starting cash balance
2. Expected cash inflows (by source):
   - Customer payments (from AR)
   - Other income
3. Expected cash outflows (by category):
   - Vendor payments (from AP)
   - Payroll
   - Operating expenses
   - Capital expenditures
4. Net cash flow by period
5. Ending cash balance
6. Minimum cash threshold alerts
7. Scenario analysis (best case, worst case, most likely)
8. Cash runway calculation

Analysis:
- Identify cash surplus/deficit periods
- Recommend actions for cash management
- Highlight periods needing financing

Output Format: {output_format}
Include Charts: {include_charts}
            """,
            required_variables=["forecast_period"],
            optional_variables=["forecast_method", "include_scenarios", "granularity",
                              "output_format", "include_charts"],
            output_format="excel",
            report_type="cash_flow_forecast",
            examples=[
                "Cash flow forecast for next quarter",
                "Weekly cash flow projection",
                "Cash forecast with scenarios"
            ]
        ))
        
        # ===== TAX LAYER PROMPTS =====
        
        self.add_prompt(PromptTemplate(
            id="gst_calculation",
            name="GST/VAT Calculation Report",
            category=PromptCategory.TAX,
            description="Calculate GST/VAT liability and credits",
            template="""
Generate GST/VAT Calculation Report:

Tax Period: {tax_period}
Tax Type: {tax_type}
Tax Rate: {tax_rate}
Include Exemptions: {include_exemptions}

Report Requirements:
1. Output Tax (Tax on Sales):
   - Total taxable sales
   - GST/VAT collected
   - Break down by tax rate
2. Input Tax (Tax on Purchases):
   - Total taxable purchases
   - GST/VAT paid
   - Break down by tax rate
3. Net Tax Liability:
   - Output tax minus input tax
   - Refund due or payment required
4. Transaction Details:
   - List of taxable transactions
   - Invoice numbers and amounts
   - Tax amounts
5. Exempted Transactions:
   - Zero-rated supplies
   - Exempt supplies
6. Adjustments and Reversals

Output Format: {output_format}
Include Supporting Documents: {include_docs}
            """,
            required_variables=["tax_period"],
            optional_variables=["tax_type", "tax_rate", "include_exemptions",
                              "output_format", "include_docs"],
            output_format="excel",
            report_type="gst_calculation",
            examples=[
                "Calculate GST for last month",
                "GST return for Q3 2024",
                "VAT calculation with input credits"
            ]
        ))
        
        # ===== BUDGET LAYER PROMPTS =====
        
        self.add_prompt(PromptTemplate(
            id="budget_variance_analysis",
            name="Budget vs Actual Variance Analysis",
            category=PromptCategory.BUDGET,
            description="Compare actual spending against budget",
            template="""
Generate Budget Variance Analysis:

Time Period: {time_period}
Department: {department}
Cost Center: {cost_center}
Category: {category}
Variance Threshold: {variance_threshold}

Report Requirements:
1. Budget vs Actual Comparison:
   - Budgeted amount
   - Actual amount
   - Variance (dollar and percentage)
2. Analysis by:
   - Department
   - Cost center
   - Expense category
   - Time period
3. Variance Classification:
   - Favorable variance (under budget)
   - Unfavorable variance (over budget)
4. Highlight significant variances (>10% or threshold)
5. Year-to-date comparison
6. Forecast to year-end
7. Recommended actions for large variances

Metrics:
- Total Budget
- Total Actual
- Total Variance
- Variance %
- Budget Utilization %

Output Format: {output_format}
Include Charts: {include_charts}
            """,
            required_variables=["time_period"],
            optional_variables=["department", "cost_center", "category",
                              "variance_threshold", "output_format", "include_charts"],
            output_format="excel",
            report_type="budget_variance",
            examples=[
                "Budget vs actual for Engineering department",
                "Show budget variance for Q4",
                "Variance analysis for marketing expenses"
            ]
        ))
        
        # ===== COMPLIANCE LAYER PROMPTS =====
        
        self.add_prompt(PromptTemplate(
            id="audit_trail_report",
            name="Audit Trail Report",
            category=PromptCategory.COMPLIANCE,
            description="Track all financial transactions for audit",
            template="""
Generate Audit Trail Report:

Time Period: {time_period}
Transaction Type: {transaction_type}
User: {user}
Entity: {entity}
Include Changes: {include_changes}

Report Requirements:
1. Complete transaction log:
   - Date and time
   - User who performed action
   - Transaction type (create, modify, delete)
   - Entity affected (invoice, payment, journal entry)
   - Before and after values (for modifications)
   - IP address and location
2. Filter by:
   - Date range
   - User
   - Transaction type
   - Entity
3. Highlight suspicious activities:
   - Unusual access patterns
   - High-value changes
   - Deleted transactions
4. Compliance checks:
   - Segregation of duties
   - Authorization levels
   - Required approvals

Output Format: {output_format}
Include Details: {include_details}
            """,
            required_variables=["time_period"],
            optional_variables=["transaction_type", "user", "entity", "include_changes",
                              "output_format", "include_details"],
            output_format="excel",
            report_type="audit_trail",
            examples=[
                "Show all transactions modified in January",
                "Audit trail for invoice deletions",
                "User activity report for compliance"
            ]
        ))
        
        # ===== ALERT LAYER PROMPTS =====
        
        self.add_prompt(PromptTemplate(
            id="overdue_alerts",
            name="Overdue & SLA Alert Report",
            category=PromptCategory.ALERT,
            description="Generate alerts for overdue items and SLA violations",
            template="""
Generate Alert Report for Overdue Items:

Alert Type: {alert_type}
Overdue Threshold: {overdue_threshold}
Priority Level: {priority}
Entity Filter: {entity_filter}
Amount Threshold: {amount_threshold}

Alert Categories:
1. Overdue Invoices (Payable):
   - Invoices past due date
   - Days overdue
   - Late payment penalties
2. Overdue Invoices (Receivable):
   - Customer invoices past due
   - Collection recommendations
3. SLA Violations:
   - Payments not made within agreed terms
   - Processing delays
4. Critical Items:
   - High-value overdue items
   - Multiple violations from same entity
5. Escalation Requirements:
   - Items requiring manager attention
   - Items needing executive approval

Alert Format:
- Priority (Critical, High, Medium, Low)
- Description
- Amount
- Days overdue
- Responsible person
- Recommended action
- Escalation level

Output Format: {output_format}
Notification: {send_notification}
            """,
            required_variables=["alert_type"],
            optional_variables=["overdue_threshold", "priority", "entity_filter",
                              "amount_threshold", "output_format", "send_notification"],
            output_format="excel",
            report_type="overdue_alerts",
            examples=[
                "Show all critical overdue items",
                "Alert for invoices over 90 days",
                "SLA violations requiring escalation"
            ]
        ))
        
        # ===== REPORT LAYER PROMPTS =====
        
        self.add_prompt(PromptTemplate(
            id="financial_dashboard",
            name="Financial Dashboard",
            category=PromptCategory.FINANCE,
            description="Comprehensive financial overview",
            template="""
Generate Financial Dashboard:

Time Period: {time_period}
Metrics: {metrics}
Include Comparisons: {include_comparisons}
Breakdown By: {breakdown_by}

Dashboard Components:
1. Key Performance Indicators:
   - Revenue (current period)
   - Expenses (current period)
   - Profit/Loss
   - Cash balance
   - AR total
   - AP total
2. Period Comparisons:
   - Month-over-month
   - Quarter-over-quarter
   - Year-over-year
3. Trend Charts:
   - Revenue trend
   - Expense trend
   - Cash flow trend
4. Aging Summaries:
   - AR aging buckets
   - AP aging buckets
5. Top Lists:
   - Top customers by revenue
   - Top vendors by expense
   - Top overdue items
6. Alerts:
   - Critical items requiring attention
   - SLA violations
   - Budget overruns

Output Format: {output_format}
Include Charts: {include_charts}
            """,
            required_variables=["time_period"],
            optional_variables=["metrics", "include_comparisons", "breakdown_by",
                              "output_format", "include_charts"],
            output_format="excel",
            report_type="financial_dashboard",
            examples=[
                "Show financial dashboard for Q4",
                "Generate monthly KPI report",
                "Financial overview with comparisons"
            ]
        ))
    
    def add_prompt(self, prompt: PromptTemplate):
        """Add prompt to library"""
        self.prompts[prompt.id] = prompt
    
    def get_prompt(self, prompt_id: str) -> Optional[PromptTemplate]:
        """Get prompt by ID"""
        return self.prompts.get(prompt_id)
    
    def get_prompts_by_category(self, category: PromptCategory) -> List[PromptTemplate]:
        """Get all prompts for a category"""
        return [p for p in self.prompts.values() if p.category == category]
    
    def search_prompts(self, query: str) -> List[PromptTemplate]:
        """Search prompts by name or description"""
        query_lower = query.lower()
        return [
            p for p in self.prompts.values()
            if query_lower in p.name.lower() or query_lower in p.description.lower()
        ]
    
    def inject_variables(
        self, 
        prompt_id: str, 
        variables: Dict[str, Any]
    ) -> Optional[str]:
        """
        Inject variables into prompt template
        
        Args:
            prompt_id: Prompt template ID
            variables: Dictionary of variables to inject
            
        Returns:
            Rendered prompt with variables injected
        """
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None
        
        # Set defaults for missing optional variables
        filled_vars = self._fill_default_variables(prompt, variables)
        
        # Inject variables into template
        try:
            rendered = prompt.template.format(**filled_vars)
            return rendered
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")
    
    def _fill_default_variables(
        self, 
        prompt: PromptTemplate, 
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fill in default values for missing optional variables"""
        filled = variables.copy()
        
        # Default values
        defaults = {
            "time_period": "last month",
            "aging_buckets": "30, 60, 90 days",
            "vendor_filter": "all vendors",
            "customer_filter": "all customers",
            "amount_threshold": "no minimum",
            "status_filter": "all statuses",
            "currency": "USD",
            "output_format": "excel",
            "sort_by": "amount descending",
            "group_by": "vendor",
            "date_from": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "date_to": datetime.now().strftime("%Y-%m-%d"),
            "as_of_date": datetime.now().strftime("%Y-%m-%d"),
            "overdue_days": "30",
            "sla_days": "45",
            "priority": "all",
            "alert_level": "high",
            "comparison_type": "year over year",
            "metrics": "all metrics",
            "breakdown_by": "category",
            "include_forecast": "no",
            "include_charts": "yes",
            "category": "all categories",
            "department": "all departments",
            "vendor": "all vendors",
            "customer": "all customers",
            "status": "all",
            "amount_min": "0",
            "amount_max": "unlimited",
            "payment_status": "all",
            "gl_account": "all accounts",
            "region": "all regions",
            "bank_account": "main checking",
            "statement_period": "current month",
            "statement_date": datetime.now().strftime("%Y-%m-%d"),
            "opening_balance": "0.00",
            "closing_balance": "0.00",
            "forecast_period": "next 90 days",
            "forecast_method": "historical average",
            "include_scenarios": "yes",
            "granularity": "monthly",
            "tax_period": "current quarter",
            "tax_type": "GST",
            "tax_rate": "18%",
            "include_exemptions": "yes",
            "include_docs": "no",
            "cost_center": "all",
            "variance_threshold": "10%",
            "transaction_type": "all",
            "user": "all users",
            "entity": "all entities",
            "include_changes": "yes",
            "include_details": "yes",
            "alert_type": "overdue",
            "overdue_threshold": "30 days",
            "entity_filter": "all",
            "send_notification": "no",
            "include_comparisons": "yes"
        }
        
        # Fill missing variables with defaults
        for var in prompt.required_variables + prompt.optional_variables:
            if var not in filled:
                filled[var] = defaults.get(var, "N/A")
        
        return filled
    
    def list_all_prompts(self) -> List[Dict[str, Any]]:
        """List all available prompts with metadata"""
        return [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category.value,
                "description": p.description,
                "report_type": p.report_type,
                "examples": p.examples
            }
            for p in self.prompts.values()
        ]
    
    def get_prompt_for_report_type(self, report_type: str) -> Optional[PromptTemplate]:
        """Get prompt by report type"""
        for prompt in self.prompts.values():
            if prompt.report_type == report_type:
                return prompt
        return None


# Example usage
if __name__ == "__main__":
    library = PromptLibrary()
    
    # List all prompts
    print("Available Prompts:")
    for prompt_info in library.list_all_prompts():
        print(f"  - {prompt_info['name']} ({prompt_info['category']})")
        print(f"    Report Type: {prompt_info['report_type']}")
        print(f"    Examples: {prompt_info['examples'][0]}")
        print()
    
    # Example: Inject variables into AP Aging prompt
    variables = {
        "time_period": "December 2024",
        "vendor_filter": "AWS, Google Cloud, Microsoft",
        "amount_threshold": "$5,000",
        "aging_buckets": "30, 60, 90, 120 days",
        "output_format": "Excel with charts"
    }
    
    rendered = library.inject_variables("ap_aging_report", variables)
    print("\n" + "="*80)
    print("RENDERED PROMPT:")
    print("="*80)
    print(rendered)