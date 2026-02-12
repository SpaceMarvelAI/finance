"""
Report Generation Agent
Specialized agent for generating financial reports and visualizations
"""

from typing import Dict, Any, Optional, List, Union
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class ReportGenerationAgent:
    """
    Report Generation Agent
    
    Generates financial reports, visualizations, and formatted outputs.
    Handles report templates, branding, and various output formats.
    """
    
    def __init__(self, name: str, llm_config: Dict[str, Any], 
                 agent_type: str = 'report_generation',
                 capabilities: Optional[List[str]] = None,
                 tools: Optional[List[str]] = None,
                 **kwargs):
        self.name = name
        self.llm_config = llm_config
        self.agent_type = agent_type
        self.capabilities = capabilities or ['report_generation', 'data_visualization', 'template_processing']
        self.tools = tools or ['report_tools', 'visualization_tools']
        
        # Initialize agent
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the report generation agent"""
        try:
            # Import AutoGen components
            from autogen import AssistantAgent
            
            # Create system message for report generation
            system_message = self._generate_system_message()
            
            # Create AutoGen agent
            self.agent = AssistantAgent(
                name=self.name,
                system_message=system_message,
                llm_config=self.llm_config,
                **self._get_agent_config()
            )
            
            logger.info(f"Initialized Report Generation Agent: {self.name}")
            
        except Exception as e:
            logger.error(f"Error initializing Report Generation Agent: {str(e)}")
            raise
    
    def generate_report(self, calculation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a financial report from calculation results
        
        Args:
            calculation_results: Results from calculations to include in report
            
        Returns:
            Generated report
        """
        try:
            # Create report generation prompt
            report_prompt = self._create_report_generation_prompt(calculation_results)
            
            # Get report structure from LLM
            report_structure = self.agent.generate_reply(
                messages=[{'content': report_prompt, 'role': 'user'}]
            )
            
            # Generate report content
            report_content = self._generate_report_content(calculation_results, report_structure)
            
            logger.info(f"Generated report from {len(calculation_results.get('results', {}))} calculation results")
            
            return report_content
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {
                'error': str(e),
                'calculation_results': calculation_results,
                'report': None
            }
    
    def create_visualizations(self, data: Dict[str, Any], 
                             visualization_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create data visualizations
        
        Args:
            data: Data to visualize
            visualization_config: Configuration for visualizations
            
        Returns:
            Created visualizations
        """
        try:
            # Create visualization prompt
            viz_prompt = self._create_visualization_prompt(data, visualization_config)
            
            # Get visualization instructions from LLM
            viz_instructions = self.agent.generate_reply(
                messages=[{'content': viz_prompt, 'role': 'user'}]
            )
            
            # Create visualizations
            visualizations = self._create_visualizations_from_instructions(data, viz_instructions)
            
            logger.info(f"Created visualizations with config: {visualization_config}")
            
            return visualizations
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {str(e)}")
            return {
                'error': str(e),
                'data': data,
                'visualization_config': visualization_config,
                'visualizations': None
            }
    
    def apply_branding(self, report: Dict[str, Any], 
                      branding_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply company branding to report
        
        Args:
            report: Report to apply branding to
            branding_config: Branding configuration
            
        Returns:
            Branded report
        """
        try:
            # Create branding prompt
            branding_prompt = self._create_branding_prompt(report, branding_config)
            
            # Get branding instructions from LLM
            branding_instructions = self.agent.generate_reply(
                messages=[{'content': branding_prompt, 'role': 'user'}]
            )
            
            # Apply branding
            branded_report = self._apply_branding_to_report(report, branding_instructions)
            
            logger.info(f"Applied branding to report: {branding_config}")
            
            return branded_report
            
        except Exception as e:
            logger.error(f"Error applying branding: {str(e)}")
            return {
                'error': str(e),
                'report': report,
                'branding_config': branding_config,
                'branded_report': None
            }
    
    def _generate_system_message(self) -> str:
        """Generate system message for the report generation agent"""
        return """
        You are a specialized Report Generation Agent. Your role is to:
        
        1. Generate comprehensive financial reports from calculation results
        2. Create data visualizations and charts for better understanding
        3. Apply company branding and formatting to reports
        4. Handle various report templates and output formats
        5. Ensure reports are professional, accurate, and actionable
        6. Generate executive summaries and key insights
        
        Your capabilities include:
        - Report generation and formatting
        - Data visualization and chart creation
        - Template processing and customization
        - Branding application and styling
        - Multiple output format support (Excel, PDF, HTML)
        - Executive summary generation
        
        When generating reports, focus on:
        - What type of report is needed based on the data and requirements?
        - What visualizations would best represent the data?
        - How should the report be structured and formatted?
        - What branding elements should be applied?
        - What output format should be used?
        - What key insights and summaries should be included?
        
        Always ensure reports are professional, accurate, and provide actionable insights.
        """
    
    def _get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration"""
        return {
            'human_input_mode': 'NEVER',
            'max_consecutive_auto_reply': 10,
            'temperature': 0.6,
            'top_p': 0.9,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0
        }
    
    def _create_report_generation_prompt(self, calculation_results: Dict[str, Any]) -> str:
        """Create prompt for report generation"""
        return f"""
        Generate a financial report from the following calculation results:

        Calculation Results:
        {calculation_results}

        Please provide report generation instructions including:

        1. Report Structure: What should the report structure be?
           (e.g., executive summary, detailed analysis, appendices)

        2. Report Type: What type of report should be generated?
           (e.g., AP Aging, AR Aging, Collections, DSO Analysis)

        3. Content Sections: What sections should be included?
           (e.g., overview, key metrics, detailed breakdown, trends)

        4. Data Presentation: How should the data be presented?
           (e.g., tables, charts, bullet points, narratives)

        5. Key Insights: What key insights should be highlighted?
           (e.g., trends, anomalies, recommendations)

        6. Output Format: What output format should be used?
           (e.g., Excel, PDF, HTML, dashboard)

        Please provide detailed report generation instructions.
        """
    
    def _generate_report_content(self, calculation_results: Dict[str, Any], 
                                report_structure: str) -> Dict[str, Any]:
        """Generate report content based on structure"""
        try:
            # This would implement actual report generation logic
            # For now, return a structured response
            
            return {
                'calculation_results': calculation_results,
                'report_structure': report_structure,
                'report_type': self._extract_report_type(report_structure),
                'content_sections': self._extract_content_sections(report_structure),
                'data_presentation': self._extract_data_presentation(report_structure),
                'key_insights': self._extract_key_insights(report_structure),
                'output_format': self._extract_output_format(report_structure),
                'report_timestamp': self._get_current_timestamp(),
                'status': 'generated',
                'report_content': {}  # Would contain actual report content
            }
            
        except Exception as e:
            logger.error(f"Error generating report content: {str(e)}")
            return {
                'error': str(e),
                'calculation_results': calculation_results,
                'report_structure': report_structure
            }
    
    def _create_visualization_prompt(self, data: Dict[str, Any], 
                                    visualization_config: Dict[str, Any]) -> str:
        """Create prompt for visualization creation"""
        return f"""
        Create visualizations for the following data:

        Data:
        {data}

        Visualization Configuration:
        {visualization_config}

        Please provide visualization instructions including:

        1. Chart Types: What types of charts should be created?
           (e.g., bar charts, line charts, pie charts, scatter plots)

        2. Data Mapping: How should the data be mapped to visual elements?
           (e.g., x-axis, y-axis, colors, sizes)

        3. Chart Configuration: What configuration options should be applied?
           (e.g., titles, labels, legends, colors, styles)

        4. Interactive Elements: Should the visualizations be interactive?
           (e.g., tooltips, zoom, filters, drill-down)

        5. Layout: How should multiple visualizations be arranged?
           (e.g., grid, dashboard, report layout)

        6. Export Format: What format should the visualizations be exported in?
           (e.g., PNG, SVG, interactive HTML)

        Please provide detailed visualization creation instructions.
        """
    
    def _create_visualizations_from_instructions(self, data: Dict[str, Any], 
                                                 viz_instructions: str) -> Dict[str, Any]:
        """Create visualizations based on instructions"""
        try:
            # This would implement actual visualization creation logic
            # For now, return a structured response
            
            return {
                'data': data,
                'viz_instructions': viz_instructions,
                'chart_types': self._extract_chart_types(viz_instructions),
                'data_mapping': self._extract_data_mapping(viz_instructions),
                'chart_configuration': self._extract_chart_configuration(viz_instructions),
                'interactive_elements': self._extract_interactive_elements(viz_instructions),
                'layout': self._extract_layout(viz_instructions),
                'export_format': self._extract_export_format(viz_instructions),
                'visualization_timestamp': self._get_current_timestamp(),
                'status': 'created',
                'visualizations': {}  # Would contain actual visualizations
            }
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {str(e)}")
            return {
                'error': str(e),
                'data': data,
                'viz_instructions': viz_instructions
            }
    
    def _create_branding_prompt(self, report: Dict[str, Any], 
                               branding_config: Dict[str, Any]) -> str:
        """Create prompt for branding application"""
        return f"""
        Apply branding to the following report:

        Report:
        {report}

        Branding Configuration:
        {branding_config}

        Please provide branding application instructions including:

        1. Logo Placement: Where should the company logo be placed?
           (e.g., header, footer, cover page)

        2. Color Scheme: What colors should be applied?
           (e.g., primary colors, accent colors, background colors)

        3. Typography: What fonts and text styles should be used?
           (e.g., headings, body text, captions)

        4. Header/Footer: What should be included in headers and footers?
           (e.g., company name, report title, page numbers, dates)

        5. Watermarks: Should watermarks be applied?
           (e.g., company logo, confidential labels)

        6. Brand Consistency: How should brand consistency be maintained?
           (e.g., consistent colors, fonts, spacing)

        Please provide detailed branding application instructions.
        """
    
    def _apply_branding_to_report(self, report: Dict[str, Any], 
                                 branding_instructions: str) -> Dict[str, Any]:
        """Apply branding to report based on instructions"""
        try:
            # This would implement actual branding application logic
            # For now, return a structured response
            
            return {
                'report': report,
                'branding_instructions': branding_instructions,
                'logo_placement': self._extract_logo_placement(branding_instructions),
                'color_scheme': self._extract_color_scheme(branding_instructions),
                'typography': self._extract_typography(branding_instructions),
                'header_footer': self._extract_header_footer(branding_instructions),
                'watermarks': self._extract_watermarks(branding_instructions),
                'brand_consistency': self._extract_brand_consistency(branding_instructions),
                'branding_timestamp': self._get_current_timestamp(),
                'status': 'branded',
                'branded_report': {}  # Would contain actual branded report
            }
            
        except Exception as e:
            logger.error(f"Error applying branding to report: {str(e)}")
            return {
                'error': str(e),
                'report': report,
                'branding_instructions': branding_instructions
            }
    
    # Helper methods for extracting information
    def _extract_report_type(self, report_structure: str) -> str:
        """Extract report type from structure"""
        # Implementation would parse the report structure
        return "financial_analysis"
    
    def _extract_content_sections(self, report_structure: str) -> List[str]:
        """Extract content sections from structure"""
        # Implementation would parse the report structure
        return ["executive_summary", "detailed_analysis", "appendices"]
    
    def _extract_data_presentation(self, report_structure: str) -> Dict[str, Any]:
        """Extract data presentation from structure"""
        # Implementation would parse the report structure
        return {"tables": True, "charts": True, "narratives": True}
    
    def _extract_key_insights(self, report_structure: str) -> List[str]:
        """Extract key insights from structure"""
        # Implementation would parse the report structure
        return ["trends", "anomalies", "recommendations"]
    
    def _extract_output_format(self, report_structure: str) -> str:
        """Extract output format from structure"""
        # Implementation would parse the report structure
        return "excel"
    
    def _extract_chart_types(self, viz_instructions: str) -> List[str]:
        """Extract chart types from instructions"""
        # Implementation would parse the visualization instructions
        return ["bar_chart", "line_chart", "pie_chart"]
    
    def _extract_data_mapping(self, viz_instructions: str) -> Dict[str, Any]:
        """Extract data mapping from instructions"""
        # Implementation would parse the visualization instructions
        return {"x_axis": "date", "y_axis": "amount", "color": "category"}
    
    def _extract_chart_configuration(self, viz_instructions: str) -> Dict[str, Any]:
        """Extract chart configuration from instructions"""
        # Implementation would parse the visualization instructions
        return {"title": True, "labels": True, "legend": True}
    
    def _extract_interactive_elements(self, viz_instructions: str) -> Dict[str, Any]:
        """Extract interactive elements from instructions"""
        # Implementation would parse the visualization instructions
        return {"tooltips": True, "zoom": False, "filters": False}
    
    def _extract_layout(self, viz_instructions: str) -> str:
        """Extract layout from instructions"""
        # Implementation would parse the visualization instructions
        return "grid"
    
    def _extract_export_format(self, viz_instructions: str) -> str:
        """Extract export format from instructions"""
        # Implementation would parse the visualization instructions
        return "png"
    
    def _extract_logo_placement(self, branding_instructions: str) -> str:
        """Extract logo placement from instructions"""
        # Implementation would parse the branding instructions
        return "header"
    
    def _extract_color_scheme(self, branding_instructions: str) -> Dict[str, Any]:
        """Extract color scheme from instructions"""
        # Implementation would parse the branding instructions
        return {"primary": "#007bff", "secondary": "#6c757d"}
    
    def _extract_typography(self, branding_instructions: str) -> Dict[str, Any]:
        """Extract typography from instructions"""
        # Implementation would parse the branding instructions
        return {"headings": "Arial Bold", "body": "Arial Regular"}
    
    def _extract_header_footer(self, branding_instructions: str) -> Dict[str, Any]:
        """Extract header/footer from instructions"""
        # Implementation would parse the branding instructions
        return {"header": True, "footer": True, "page_numbers": True}
    
    def _extract_watermarks(self, branding_instructions: str) -> bool:
        """Extract watermarks from instructions"""
        # Implementation would parse the branding instructions
        return False
    
    def _extract_brand_consistency(self, branding_instructions: str) -> bool:
        """Extract brand consistency from instructions"""
        # Implementation would parse the branding instructions
        return True
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().isoformat()