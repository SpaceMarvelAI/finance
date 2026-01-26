#!/usr/bin/env python3
"""
Custom Migration Script for Current Directory Structure
Reorganizes existing structure into three-layer architecture
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple

class CustomStructureMigrator:
    """Migrates from current structure to three-layer architecture"""
    
    def __init__(self, source_root: str, dry_run: bool = True):
        self.source_root = Path(source_root).resolve()
        self.dry_run = dry_run
        
        # Create new structure in a subfolder to avoid conflicts
        self.target_root = self.source_root / "restructured"
        
        self.created_dirs = set()
        self.moved_files = []
        self.skipped_files = []
        self.errors = []
    
    def get_file_mappings(self) -> List[Tuple[Path, str]]:
        """
        Map current files to their new locations in three-layer structure
        Returns: List of (source_path, target_relative_path) tuples
        """
        mappings = []
        
        # ========================================
        # LAYER 1: INTELLIGENCE LAYER
        # ========================================
        
        # Parsing - from agents/routing/
        mappings.extend([
            (self.source_root / 'agents/routing/domain_classifier.py', '1_intelligence_layer/parsing/'),
            (self.source_root / 'agents/routing/variable_extractor.py', '1_intelligence_layer/parsing/'),
            (self.source_root / 'agents/routing/enhanced_intent_parser.py', '1_intelligence_layer/parsing/'),
            (self.source_root / 'agents/orchestration/intent_parser_agent.py', '1_intelligence_layer/parsing/'),
        ])
        
        # Prompts - from core_system/
        mappings.extend([
            (self.source_root / 'core_system/prompt_library.py', '1_intelligence_layer/prompts/'),
            (self.source_root / 'core_system/router_prompt_integrator.py', '1_intelligence_layer/routing/'),
        ])
        
        # Orchestration - from agents/orchestration/
        mappings.extend([
            (self.source_root / 'agents/orchestration/master_orchestrator_agent.py', '1_intelligence_layer/orchestration/'),
            (self.source_root / 'agents/orchestration/enhanced_orchestrator.py', '1_intelligence_layer/orchestration/'),
            (self.source_root / 'agents/orchestration/workflow_planner_agent.py', '1_intelligence_layer/orchestration/'),
            (self.source_root / 'orchestrator.py', '1_intelligence_layer/orchestration/'),
            (self.source_root / 'core_system/financial_report_system.py', '1_intelligence_layer/orchestration/'),
        ])
        
        # ========================================
        # LAYER 2: PROCESSING LAYER
        # ========================================
        
        # Document Processing - from agents/core/
        mappings.extend([
            (self.source_root / 'agents/core/enhanced_ingestion_agent.py', '2_processing_layer/document_processing/'),
            (self.source_root / 'database/document_processor.py', '2_processing_layer/document_processing/'),
            (self.source_root / 'database/document_processing_service.py', '2_processing_layer/document_processing/'),
        ])
        
        # Parsers - from parsers/
        mappings.extend([
            (self.source_root / 'parsers/csv_parser.py', '2_processing_layer/document_processing/parsers/'),
            (self.source_root / 'parsers/universal_docling_parser.py', '2_processing_layer/document_processing/parsers/'),
            (self.source_root / 'parsers/parser_selector.py', '2_processing_layer/document_processing/parsers/'),
            (self.source_root / 'parsers/parsed_data_validator.py', '2_processing_layer/document_processing/parsers/'),
        ])
        
        # Agents Core - from agents/core/
        mappings.extend([
            (self.source_root / 'agents/core/base_agent.py', '2_processing_layer/agents/core/'),
            (self.source_root / 'agents/core/configurable_workflow_agent.py', '2_processing_layer/agents/core/'),
            (self.source_root / 'agents/core/rule_based_agent.py', '2_processing_layer/agents/core/'),
            (self.source_root / 'agents/core/universal_report_agent.py', '2_processing_layer/agents/core/'),
        ])
        
        # AP Agents - from agents/reports/ap/ and agents/specialized/
        mappings.extend([
            (self.source_root / 'agents/reports/ap/ap_register_agent.py', '2_processing_layer/agents/accounts_payable/'),
            (self.source_root / 'agents/reports/ap/ap_aging_agent.py', '2_processing_layer/agents/accounts_payable/'),
            (self.source_root / 'agents/reports/ap/ap_overdue_agent.py', '2_processing_layer/agents/accounts_payable/'),
            (self.source_root / 'agents/reports/ap/ap_duplicate_agent.py', '2_processing_layer/agents/accounts_payable/'),
        ])
        
        # AR Agents - from agents/reports/ar/
        mappings.extend([
            (self.source_root / 'agents/reports/ar/ar_register_agent.py', '2_processing_layer/agents/accounts_receivable/'),
            (self.source_root / 'agents/reports/ar/ar_aging_agent.py', '2_processing_layer/agents/accounts_receivable/'),
            (self.source_root / 'agents/reports/ar/ar_collection_agent.py', '2_processing_layer/agents/accounts_receivable/'),
            (self.source_root / 'agents/reports/ar/dso_agent.py', '2_processing_layer/agents/accounts_receivable/'),
        ])
        
        # Report Generation - from reports/
        mappings.extend([
            (self.source_root / 'reports/branded_excel_generator.py', '2_processing_layer/report_generation/'),
            (self.source_root / 'reports/report_generator.py', '2_processing_layer/report_generation/'),
            (self.source_root / 'reports/excel_generator.py', '2_processing_layer/report_generation/'),
            (self.source_root / 'reports/ap_aging_report.py', '2_processing_layer/report_generation/'),
            (self.source_root / 'reports/ap_invoice_register.py', '2_processing_layer/report_generation/'),
            (self.source_root / 'reports/ap_overdue_sla_report.py', '2_processing_layer/report_generation/'),
            (self.source_root / 'reports/ar_invoice_register.py', '2_processing_layer/report_generation/'),
        ])
        
        # Workflow Nodes - from nodes/
        mappings.extend([
            (self.source_root / 'nodes/base_node.py', '2_processing_layer/workflows/nodes/'),
            (self.source_root / 'nodes/data_nodes.py', '2_processing_layer/workflows/nodes/'),
            (self.source_root / 'nodes/calculation_nodes.py', '2_processing_layer/workflows/nodes/'),
            (self.source_root / 'nodes/aggregation_nodes.py', '2_processing_layer/workflows/nodes/'),
            (self.source_root / 'nodes/output_nodes.py', '2_processing_layer/workflows/nodes/'),
        ])
        
        # ========================================
        # LAYER 3: DATA LAYER
        # ========================================
        
        # Database - from core/database/
        mappings.extend([
            (self.source_root / 'database/database_manager.py', '3_data_layer/database/'),
            (self.source_root / 'core/database/session.py', '3_data_layer/database/'),
            (self.source_root / 'core/database/init_db.py', '3_data_layer/database/'),
            (self.source_root / 'init_user_settings_db.py', '3_data_layer/database/'),
        ])
        
        # Models - from core/models/
        mappings.extend([
            (self.source_root / 'core/models/database_models.py', '3_data_layer/models/'),
            (self.source_root / 'database/enhanced_database_schema.py', '3_data_layer/models/'),
        ])
        
        # Schemas - from core/schemas/
        mappings.extend([
            (self.source_root / 'core/schemas/canonical_schema.py', '3_data_layer/schemas/'),
        ])
        
        # Repositories - from core/database/
        mappings.extend([
            (self.source_root / 'core/database/document_repository.py', '3_data_layer/repositories/'),
        ])
        
        # ========================================
        # SHARED COMPONENTS
        # ========================================
        
        # Config - from config/
        mappings.extend([
            (self.source_root / 'config/settings.py', 'shared/config/'),
            (self.source_root / 'config/config_manager.py', 'shared/config/'),
            (self.source_root / 'config/logging_config.py', 'shared/config/'),
        ])
        
        # LLM - from llm/
        mappings.extend([
            (self.source_root / 'llm/groq_client.py', 'shared/llm/'),
        ])
        
        # Utils - from database/
        mappings.extend([
            (self.source_root / 'database/currency_converter.py', 'shared/utils/'),
            (self.source_root / 'database/live_exchange_rates.py', 'shared/utils/'),
            (self.source_root / 'database/migrate_currency.py', 'shared/utils/'),
        ])
        
        # Branding - from branding/
        mappings.extend([
            (self.source_root / 'branding/company_branding.py', 'shared/branding/'),
            (self.source_root / 'api_branding.py', 'shared/branding/'),
            (self.source_root / 'spacemarvel.png', 'shared/branding/assets/'),
        ])
        
        # Tools
        mappings.extend([
            (self.source_root / 'tools/mcp_financial_tools.py', 'shared/tools/'),
            (self.source_root / 'tools/user_settings.py', 'shared/tools/'),
        ])
        
        # Calculations
        mappings.extend([
            (self.source_root / 'calculations/calculation_engine.py', 'shared/calculations/'),
        ])
        
        # ========================================
        # TESTS
        # ========================================
        
        mappings.extend([
            (self.source_root / 'test_prompt.py', 'tests/unit/'),
            (self.source_root / 'test.py', 'tests/integration/'),
            (self.source_root / 'test_ingestion.py', 'tests/integration/'),
        ])
        
        # ========================================
        # ROOT FILES
        # ========================================
        
        mappings.extend([
            (self.source_root / 'api.py', ''),
            (self.source_root / 'demo_system.py', ''),
            (self.source_root / 'requirements.txt', ''),
        ])
        
        # Filter out files that don't exist
        existing_mappings = []
        for source_path, target_dir in mappings:
            if source_path.exists():
                existing_mappings.append((source_path, target_dir))
            else:
                self.skipped_files.append(str(source_path))
        
        return existing_mappings
    
    def create_directory_structure(self) -> None:
        """Create the complete directory structure"""
        
        directories = [
            # Intelligence Layer
            '1_intelligence_layer/parsing',
            '1_intelligence_layer/routing',
            '1_intelligence_layer/prompts',
            '1_intelligence_layer/orchestration',
            
            # Processing Layer
            '2_processing_layer/document_processing/parsers',
            '2_processing_layer/document_processing/services',
            '2_processing_layer/agents/core',
            '2_processing_layer/agents/accounts_payable',
            '2_processing_layer/agents/accounts_receivable',
            '2_processing_layer/agents/reconciliation',
            '2_processing_layer/agents/monitoring_analysis',
            '2_processing_layer/report_generation',
            '2_processing_layer/reconciliation',
            '2_processing_layer/workflows/nodes',
            '2_processing_layer/workflows/execution',
            
            # Data Layer
            '3_data_layer/database',
            '3_data_layer/models',
            '3_data_layer/schemas',
            '3_data_layer/repositories',
            
            # Shared
            'shared/config',
            'shared/llm',
            'shared/utils',
            'shared/branding/assets',
            'shared/tools',
            'shared/calculations',
            
            # Tests
            'tests/unit',
            'tests/integration',
            'tests/e2e',
            
            # Docs
            'docs/architecture',
        ]
        
        print("\n" + "="*70)
        print("CREATING DIRECTORY STRUCTURE")
        print("="*70)
        
        for directory in directories:
            dir_path = self.target_root / directory
            
            if self.dry_run:
                print(f"[DRY RUN] Would create: {dir_path.relative_to(self.source_root)}")
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"[CREATED] {dir_path.relative_to(self.source_root)}")
                
                # Create __init__.py
                init_file = dir_path / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
            
            self.created_dirs.add(str(dir_path))
    
    def migrate_files(self) -> None:
        """Migrate files to new structure"""
        
        print("\n" + "="*70)
        print("MIGRATING FILES")
        print("="*70)
        
        mappings = self.get_file_mappings()
        
        for source_path, target_dir in mappings:
            if target_dir:
                target_path = self.target_root / target_dir / source_path.name
            else:
                target_path = self.target_root / source_path.name
            
            if self.dry_run:
                print(f"[DRY RUN] Would copy:")
                print(f"  FROM: {source_path.relative_to(self.source_root)}")
                print(f"  TO:   {target_path.relative_to(self.source_root)}")
            else:
                try:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, target_path)
                    print(f"[COPIED] {source_path.name}")
                    print(f"  └─> {target_path.relative_to(self.source_root)}")
                    self.moved_files.append((str(source_path), str(target_path)))
                except Exception as e:
                    error_msg = f"Error copying {source_path.name}: {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    self.errors.append(error_msg)
    
    def generate_report(self) -> str:
        """Generate migration report"""
        
        report = "\n" + "="*70 + "\n"
        report += "MIGRATION REPORT\n"
        report += "="*70 + "\n\n"
        
        report += f"Mode: {'DRY RUN' if self.dry_run else 'ACTUAL MIGRATION'}\n"
        report += f"Source: {self.source_root}\n"
        report += f"Target: {self.target_root}\n\n"
        
        report += f"Directories Created: {len(self.created_dirs)}\n"
        report += f"Files Migrated: {len(self.moved_files)}\n"
        report += f"Files Skipped (not found): {len(self.skipped_files)}\n"
        report += f"Errors: {len(self.errors)}\n\n"
        
        if self.errors:
            report += "ERRORS:\n"
            for error in self.errors:
                report += f"  • {error}\n"
            report += "\n"
        
        if self.skipped_files and len(self.skipped_files) < 10:
            report += "SKIPPED FILES (not found):\n"
            for skipped in self.skipped_files:
                report += f"  • {Path(skipped).name}\n"
            report += "\n"
        
        report += "="*70 + "\n"
        
        if self.dry_run:
            report += "\nThis was a DRY RUN. No files were actually moved.\n"
            report += "Run with --execute flag to perform actual migration.\n"
        else:
            report += "\nMigration completed!\n"
            report += f"New structure created in: {self.target_root.relative_to(self.source_root)}/\n"
            report += "\nNext steps:\n"
            report += "1. Review the new structure\n"
            report += "2. Update import statements\n"
            report += "3. Test the system\n"
            report += "4. Replace old structure with new one\n"
        
        return report
    
    def execute(self) -> None:
        """Execute complete migration"""
        
        print("\n" + "="*70)
        print("FINANCIAL AUTOMATION - STRUCTURE MIGRATION")
        print("="*70)
        print(f"Current Directory: {self.source_root}")
        print(f"Target Directory: {self.target_root.relative_to(self.source_root)}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'ACTUAL MIGRATION'}")
        print("="*70)
        
        self.create_directory_structure()
        self.migrate_files()
        print(self.generate_report())


def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migrate financial automation to three-layer structure'
    )
    parser.add_argument(
        '--source',
        default='.',
        help='Source directory (default: current directory)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually perform migration (default is dry run)'
    )
    
    args = parser.parse_args()
    
    migrator = CustomStructureMigrator(
        source_root=args.source,
        dry_run=not args.execute
    )
    
    migrator.execute()


if __name__ == '__main__':
    main()