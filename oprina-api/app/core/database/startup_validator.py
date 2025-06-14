"""
Database startup validator for Oprina API.

This module runs validation checks when the application starts up
to ensure the database schema is properly configured.
"""

import asyncio
from typing import Dict, List
from supabase import Client
import structlog

from app.core.database.schema_validator import SchemaValidator, validate_database_schema
from app.core.database.connection import get_database

logger = structlog.get_logger(__name__)


class StartupValidator:
    """Validates database setup during application startup."""
    
    def __init__(self, db_client: Client):
        self.db = db_client
        self.validator = SchemaValidator(db_client)
    
    async def run_startup_checks(self) -> Dict[str, any]:
        """Run comprehensive startup validation checks."""
        logger.info("Starting database validation checks...")
        
        results = {
            "startup_successful": True,
            "schema_validation": None,
            "migration_status": None,
            "recommendations": [],
            "warnings": [],
            "errors": []
        }
        
        try:
            # 1. Basic connectivity test
            await self._test_database_connectivity()
            logger.info("✅ Database connectivity: OK")
            
            # 2. Schema validation
            schema_results = await self.validator.validate_schema()
            results["schema_validation"] = schema_results
            
            if schema_results["valid"]:
                logger.info("✅ Database schema: OK")
            else:
                logger.warning("⚠️ Database schema issues detected")
                results["warnings"].append("Database schema validation failed")
                
                if schema_results["missing_tables"]:
                    results["recommendations"].append(
                        f"Missing tables: {', '.join(schema_results['missing_tables'])}. Run migrations."
                    )
            
            # 3. Migration status check
            migration_status = schema_results.get("migration_status")
            results["migration_status"] = migration_status
            
            if migration_status:
                logger.info(f"✅ Migration system: Active (version: {migration_status.get('current_version')})")
            else:
                logger.warning("⚠️ Migration tracking system not found")
                results["warnings"].append("Migration tracking system not available")
            
            # 4. Repository validation
            await self._validate_repositories()
            logger.info("✅ Repository validation: OK")
            
            if results["warnings"] or not schema_results["valid"]:
                results["startup_successful"] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Startup validation failed: {e}")
            results["startup_successful"] = False
            results["errors"].append(f"Validation error: {str(e)}")
            return results
    
    async def _test_database_connectivity(self) -> None:
        """Test basic database connectivity."""
        try:
            response = self.db.table("users").select("id").limit(1).execute()
        except Exception as e:
            raise Exception(f"Database connectivity test failed: {e}")
    
    async def _validate_repositories(self) -> None:
        """Validate that repositories can be instantiated correctly."""
        try:
            from app.core.database.repositories.user_repository import UserRepository
            from app.core.database.repositories.session_repository import SessionRepository
            from app.core.database.repositories.message_repository import MessageRepository
            
            # Test repository instantiation
            user_repo = UserRepository(self.db)
            session_repo = SessionRepository(self.db)
            message_repo = MessageRepository(self.db)
            
            # Verify table names are correct
            expected_tables = {
                "users": user_repo.table_name,
                "sessions": session_repo.table_name,
                "messages": message_repo.table_name,
            }
            
            for expected, actual in expected_tables.items():
                if expected != actual:
                    raise Exception(f"Repository table mismatch: expected '{expected}', got '{actual}'")
            
        except Exception as e:
            raise Exception(f"Repository validation failed: {e}")


async def run_startup_validation(db_client: Client = None) -> Dict[str, any]:
    """Convenience function to run startup validation."""
    if db_client is None:
        db_client = await get_database()
    
    validator = StartupValidator(db_client)
    return await validator.run_startup_checks()


if __name__ == "__main__":
    asyncio.run(run_startup_validation()) 