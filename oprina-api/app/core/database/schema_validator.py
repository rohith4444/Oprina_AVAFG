"""
Database schema validator for Oprina API.

This module validates that the database schema created by migrations
matches what the repository classes expect to work with.
"""

from typing import Dict, List, Set, Optional
from supabase import Client
import structlog

logger = structlog.get_logger(__name__)


class SchemaValidator:
    """Validates database schema against repository expectations."""
    
    def __init__(self, db_client: Client):
        self.db = db_client
        
    # Expected schema based on migration files
    EXPECTED_TABLES = {
        # Core application tables (from 001_initial_schema.sql)
        "users": {
            "required_columns": {
                "id", "email", "password_hash", "display_name", "avatar_url",
                "preferences", "timezone", "language", "is_active", "is_verified",
                "email_verified_at", "has_google_oauth", "has_microsoft_oauth",
                "last_login_at", "last_activity_at", "created_at", "updated_at"
            },
            "indexes": {
                "idx_users_email", "idx_users_active", "idx_users_created_at"
            }
        },
        "sessions": {
            "required_columns": {
                "id", "user_id", "session_token", "session_name", "title",
                "description", "context_data", "agent_type", "agent_config",
                "message_count", "total_tokens_used", "estimated_cost",
                "started_at", "ended_at", "last_activity_at", "status",
                "is_archived", "created_at", "updated_at"
            },
            "indexes": {
                "idx_sessions_user_id", "idx_sessions_token", "idx_sessions_status",
                "idx_sessions_activity", "idx_sessions_created_at"
            }
        },
        "messages": {
            "required_columns": {
                "id", "session_id", "role", "content", "content_type",
                "message_index", "parent_message_id", "agent_response_data",
                "processing_time_ms", "prompt_tokens", "completion_tokens",
                "total_tokens", "estimated_cost", "has_voice_response",
                "voice_response_url", "has_avatar_response", "avatar_session_id",
                "status", "error_message", "created_at", "updated_at"
            },
            "indexes": {
                "idx_messages_session_id", "idx_messages_role", "idx_messages_index",
                "idx_messages_created_at", "idx_messages_parent"
            }
        },
        "user_tokens": {
            "required_columns": {
                "id", "user_id", "token_type", "token_hash", "token_data",
                "expires_at", "used_at", "is_revoked", "created_at", "updated_at"
            },
            "indexes": {
                "idx_user_tokens_user_id", "idx_user_tokens_type",
                "idx_user_tokens_expires", "idx_user_tokens_hash"
            }
        },
        "user_activities": {
            "required_columns": {
                "id", "user_id", "activity_type", "activity_data", "session_id",
                "ip_address", "user_agent", "created_at"
            },
            "indexes": {
                "idx_user_activities_user_id", "idx_user_activities_type",
                "idx_user_activities_session", "idx_user_activities_created_at"
            }
        },
        
        # OAuth integration tables (from 003_add_service_tokens.sql)
        "service_tokens": {
            "required_columns": {
                "id", "user_id", "service_type", "service_name",
                "access_token_encrypted", "refresh_token_encrypted", "id_token_encrypted",
                "token_type", "scope", "expires_at", "provider", "provider_user_id",
                "provider_email", "is_active", "is_revoked", "revoked_at",
                "revoked_reason", "last_used_at", "use_count", "token_metadata",
                "created_at", "updated_at"
            },
            "indexes": {
                "idx_service_tokens_user_id", "idx_service_tokens_service_type",
                "idx_service_tokens_provider", "idx_service_tokens_active"
            }
        },
        "token_refresh_logs": {
            "required_columns": {
                "id", "service_token_id", "refresh_type", "refresh_status",
                "started_at", "completed_at", "previous_expires_at", "new_expires_at",
                "error_message", "retry_count", "refresh_metadata", "created_at"
            },
            "indexes": {
                "idx_token_refresh_logs_service_token_id", "idx_token_refresh_logs_status",
                "idx_token_refresh_logs_created_at"
            }
        },
        
        # Avatar usage tables (from 002_add_avatar_usage.sql)
        "avatar_usage_records": {
            "required_columns": {
                "id", "user_id", "session_id", "avatar_session_id", "avatar_name",
                "session_started_at", "session_ended_at", "duration_seconds",
                "words_spoken", "messages_count", "estimated_cost", "billing_period",
                "status", "error_message", "created_at", "updated_at"
            },
            "indexes": {
                "idx_avatar_usage_user_id", "idx_avatar_usage_session_id",
                "idx_avatar_usage_avatar_session_id", "idx_avatar_usage_billing_period"
            }
        },
        "usage_quotas": {
            "required_columns": {
                "id", "user_id", "total_limit_minutes", "used_minutes", "used_seconds",
                "session_count", "quota_exhausted", "exhausted_at", "created_at", "updated_at"
            },
            "indexes": {
                "idx_usage_quotas_user_id", "idx_usage_quotas_exhausted"
            }
        },
        "usage_summaries": {
            "required_columns": {
                "id", "user_id", "billing_period", "total_sessions", "total_duration_seconds",
                "total_words_spoken", "total_messages", "total_estimated_cost",
                "created_at", "updated_at"
            },
            "indexes": {
                "idx_usage_summaries_user_id", "idx_usage_summaries_billing_period"
            }
        },
        
        # Migration management tables (from 005_add_schema_migrations.sql)
        "schema_migrations": {
            "required_columns": {
                "id", "version", "filename", "description", "checksum",
                "applied_at", "execution_time_ms", "applied_by", "status",
                "error_message", "rollback_sql", "rolled_back_at", "rolled_back_by", "created_at"
            },
            "indexes": {
                "idx_schema_migrations_version", "idx_schema_migrations_applied_at",
                "idx_schema_migrations_status"
            }
        }
    }
    
    # Repository table name mappings
    REPOSITORY_TABLE_MAPPINGS = {
        "UserRepository": "users",
        "SessionRepository": "sessions",  # Fixed from "user_sessions"
        "MessageRepository": "messages",
        "TokenRepository": "service_tokens",
        "UsageRepository": "avatar_usage_records"
    }
    
    async def validate_schema(self) -> Dict[str, any]:
        """
        Validate that the database schema matches migration expectations.
        
        Returns:
            Dict with validation results
        """
        results = {
            "valid": True,
            "missing_tables": [],
            "missing_columns": {},
            "missing_indexes": {},
            "repository_mismatches": [],
            "migration_status": None
        }
        
        try:
            # Check if migration tracking exists
            migration_status = await self._check_migration_status()
            results["migration_status"] = migration_status
            
            # Get actual database schema
            actual_tables = await self._get_database_tables()
            actual_columns = await self._get_table_columns()
            actual_indexes = await self._get_database_indexes()
            
            # Validate tables exist
            for table_name, table_spec in self.EXPECTED_TABLES.items():
                if table_name not in actual_tables:
                    results["missing_tables"].append(table_name)
                    results["valid"] = False
                    continue
                
                # Validate columns exist
                missing_columns = table_spec["required_columns"] - actual_columns.get(table_name, set())
                if missing_columns:
                    results["missing_columns"][table_name] = list(missing_columns)
                    results["valid"] = False
                
                # Validate indexes exist (optional - some might be named differently)
                missing_indexes = table_spec["indexes"] - actual_indexes.get(table_name, set())
                if missing_indexes:
                    results["missing_indexes"][table_name] = list(missing_indexes)
                    # Don't mark as invalid for missing indexes - they're performance optimizations
            
            # Validate repository mappings
            repository_issues = await self._validate_repository_mappings(actual_tables)
            results["repository_mismatches"] = repository_issues
            if repository_issues:
                results["valid"] = False
            
            logger.info(f"Schema validation completed. Valid: {results['valid']}")
            return results
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            results["valid"] = False
            results["error"] = str(e)
            return results
    
    async def _check_migration_status(self) -> Optional[Dict]:
        """Check if migration tracking system is available."""
        try:
            response = self.db.table("schema_migrations").select("version").limit(1).execute()
            if response.data:
                # Get current schema version
                version_response = self.db.table("database_schema_version").select("*").limit(1).execute()
                if version_response.data:
                    return version_response.data[0]
            return None
        except Exception:
            return None
    
    async def _get_database_tables(self) -> Set[str]:
        """Get list of tables in the database."""
        try:
            # Use Supabase's information_schema access
            response = self.db.rpc('get_table_names').execute()
            if response.data:
                return set(response.data)
            
            # Fallback: try to query known tables
            known_tables = set()
            for table_name in self.EXPECTED_TABLES.keys():
                try:
                    self.db.table(table_name).select("*").limit(1).execute()
                    known_tables.add(table_name)
                except Exception:
                    pass
            return known_tables
            
        except Exception as e:
            logger.warning(f"Could not get table list: {e}")
            return set()
    
    async def _get_table_columns(self) -> Dict[str, Set[str]]:
        """Get columns for each table."""
        table_columns = {}
        
        for table_name in self.EXPECTED_TABLES.keys():
            try:
                # Try to get table structure by querying with limit 0
                response = self.db.table(table_name).select("*").limit(0).execute()
                # This is a limitation - Supabase doesn't easily expose column info
                # In practice, you'd use the Supabase dashboard or direct SQL
                table_columns[table_name] = set()  # Placeholder
            except Exception:
                table_columns[table_name] = set()
        
        return table_columns
    
    async def _get_database_indexes(self) -> Dict[str, Set[str]]:
        """Get indexes for each table."""
        # Similar limitation with Supabase - would need direct SQL access
        return {}
    
    async def _validate_repository_mappings(self, actual_tables: Set[str]) -> List[str]:
        """Validate that repository table mappings are correct."""
        issues = []
        
        for repo_class, expected_table in self.REPOSITORY_TABLE_MAPPINGS.items():
            if expected_table not in actual_tables:
                issues.append(f"{repo_class} expects table '{expected_table}' but it doesn't exist")
        
        return issues
    
    async def get_migration_recommendations(self) -> List[str]:
        """Get recommendations for fixing schema issues."""
        validation_results = await self.validate_schema()
        recommendations = []
        
        if not validation_results["valid"]:
            if validation_results["missing_tables"]:
                recommendations.append(
                    f"Run migrations to create missing tables: {', '.join(validation_results['missing_tables'])}"
                )
            
            if validation_results["repository_mismatches"]:
                recommendations.append(
                    "Fix repository table name mismatches:\n" + 
                    "\n".join(f"  - {issue}" for issue in validation_results["repository_mismatches"])
                )
            
            if not validation_results["migration_status"]:
                recommendations.append(
                    "Migration tracking system not found. Run migration 005_add_schema_migrations.sql"
                )
        
        return recommendations


