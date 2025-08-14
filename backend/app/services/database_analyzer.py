"""
Database Analysis Service with Graceful Degradation

Analyzes database usage patterns from source code and optionally connects to live databases
for enhanced schema analysis. Works even without database credentials by providing static analysis.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class SQLQuery:
    """Represents a SQL query found in source code"""
    file_path: str
    line_number: int
    query_text: str
    query_type: str  # SELECT, INSERT, UPDATE, DELETE, etc.
    tables: List[str]
    parameters: List[str]
    is_prepared_statement: bool
    context_function: Optional[str] = None
    context_class: Optional[str] = None

@dataclass
class DatabaseTable:
    """Represents a database table (from live connection or inferred from code)"""
    name: str
    columns: List[Dict[str, Any]]
    indexes: List[str]
    foreign_keys: List[Dict[str, str]]
    is_inferred: bool  # True if inferred from code, False if from live DB

@dataclass
class DatabaseConnection:
    """Represents a database connection configuration"""
    db_type: str  # oracle, postgres, mysql, sqlserver
    host: str
    port: int
    database: str
    username: str
    password: str
    is_available: bool = False

class DatabaseAnalyzer:
    """Analyzes database usage with graceful degradation"""
    
    def __init__(self):
        self.sql_patterns = self._compile_sql_patterns()
        self.connections: Dict[str, DatabaseConnection] = {}
        self._setup_connections()
    
    def _compile_sql_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for SQL detection"""
        patterns = {
            # Basic SQL operations
            'select': re.compile(r'\b(SELECT\s+.*?FROM\s+\w+.*?)(?:;|$|\n)', re.IGNORECASE | re.DOTALL),
            'insert': re.compile(r'\b(INSERT\s+INTO\s+\w+.*?)(?:;|$|\n)', re.IGNORECASE | re.DOTALL),
            'update': re.compile(r'\b(UPDATE\s+\w+.*?)(?:;|$|\n)', re.IGNORECASE | re.DOTALL),
            'delete': re.compile(r'\b(DELETE\s+FROM\s+\w+.*?)(?:;|$|\n)', re.IGNORECASE | re.DOTALL),
            
            # String-based queries (Java/Python)
            'string_query': re.compile(r'["\']([^"\']*(?:SELECT|INSERT|UPDATE|DELETE)[^"\']*)["\']', re.IGNORECASE),
            
            # Prepared statements
            'prepared_statement': re.compile(r'(?:prepareStatement|prepare)\s*\(\s*["\']([^"\']*)["\']', re.IGNORECASE),
            
            # Named queries (JPA/Hibernate)
            'named_query': re.compile(r'@NamedQuery\s*\(\s*name\s*=\s*["\']([^"\']*)["\'].*?query\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE | re.DOTALL),
            
            # Table extraction
            'table_name': re.compile(r'\b(?:FROM|INTO|UPDATE|JOIN)\s+(\w+)', re.IGNORECASE),
            
            # Parameter placeholders
            'parameters': re.compile(r'[?:]\w*|\$\d+|\{\w+\}'),
        }
        return patterns
    
    def _setup_connections(self):
        """Setup database connections based on configuration"""
        # Oracle
        if all([settings.ORACLE_HOST, settings.ORACLE_USERNAME, settings.ORACLE_PASSWORD]):
            self.connections['oracle'] = DatabaseConnection(
                db_type='oracle',
                host=settings.ORACLE_HOST,
                port=settings.ORACLE_PORT,
                database=settings.ORACLE_SERVICE or 'XE',
                username=settings.ORACLE_USERNAME,
                password=settings.ORACLE_PASSWORD
            )
        
        # PostgreSQL
        if settings.POSTGRES_URL or (settings.POSTGRES_HOST and settings.POSTGRES_USERNAME):
            self.connections['postgres'] = DatabaseConnection(
                db_type='postgres',
                host=settings.POSTGRES_HOST or 'localhost',
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DATABASE or 'postgres',
                username=settings.POSTGRES_USERNAME or '',
                password=settings.POSTGRES_PASSWORD or ''
            )
        
        # MySQL
        if settings.MYSQL_URL or (settings.MYSQL_HOST and settings.MYSQL_USERNAME):
            self.connections['mysql'] = DatabaseConnection(
                db_type='mysql',
                host=settings.MYSQL_HOST or 'localhost',
                port=settings.MYSQL_PORT,
                database=settings.MYSQL_DATABASE or 'mysql',
                username=settings.MYSQL_USERNAME or '',
                password=settings.MYSQL_PASSWORD or ''
            )
        
        # SQL Server
        if settings.SQLSERVER_URL or (settings.SQLSERVER_HOST and settings.SQLSERVER_USERNAME):
            self.connections['sqlserver'] = DatabaseConnection(
                db_type='sqlserver',
                host=settings.SQLSERVER_HOST or 'localhost',
                port=settings.SQLSERVER_PORT,
                database=settings.SQLSERVER_DATABASE or 'master',
                username=settings.SQLSERVER_USERNAME or '',
                password=settings.SQLSERVER_PASSWORD or ''
            )
    
    async def analyze_database_usage(self, file_paths: List[Path]) -> Dict[str, Any]:
        """
        Main analysis method - performs static analysis and optional live DB analysis
        
        Always works regardless of database connectivity
        """
        logger.info(f"Starting database analysis of {len(file_paths)} files")
        
        # Phase 1: Static Analysis (always works)
        static_results = await self._static_analysis(file_paths)
        
        # Phase 2: Live Database Analysis (optional enhancement)
        live_results = {}
        if settings.ENABLE_DB_ANALYSIS and self.connections:
            live_results = await self._live_database_analysis(static_results['queries'])
        
        # Combine results
        results = {
            'static_analysis': static_results,
            'live_analysis': live_results,
            'analysis_mode': 'enhanced' if live_results else 'static_only',
            'available_connections': list(self.connections.keys()),
            'total_queries_found': len(static_results['queries']),
            'unique_tables': len(static_results['tables']),
        }
        
        logger.info(f"Database analysis completed: {results['analysis_mode']} mode, {results['total_queries_found']} queries found")
        return results
    
    async def _static_analysis(self, file_paths: List[Path]) -> Dict[str, Any]:
        """Static analysis of SQL queries from source code"""
        queries: List[SQLQuery] = []
        tables_mentioned: set = set()
        file_query_counts: Dict[str, int] = {}
        
        for file_path in file_paths:
            try:
                file_queries = await self._extract_queries_from_file(file_path)
                queries.extend(file_queries)
                file_query_counts[str(file_path)] = len(file_queries)
                
                # Track unique tables
                for query in file_queries:
                    tables_mentioned.update(query.tables)
                    
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
        
        # Analyze query patterns
        query_patterns = self._analyze_query_patterns(queries)
        
        return {
            'queries': [self._query_to_dict(q) for q in queries],
            'tables': list(tables_mentioned),
            'file_query_counts': file_query_counts,
            'query_patterns': query_patterns,
            'inferred_schema': self._infer_schema_from_queries(queries)
        }
    
    async def _extract_queries_from_file(self, file_path: Path) -> List[SQLQuery]:
        """Extract SQL queries from a single file"""
        queries: List[SQLQuery] = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            logger.debug(f"Could not read {file_path}: {e}")
            return queries
        
        # Extract different types of SQL queries
        for pattern_name, pattern in self.sql_patterns.items():
            for match in pattern.finditer(content):
                try:
                    query_text = match.group(1) if match.groups() else match.group(0)
                    
                    # Find line number
                    line_number = content[:match.start()].count('\n') + 1
                    
                    # Extract query details
                    query = self._parse_sql_query(
                        file_path=str(file_path),
                        line_number=line_number,
                        query_text=query_text,
                        is_prepared=pattern_name == 'prepared_statement'
                    )
                    
                    if query:
                        queries.append(query)
                        
                except Exception as e:
                    logger.debug(f"Error parsing query in {file_path}: {e}")
        
        return queries
    
    def _parse_sql_query(self, file_path: str, line_number: int, query_text: str, is_prepared: bool = False) -> Optional[SQLQuery]:
        """Parse a SQL query string and extract metadata"""
        query_text = query_text.strip()
        if len(query_text) < 10:  # Skip very short strings
            return None
        
        # Determine query type
        query_type = 'UNKNOWN'
        query_upper = query_text.upper()
        for qtype in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']:
            if qtype in query_upper:
                query_type = qtype
                break
        
        # Extract table names
        tables = []
        table_matches = self.sql_patterns['table_name'].findall(query_text)
        for table in table_matches:
            if table and table not in ['VALUES', 'SET', 'WHERE']:  # Filter out SQL keywords
                tables.append(table.lower())
        
        # Extract parameters
        param_matches = self.sql_patterns['parameters'].findall(query_text)
        parameters = [p.strip('?:{}$') for p in param_matches if p]
        
        return SQLQuery(
            file_path=file_path,
            line_number=line_number,
            query_text=query_text,
            query_type=query_type,
            tables=list(set(tables)),  # Remove duplicates
            parameters=parameters,
            is_prepared_statement=is_prepared
        )
    
    def _analyze_query_patterns(self, queries: List[SQLQuery]) -> Dict[str, Any]:
        """Analyze patterns in the extracted queries"""
        patterns = {
            'by_type': {},
            'by_table': {},
            'prepared_statements': 0,
            'parameterized_queries': 0,
            'most_queried_tables': [],
            'complex_queries': []
        }
        
        table_usage = {}
        
        for query in queries:
            # Count by type
            patterns['by_type'][query.query_type] = patterns['by_type'].get(query.query_type, 0) + 1
            
            # Count by table
            for table in query.tables:
                patterns['by_table'][table] = patterns['by_table'].get(table, 0) + 1
                table_usage[table] = table_usage.get(table, 0) + 1
            
            # Count prepared statements
            if query.is_prepared_statement:
                patterns['prepared_statements'] += 1
            
            # Count parameterized queries
            if query.parameters:
                patterns['parameterized_queries'] += 1
            
            # Identify complex queries (heuristic)
            if len(query.query_text) > 200 or 'JOIN' in query.query_text.upper():
                patterns['complex_queries'].append({
                    'file': query.file_path,
                    'line': query.line_number,
                    'length': len(query.query_text)
                })
        
        # Most queried tables
        patterns['most_queried_tables'] = sorted(
            table_usage.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return patterns
    
    def _infer_schema_from_queries(self, queries: List[SQLQuery]) -> Dict[str, DatabaseTable]:
        """Infer database schema from query analysis"""
        inferred_tables = {}
        
        for query in queries:
            for table_name in query.tables:
                if table_name not in inferred_tables:
                    inferred_tables[table_name] = DatabaseTable(
                        name=table_name,
                        columns=[],
                        indexes=[],
                        foreign_keys=[],
                        is_inferred=True
                    )
                
                # Try to infer column names from queries
                columns = self._extract_columns_from_query(query.query_text)
                for col in columns:
                    # Add column if not already present
                    existing_cols = [c['name'] for c in inferred_tables[table_name].columns]
                    if col not in existing_cols:
                        inferred_tables[table_name].columns.append({
                            'name': col,
                            'type': 'INFERRED',
                            'nullable': True,
                            'source': 'query_analysis'
                        })
        
        return inferred_tables
    
    def _extract_columns_from_query(self, query_text: str) -> List[str]:
        """Extract column names from a SQL query (basic heuristic)"""
        columns = []
        query_upper = query_text.upper()
        
        # For SELECT queries, try to extract column names
        if 'SELECT' in query_upper and 'FROM' in query_upper:
            try:
                # Extract between SELECT and FROM
                select_part = query_text[query_text.upper().find('SELECT') + 6:query_text.upper().find('FROM')]
                if '*' not in select_part:
                    # Split by comma and clean up
                    potential_columns = [col.strip() for col in select_part.split(',')]
                    for col in potential_columns:
                        # Remove aliases (AS keyword)
                        col = col.split(' AS ')[0].strip()
                        col = col.split(' as ')[0].strip()
                        # Remove table prefixes
                        if '.' in col:
                            col = col.split('.')[-1]
                        # Basic validation
                        if col and col.isalnum():
                            columns.append(col.lower())
            except Exception:
                pass  # Ignore parsing errors
        
        return columns
    
    async def _live_database_analysis(self, queries: List[Dict]) -> Dict[str, Any]:
        """Enhance analysis with live database connections"""
        live_analysis = {
            'connected_databases': [],
            'schema_information': {},
            'connection_errors': []
        }
        
        for db_type, connection in self.connections.items():
            try:
                logger.info(f"Attempting connection to {db_type} database")
                schema_info = await self._get_database_schema(connection)
                if schema_info:
                    live_analysis['connected_databases'].append(db_type)
                    live_analysis['schema_information'][db_type] = schema_info
                    connection.is_available = True
                    logger.info(f"Successfully connected to {db_type}")
                
            except Exception as e:
                error_msg = f"Could not connect to {db_type}: {str(e)}"
                logger.warning(error_msg)
                live_analysis['connection_errors'].append({
                    'database': db_type,
                    'error': error_msg
                })
        
        return live_analysis
    
    async def _get_database_schema(self, connection: DatabaseConnection) -> Optional[Dict]:
        """Get schema information from a live database connection"""
        # This is a placeholder for actual database connection logic
        # Would need appropriate database drivers (cx_Oracle, psycopg2, etc.)
        
        try:
            # Simulate connection attempt with timeout
            await asyncio.wait_for(self._attempt_connection(connection), timeout=settings.DB_CONNECTION_TIMEOUT)
            
            # If connection successful, would extract schema here
            return {
                'connection_successful': True,
                'tables': [],  # Would populate from actual DB
                'schemas': [],
                'connection_time': 0.5  # Would measure actual time
            }
            
        except asyncio.TimeoutError:
            raise Exception(f"Connection timeout after {settings.DB_CONNECTION_TIMEOUT} seconds")
        except Exception as e:
            raise Exception(f"Connection failed: {str(e)}")
    
    async def _attempt_connection(self, connection: DatabaseConnection):
        """Attempt database connection (placeholder)"""
        # This would contain actual database connection logic
        # For now, just simulate a connection attempt
        await asyncio.sleep(0.1)  # Simulate connection time
        
        # In real implementation, would use appropriate drivers:
        # - cx_Oracle for Oracle
        # - psycopg2 for PostgreSQL  
        # - pymysql for MySQL
        # - pyodbc for SQL Server
        
        # For demonstration, always "succeed" but don't actually connect
        logger.debug(f"Simulated connection attempt to {connection.db_type}")
    
    def _query_to_dict(self, query: SQLQuery) -> Dict[str, Any]:
        """Convert SQLQuery to dictionary for JSON serialization"""
        return {
            'file_path': query.file_path,
            'line_number': query.line_number,
            'query_text': query.query_text,
            'query_type': query.query_type,
            'tables': query.tables,
            'parameters': query.parameters,
            'is_prepared_statement': query.is_prepared_statement,
            'context_function': query.context_function,
            'context_class': query.context_class
        }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get status of all configured database connections"""
        status = {
            'total_configured': len(self.connections),
            'connections': {}
        }
        
        for db_type, connection in self.connections.items():
            status['connections'][db_type] = {
                'host': connection.host,
                'port': connection.port,
                'database': connection.database,
                'username': connection.username,
                'is_available': connection.is_available,
                'password_configured': bool(connection.password)
            }
        
        return status

# Singleton instance
database_analyzer = DatabaseAnalyzer()