"""Database utility functions"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_table_info(table_name: str) -> Optional[Dict[str, Any]]:
    """Get information about a database table"""
    try:
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            logger.error(f"Invalid table name: {table_name}")
            return None
        
        db = SessionLocal()

        query = text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """)
        
        result = db.execute(query, {"table_name": table_name})
        columns = [
            {
                "name": row.column_name,
                "type": row.data_type,
                "nullable": row.is_nullable == "YES",
                "default": row.column_default
            }
            for row in result
        ]

        # Safe to use f-string after validation
        count_query = text(f"SELECT COUNT(*) as count FROM {table_name}")
        count_result = db.execute(count_query)
        row_count = count_result.scalar()
        
        db.close()
        
        return {
            "table_name": table_name,
            "columns": columns,
            "row_count": row_count
        }
        
    except Exception as e:
        logger.error(f"Error getting table info for {table_name}: {e}")
        return None


def get_database_stats() -> Dict[str, Any]:
    """Get general database statistics"""
    try:
        db = SessionLocal()

        tables_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        
        result = db.execute(tables_query)
        table_names = [row.table_name for row in result]

        table_stats = {}
        for table_name in table_names:
            try:
                # Validate table name to prevent SQL injection
                import re
                if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
                    logger.warning(f"Skipping invalid table name: {table_name}")
                    continue
                
                count_query = text(f"SELECT COUNT(*) as count FROM {table_name}")
                count_result = db.execute(count_query)
                table_stats[table_name] = count_result.scalar()
            except Exception as e:
                logger.warning(f"Could not get count for table {table_name}: {e}")
                table_stats[table_name] = "Error"
        
        db.close()
        
        return {
            "total_tables": len(table_names),
            "table_names": table_names,
            "table_stats": table_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {"error": str(e)}


def execute_raw_query(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Execute a raw SQL query and return results"""
    try:
        db = SessionLocal()
        
        result = db.execute(text(query), params or {})

        columns = result.keys()
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        
        db.close()
        
        return rows
        
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise