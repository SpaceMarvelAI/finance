"""
Output Template Nodes for Financial Reports
Specialized nodes for generating branded reports with different formats
"""

from .base_template_node import BaseTemplateNode
from .excel_template_node import ExcelTemplateNode
from .branding_node import BrandingLoaderNode

# Report Template Nodes - Fixed versions
from .report_templates.ap_aging_node_fixed import APAgingReportNode
from .report_templates.ap_register_node_fixed import APRegisterReportNode
from .report_templates.ar_aging_node_fixed import ARAgingReportNode
from .report_templates.ar_register_node import ARRegisterReportNode
from .report_templates.ar_collection_node import ARCollectionReportNode
from .report_templates.dso_node import DSOReportNode
from .report_templates.ap_overdue_node import APOverdueReportNode

__all__ = [
    'BaseTemplateNode',
    'ExcelTemplateNode', 
    'BrandingLoaderNode',
    'APAgingReportNode',
    'APRegisterReportNode',
    'ARCollectionReportNode',
    'ARAgingReportNode',
    'ARRegisterReportNode',
    'DSOReportNode',
    'APOverdueReportNode'
]
