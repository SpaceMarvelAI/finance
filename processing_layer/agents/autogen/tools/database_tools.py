"""
Database Tools
Specialized tools for database operations used by AutoGen agents
"""

from typing import Dict, Any, Optional, List, Union
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class DatabaseTools:
    """
    Database Tools
    
    Provides database operations for AutoGen agents including querying,
    data retrieval, and database management operations.
    """
    
    def __init__(self, database_manager):
        self.database_manager = database_manager
        
        # Initialize database tools
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize database tools"""
        try:
            # Import database manager if not already imported
            if not self.database_manager:
                from data_layer.database.database_manager import DatabaseManager
                self.database_manager = DatabaseManager()
            
            logger.info("Database tools initialized")
            
        except Exception as e:
            logger.error(f"Error initializing database tools: {str(e)}")
            raise
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a database query
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query execution result
        """
        try:
            # Execute query using database manager
            result = self.database_manager.execute_query(query, params)
            
            logger.info(f"Executed query: {query[:50]}...")
            
            return {
                'status': 'success',
                'query': query,
                'params': params,
                'result': result,
                'execution_time': self._get_execution_time(),
                'row_count': len(result) if isinstance(result, list) else 0
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                'status': 'error',
                'query': query,
                'params': params,
                'error': str(e)
            }
    
    def retrieve_data(self, table_name: str, filters: Optional[Dict[str, Any]] = None,
                     columns: Optional[List[str]] = None, 
                     limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieve data from a specific table
        
        Args:
            table_name: Name of the table to retrieve data from
            filters: Filter conditions for the query
            columns: Specific columns to retrieve
            limit: Maximum number of rows to retrieve
            
        Returns:
            Retrieved data
        """
        try:
            # Build query based on parameters
            query, params = self._build_select_query(table_name, filters, columns, limit)
            
            # Execute query
            result = self.database_manager.execute_query(query, params)
            
            logger.info(f"Retrieved {len(result)} records from {table_name}")
            
            return {
                'status': 'success',
                'table_name': table_name,
                'filters': filters,
                'columns': columns,
                'limit': limit,
                'data': result,
                'execution_time': self._get_execution_time(),
                'row_count': len(result)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving data from {table_name}: {str(e)}")
            return {
                'status': 'error',
                'table_name': table_name,
                'filters': filters,
                'columns': columns,
                'limit': limit,
                'error': str(e)
            }
    
    def insert_data(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert data into a table
        
        Args:
            table_name: Name of the table to insert data into
            data: Data to insert
            
        Returns:
            Insert operation result
        """
        try:
            # Build insert query
            query, params = self._build_insert_query(table_name, data)
            
            # Execute insert
            result = self.database_manager.execute_query(query, params)
            
            logger.info(f"Inserted data into {table_name}")
            
            return {
                'status': 'success',
                'table_name': table_name,
                'data': data,
                'insert_id': result,
                'execution_time': self._get_execution_time()
            }
            
        except Exception as e:
            logger.error(f"Error inserting data into {table_name}: {str(e)}")
            return {
                'status': 'error',
                'table_name': table_name,
                'data': data,
                'error': str(e)
            }
    
    def update_data(self, table_name: str, data: Dict[str, Any], 
                   filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update data in a table
        
        Args:
            table_name: Name of the table to update data in
            data: Data to update
            filters: Filter conditions for the update
            
        Returns:
            Update operation result
        """
        try:
            # Build update query
            query, params = self._build_update_query(table_name, data, filters)
            
            # Execute update
            result = self.database_manager.execute_query(query, params)
            
            logger.info(f"Updated data in {table_name}")
            
            return {
                'status': 'success',
                'table_name': table_name,
                'data': data,
                'filters': filters,
                'rows_affected': result,
                'execution_time': self._get_execution_time()
            }
            
        except Exception as e:
            logger.error(f"Error updating data in {table_name}: {str(e)}")
            return {
                'status': 'error',
                'table_name': table_name,
                'data': data,
                'filters': filters,
                'error': str(e)
            }
    
    def delete_data(self, table_name: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete data from a table
        
        Args:
            table_name: Name of the table to delete data from
            filters: Filter conditions for the delete
            
        Returns:
            Delete operation result
        """
        try:
            # Build delete query
            query, params = self._build_delete_query(table_name, filters)
            
            # Execute delete
            result = self.database_manager.execute_query(query, params)
            
            logger.info(f"Deleted data from {table_name}")
            
            return {
                'status': 'success',
                'table_name': table_name,
                'filters': filters,
                'rows_affected': result,
                'execution_time': self._get_execution_time()
            }
            
        except Exception as e:
            logger.error(f"Error deleting data from {table_name}: {str(e)}")
            return {
                'status': 'error',
                'table_name': table_name,
                'filters': filters,
                'error': str(e)
            }
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get the schema of a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table schema information
        """
        try:
            # Get table schema using database manager
            schema = self.database_manager.get_table_schema(table_name)
            
            logger.info(f"Retrieved schema for {table_name}")
            
            return {
                'status': 'success',
                'table_name': table_name,
                'schema': schema,
                'execution_time': self._get_execution_time()
            }
            
        except Exception as e:
            logger.error(f"Error getting schema for {table_name}: {str(e)}")
            return {
                'status': 'error',
                'table_name': table_name,
                'error': str(e)
            }
    
    def execute_aggregation(self, table_name: str, aggregations: Dict[str, str],
                           group_by: Optional[List[str]] = None,
                           filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute aggregation query
        
        Args:
            table_name: Name of the table
            aggregations: Dictionary of column aggregations (e.g., {'amount': 'SUM', 'count': 'COUNT'})
            group_by: Columns to group by
            filters: Filter conditions
            
        Returns:
            Aggregation results
        """
        try:
            # Build aggregation query
            query, params = self._build_aggregation_query(table_name, aggregations, group_by, filters)
            
            # Execute query
            result = self.database_manager.execute_query(query, params)
            
            logger.info(f"Executed aggregation on {table_name}")
            
            return {
                'status': 'success',
                'table_name': table_name,
                'aggregations': aggregations,
                'group_by': group_by,
                'filters': filters,
                'results': result,
                'execution_time': self._get_execution_time()
            }
            
        except Exception as e:
            logger.error(f"Error executing aggregation on {table_name}: {str(e)}")
            return {
                'status': 'error',
                'table_name': table_name,
                'aggregations': aggregations,
                'group_by': group_by,
                'filters': filters,
                'error': str(e)
            }
    
    def _build_select_query(self, table_name: str, filters: Optional[Dict[str, Any]] = None,
                           columns: Optional[List[str]] = None, 
                           limit: Optional[int] = None) -> tuple:
        """Build SELECT query"""
        try:
            # Build column list
            if columns:
                column_list = ', '.join(columns)
            else:
                column_list = '*'
            
            # Build WHERE clause
            where_clause = ""
            params = {}
            
            if filters:
                where_conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        where_conditions.append(f"{key} IN ({','.join(['?' for _ in value])})")
                        params[key] = value
                    else:
                        where_conditions.append(f"{key} = ?")
                        params[key] = value
                
                where_clause = f"WHERE {' AND '.join(where_conditions)}"
            
            # Build LIMIT clause
            limit_clause = f"LIMIT {limit}" if limit else ""
            
            # Build final query
            query = f"SELECT {column_list} FROM {table_name} {where_clause} {limit_clause}"
            
            return query, params
            
        except Exception as e:
            logger.error(f"Error building SELECT query: {str(e)}")
            raise
    
    def _build_insert_query(self, table_name: str, data: Dict[str, Any]) -> tuple:
        """Build INSERT query"""
        try:
            # Build column and value lists
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data.values()])
            
            # Build query
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            return query, list(data.values())
            
        except Exception as e:
            logger.error(f"Error building INSERT query: {str(e)}")
            raise
    
    def _build_update_query(self, table_name: str, data: Dict[str, Any], 
                           filters: Dict[str, Any]) -> tuple:
        """Build UPDATE query"""
        try:
            # Build SET clause
            set_clauses = []
            params = []
            
            for key, value in data.items():
                set_clauses.append(f"{key} = ?")
                params.append(value)
            
            set_clause = ', '.join(set_clauses)
            
            # Build WHERE clause
            where_conditions = []
            for key, value in filters.items():
                where_conditions.append(f"{key} = ?")
                params.append(value)
            
            where_clause = ' AND '.join(where_conditions)
            
            # Build query
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            
            return query, params
            
        except Exception as e:
            logger.error(f"Error building UPDATE query: {str(e)}")
            raise
    
    def _build_delete_query(self, table_name: str, filters: Dict[str, Any]) -> tuple:
        """Build DELETE query"""
        try:
            # Build WHERE clause
            where_conditions = []
            params = []
            
            for key, value in filters.items():
                where_conditions.append(f"{key} = ?")
                params.append(value)
            
            where_clause = ' AND '.join(where_conditions)
            
            # Build query
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            
            return query, params
            
        except Exception as e:
            logger.error(f"Error building DELETE query: {str(e)}")
            raise
    
    def _build_aggregation_query(self, table_name: str, aggregations: Dict[str, str],
                                group_by: Optional[List[str]] = None,
                                filters: Optional[Dict[str, Any]] = None) -> tuple:
        """Build aggregation query"""
        try:
            # Build SELECT clause with aggregations
            select_clauses = []
            for column, function in aggregations.items():
                select_clauses.append(f"{function}({column}) as {function.lower()}_{column}")
            
            select_clause = ', '.join(select_clauses)
            
            # Build WHERE clause
            where_clause = ""
            params = {}
            
            if filters:
                where_conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        where_conditions.append(f"{key} IN ({','.join(['?' for _ in value])})")
                        params[key] = value
                    else:
                        where_conditions.append(f"{key} = ?")
                        params[key] = value
                
                where_clause = f"WHERE {' AND '.join(where_conditions)}"
            
            # Build GROUP BY clause
            group_by_clause = ""
            if group_by:
                group_by_clause = f"GROUP BY {', '.join(group_by)}"
            
            # Build query
            query = f"SELECT {select_clause} FROM {table_name} {where_clause} {group_by_clause}"
            
            return query, params
            
        except Exception as e:
            logger.error(f"Error building aggregation query: {str(e)}")
            raise
    
    def _get_execution_time(self) -> float:
        """Get current execution time"""
        import time
        return time.time()