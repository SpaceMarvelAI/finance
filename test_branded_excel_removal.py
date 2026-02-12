, ar_collection_node#!/usr/bin/env python3
"""
Test script to verify BrandedExcelGenerator removal
"""

import sys
import os

def test_branded_excel_removal():
    """Test that BrandedExcelGenerator has been removed and nodes work"""
    
    print("Testing BrandedExcelGenerator removal...")
    
    # Test 1: Check that BrandedExcelGenerator file is gone
    branded_excel_path = "processing_layer/report_generation/branded_excel_generator.py"
    if os.path.exists(branded_excel_path):
        print(f"❌ FAIL: BrandedExcelGenerator still exists at {branded_excel_path}")
        return False
    else:
        print("✅ PASS: BrandedExcelGenerator file removed")
    
    # Test 2: Check that fixed nodes exist
    fixed_nodes = [
        "processing_layer/workflows/nodes/output_nodes/report_templates/ap_aging_node_fixed.py",
        "processing_layer/workflows/nodes/output_nodes/report_templates/ap_register_node_fixed.py", 
        "processing_layer/workflows/nodes/output_nodes/report_templates/ar_aging_node_fixed.py"
    ]
    
    for node_path in fixed_nodes:
        if os.path.exists(node_path):
            print(f"✅ PASS: Fixed node exists at {node_path}")
        else:
            print(f"❌ FAIL: Fixed node missing at {node_path}")
            return False
    
    # Test 3: Try importing the fixed nodes
    try:
        sys.path.insert(0, os.getcwd())
        
        # Test importing fixed nodes
        from processing_layer.workflows.nodes.output_nodes.report_templates.ap_aging_node_fixed import APAgingReportNode
        from processing_layer.workflows.nodes.output_nodes.report_templates.ap_register_node_fixed import APRegisterReportNode
        from processing_layer.workflows.nodes.output_nodes.report_templates.ar_aging_node_fixed import ARAgingReportNode
        
        print("✅ PASS: Fixed nodes can be imported successfully")
        
        # Test that they are registered
        from processing_layer.workflows.nodes.base_node import NodeRegistry
        registry = NodeRegistry.get_instance()
        
        if 'APAgingReportNode' in registry.nodes:
            print("✅ PASS: APAgingReportNode is registered")
        else:
            print("❌ FAIL: APAgingReportNode not registered")
            return False
            
        if 'APRegisterReportNode' in registry.nodes:
            print("✅ PASS: APRegisterReportNode is registered")
        else:
            print("❌ FAIL: APRegisterReportNode not registered")
            return False
            
        if 'ARAgingReportNode' in registry.nodes:
            print("✅ PASS: ARAgingReportNode is registered")
        else:
            print("❌ FAIL: ARAgingReportNode not registered")
            return False
        
    except ImportError as e:
        print(f"❌ FAIL: Cannot import fixed nodes: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error testing fixed nodes: {e}")
        return False
    
    # Test 4: Try importing output_nodes without BrandedExcelGenerator
    try:
        from processing_layer.workflows.nodes.output_nodes import ExcelGeneratorNode, GenericExcelGeneratorNode
        print("✅ PASS: Output nodes can be imported without BrandedExcelGenerator")
    except ImportError as e:
        print(f"❌ FAIL: Cannot import output nodes: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error importing output nodes: {e}")
        return False
    
    print("\n🎉 All tests passed! BrandedExcelGenerator has been successfully removed.")
    return True

if __name__ == "__main__":
    success = test_branded_excel_removal()
    sys.exit(0 if success else 1)