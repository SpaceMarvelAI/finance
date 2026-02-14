"""
Node Registry
Maps node classes to human-readable metadata
"""

from typing import Dict, Any, List

class NodeMetadata:
    """Metadata for a workflow node"""
    
    def __init__(self, title: str, description: str, category: str, icon: str = ""):
        self.title = title
        self.description = description
        self.category = category
        self.icon = icon
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "icon": self.icon
        }


# Define metadata for ALL nodes
NODE_METADATA_REGISTRY = {
    # Data Fetch Nodes
    "InvoiceFetchNode": NodeMetadata(
        title="Fetch All Invoices",
        description="Retrieve invoices from the database",
        category="data_fetch"
    ),
    "InvoiceFetchNodePurchase": NodeMetadata(
        title="Fetch Purchase Invoices",
        description="Retrieve purchase invoices from vendors",
        category="data_fetch"
    ),
    "InvoiceFetchNodeSales": NodeMetadata(
        title="Fetch Sales Invoices",
        description="Retrieve sales invoices from customers",
        category="data_fetch"
    ),
    
    # Calculation Nodes
    "OutstandingCalculatorNode": NodeMetadata(
        title="Calculate Outstanding",
        description="Calculate outstanding amounts for invoices",
        category="calculation"
    ),
    "AgingCalculatorNode": NodeMetadata(
        title="Calculate Aging Days",
        description="Calculate aging buckets (0-30, 31-60, etc.)",
        category="calculation"
    ),
    "TotalsCalculationNode": NodeMetadata(
        title="Calculate Totals",
        description="Calculate summary totals",
        category="calculation"
    ),
    
    # Filter & Processing Nodes
    "FilterNode": NodeMetadata(
        title="Filter Data",
        description="Filter data based on conditions",
        category="processing"
    ),
    "SortNode": NodeMetadata(
        title="Sort Data",
        description="Sort data by specified fields",
        category="processing"
    ),
    "GroupingNode": NodeMetadata(
        title="Group by Bucket",
        description="Group data into categories",
        category="processing"
    ),
    "DataTransformationNode": NodeMetadata(
        title="Format Data",
        description="Transform data for output",
        category="processing"
    ),
    
    # Analysis Nodes
    "SummaryNode": NodeMetadata(
        title="Calculate Summary",
        description="Generate summary statistics",
        category="analysis"
    ),
    "SLACheckerNode": NodeMetadata(
        title="Check SLA Breaches",
        description="Check for SLA breaches",
        category="analysis"
    ),
    "DuplicateDetectorNode": NodeMetadata(
        title="Detect Duplicates",
        description="Identify duplicate invoices",
        category="analysis"
    ),
    
    # Output Nodes
    "ExcelGeneratorNode": NodeMetadata(
        title="Export Excel",
        description="Generate Excel report",
        category="output"
    ),
}


def get_node_metadata(node_class_name: str) -> Dict[str, Any]:
    """Get metadata for a node class"""
    metadata = NODE_METADATA_REGISTRY.get(node_class_name)
    
    if metadata:
        return metadata.to_dict()
    
    # Fallback: prettify the class name
    pretty_name = node_class_name.replace('Node', '').replace('_', ' ').title()
    return {
        "title": pretty_name,
        "description": f"Execute {pretty_name}",
        "category": "unknown"
    }


def register_node_metadata(node_class_name: str, metadata: NodeMetadata):
    """Register new node metadata"""
    NODE_METADATA_REGISTRY[node_class_name] = metadata