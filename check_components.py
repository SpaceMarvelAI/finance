"""
Diagnostic Script - Check What's Available
Run this to see what components are missing
"""

import sys
import os

print("=" * 80)
print("COMPONENT AVAILABILITY CHECK")
print("=" * 80)
print()

# Check Python path
print("Python Path:")
for p in sys.path[:5]:
    print(f"  {p}")
print()

# Check current directory
print(f"Current Directory: {os.getcwd()}")
print()

# Try importing each component
components = {
    'database_manager': 'data_layer.database.database_manager',
    'document_processing': 'data_layer.processing.document_processing_service',
    'workflow_planner': 'intelligence_layer.orchestration.workflow_planner_agent',
    'router_integrator': 'intelligence_layer.orchestration.router_prompt_integrator',
    'configurable_workflow': 'processing_layer.agents.core.configurable_workflow_agent',
    'node_registry': 'processing_layer.workflows.nodes',
}

print("Component Check:")
print()

available = []
missing = []

for name, module_path in components.items():
    try:
        parts = module_path.split('.')
        if len(parts) > 1:
            # Try importing the module
            exec(f"from {'.'.join(parts[:-1])} import {parts[-1]}")
        else:
            exec(f"import {module_path}")
        print(f"   {name}: {module_path}")
        available.append(name)
    except ImportError as e:
        print(f"   {name}: {module_path}")
        print(f"      Error: {e}")
        missing.append((name, module_path, str(e)))
print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print(f"Available: {len(available)}/{len(components)}")
print(f"Missing: {len(missing)}/{len(components)}")
print()

if missing:
    print("Missing Components:")
    for name, module, error in missing:
        print(f"  - {name} ({module})")
    print()
    print("SOLUTIONS:")
    print()
    print("1. Check if directories exist:")
    dirs_to_check = [
        'data_layer/database',
        'data_layer/processing',
        'intelligence_layer/orchestration',
        'processing_layer/agents/core',
        'restructured/processing_layer/workflows/nodes'
    ]
    for d in dirs_to_check:
        exists = os.path.exists(d)
        status = "" if exists else ""
        print(f"   {status} {d}")
    print()
    
    print("2. Make sure __init__.py files exist in:")
    init_files = [
        'data_layer/__init__.py',
        'data_layer/database/__init__.py',
        'data_layer/processing/__init__.py',
        'intelligence_layer/__init__.py',
        'intelligence_layer/orchestration/__init__.py',
        'processing_layer/__init__.py',
        'processing_layer/agents/__init__.py',
        'processing_layer/agents/core/__init__.py',
    ]
    for f in init_files:
        exists = os.path.exists(f)
        status = "" if exists else ""
        print(f"   {status} {f}")
    print()
    
    print("3. Check PYTHONPATH:")
    print(f"   Current: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"   Should include: {os.getcwd()}")
    print()
    
else:
    print(" All components available!")
    print()
    print("You can now run:")
    print("  python production_api.py")
    print()

print("=" * 80)