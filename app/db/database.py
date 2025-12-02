import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)

# Optimized database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    # Connection pool settings
    poolclass=QueuePool,
    pool_size=20,  # Number of connections to maintain
    max_overflow=30,  # Additional connections beyond pool_size
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Timeout for getting connection from pool
    # Query optimization settings
    echo=False,  # Set to True for SQL debugging
    echo_pool=False,  # Set to True for pool debugging
    # Connection settings
    connect_args=(
        {
            "options": "-c timezone=utc",
            "application_name": "voice_collection_platform",
            "connect_timeout": 10,
        }
        if "postgresql" in settings.DATABASE_URL
        else {}
    ),
)


# Add connection pool event listeners for monitoring
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)."""
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkout for monitoring."""
    logger.debug("Connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection checkin for monitoring."""
    logger.debug("Connection checked in to pool")


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Keep objects accessible after commit
)

Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables in the database"""
    Base.metadata.drop_all(bind=engine)


def get_connection_pool_status():
    """Get current connection pool status for monitoring."""
    try:
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "total_connections": pool.size() + pool.overflow(),
            "available_connections": pool.checkedin(),
            "pool_status": "healthy" if pool.checkedin() > 0 else "warning",
        }
    except Exception as e:
        logger.error(f"Error getting connection pool status: {e}")
        return {"error": str(e)}


def optimize_database_settings():
    """Apply database-specific optimizations."""
    try:
        with engine.connect() as conn:
            if "postgresql" in settings.DATABASE_URL:
                # PostgreSQL optimizations
                conn.execute("SET shared_preload_libraries = 'pg_stat_statements'")
                conn.execute("SET log_statement = 'none'")  # Reduce logging overhead
                conn.execute(
                    "SET log_min_duration_statement = 1000"
                )  # Log slow queries
                conn.execute("SET work_mem = '256MB'")
                conn.execute("SET maintenance_work_mem = '512MB'")
                conn.execute("SET effective_cache_size = '2GB'")
                conn.execute("SET random_page_cost = 1.1")
                logger.info("Applied PostgreSQL performance optimizations")

        return True
    except Exception as e:
        logger.warning(f"Could not apply database optimizations: {e}")
        return False