# Utility function for easy validation
async def validate_database_schema(db_client: Client) -> Dict[str, any]:
    """
    Convenience function to validate database schema.
    
    Usage:
        from app.core.database.schema_validator import validate_database_schema
        
        results = await validate_database_schema(db_client)
        if not results["valid"]:
            print("Schema issues found:", results)
    """
    validator = SchemaValidator(db_client)
    return await validator.validate_schema()


# Repository table name constants (to prevent hardcoding)
class TableNames:
    """Centralized table name constants for repositories."""
    
    # Core tables
    USERS = "users"
    SESSIONS = "sessions"  # Fixed from "user_sessions"
    MESSAGES = "messages"
    USER_TOKENS = "user_tokens"
    USER_ACTIVITIES = "user_activities"
    
    # OAuth tables
    SERVICE_TOKENS = "service_tokens"
    TOKEN_REFRESH_LOGS = "token_refresh_logs"
    
    # Avatar usage tables
    AVATAR_USAGE_RECORDS = "avatar_usage_records"
    USAGE_QUOTAS = "usage_quotas"
    USAGE_SUMMARIES = "usage_summaries"
    
    # Migration tables
    SCHEMA_MIGRATIONS = "schema_migrations"
    MIGRATION_DEPENDENCIES = "migration_dependencies"
    DATABASE_SCHEMA_VERSION = "database_schema_version" 