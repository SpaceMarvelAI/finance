"""
AutoGen API
REST API endpoints for AutoGen agent management and orchestration
"""

from typing import Dict, Any, Optional, List, Union
from flask import Flask, request, jsonify
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class AutoGenAPI:
    """
    AutoGen API
    
    Provides REST API endpoints for managing AutoGen agents,
    workflows, and orchestrations.
    """
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.app = Flask(__name__)
        
        # Initialize API routes
        self._initialize_routes()
    
    def _initialize_routes(self):
        """Initialize API routes"""
        
        @self.app.route('/api/autogen/agents', methods=['POST'])
        def create_agent():
            """Create a new agent"""
            try:
                data = request.get_json()
                agent_type = data.get('agent_type')
                agent_config = data.get('agent_config', {})
                
                if not agent_type:
                    return jsonify({
                        'status': 'error',
                        'message': 'Agent type is required'
                    }), 400
                
                agent_id = self.orchestrator.create_agent(agent_type, agent_config)
                
                if agent_id:
                    return jsonify({
                        'status': 'success',
                        'agent_id': agent_id
                    }), 201
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to create agent'
                    }), 500
                    
            except Exception as e:
                logger.error(f"Error creating agent: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/autogen/agents/<agent_id>', methods=['GET'])
        def get_agent(agent_id):
            """Get agent information"""
            try:
                result = self.orchestrator.get_agent_capabilities(agent_id)
                return jsonify(result)
                    
            except Exception as e:
                logger.error(f"Error getting agent info: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/autogen/agents/<agent_id>/task', methods=['POST'])
        def execute_agent_task(agent_id):
            """Execute a task with an agent"""
            try:
                data = request.get_json()
                task = data.get('task', {})
                
                result = self.orchestrator.execute_agent_task(agent_id, task)
                return jsonify(result)
                    
            except Exception as e:
                logger.error(f"Error executing agent task: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/autogen/workflows', methods=['POST'])
        def create_workflow():
            """Create a new workflow"""
            try:
                data = request.get_json()
                workflow_config = data.get('workflow_config', {})
                
                workflow_id = self.orchestrator.create_workflow(workflow_config)
                
                if workflow_id:
                    return jsonify({
                        'status': 'success',
                        'workflow_id': workflow_id
                    }), 201
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to create workflow'
                    }), 500
                    
            except Exception as e:
                logger.error(f"Error creating workflow: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/autogen/workflows/<workflow_id>', methods=['GET'])
        def get_workflow(workflow_id):
            """Get workflow information"""
            try:
                result = self.orchestrator.get_workflow_status(workflow_id)
                return jsonify(result)
                    
            except Exception as e:
                logger.error(f"Error getting workflow info: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/autogen/workflows/<workflow_id>/execute', methods=['POST'])
        def execute_workflow(workflow_id):
            """Execute a workflow"""
            try:
                data = request.get_json()
                input_data = data.get('input_data', {})
                
                result = self.orchestrator.execute_workflow(workflow_id, input_data)
                return jsonify(result)
                    
            except Exception as e:
                logger.error(f"Error executing workflow: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/autogen/status', methods=['GET'])
        def get_status():
            """Get orchestrator status"""
            try:
                result = self.orchestrator.get_orchestrator_status()
                return jsonify(result)
                    
            except Exception as e:
                logger.error(f"Error getting orchestrator status: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/autogen/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'service': 'autogen-api',
                'timestamp': self._get_current_timestamp()
            })
    
    def run(self, host='0.0.0.0', port=5001, debug=False):
        """Run the API server"""
        try:
            logger.info(f"Starting AutoGen API on {host}:{port}")
            self.app.run(host=host, port=port, debug=debug)
        except Exception as e:
            logger.error(f"Error starting AutoGen API: {str(e)}")
            raise
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().isoformat()