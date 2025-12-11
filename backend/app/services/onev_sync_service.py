import logging
from app.db import db_manager
from app.global_config import global_data
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def sync_from_onev(app_name:str) -> dict:
    """
    Syncing users from onev portal.
    Skips users that already exist in timesheet_db.
    
    """
    
    database_name = global_data.app_db_mapping.get(app_name)
    print(f"Database name for app '{app_name}': {database_name}")
    if database_name:
        print(f"Database name found: {database_name}")
        
    try:
        async with await db_manager.transaction():
            
            users_query = f"""
            INSERT INTO {database_name}.users (
                users_id,
                email,
                username,
                first_name,
                last_name,
                phone,
                department,
                employee_id,
                hire_date,
                hourly_rate,
                `group`,
                is_active,
                password_hash,
                last_login,
                created_at,
                updated_at,
                is_admin,
                manager_id
            )
            SELECT
                users_id,
                email,
                username,
                first_name,
                last_name,
                phone,
                department,
                employee_id,
                hire_date,
                hourly_rate,
                `group`,
                is_active,
                password_hash,
                last_login,
                created_at,
                updated_at,
                is_admin,
                manager_id
            FROM onev_portal_database.users
            ON DUPLICATE KEY UPDATE
                email = VALUES(email),
                username = VALUES(username),
                first_name = VALUES(first_name),
                last_name = VALUES(last_name),
                phone = VALUES(phone),
                department = VALUES(department),
                employee_id = VALUES(employee_id),
                hire_date = VALUES(hire_date),
                hourly_rate = VALUES(hourly_rate),
                `group` = VALUES(`group`),
                is_active = VALUES(is_active),
                password_hash = VALUES(password_hash),
                last_login = VALUES(last_login),
                created_at = VALUES(created_at),
                updated_at = VALUES(updated_at),
                is_admin = VALUES(is_admin),
                manager_id = VALUES(manager_id);
            """

            users_result = await db_manager.execute(users_query)
            logger.info(f"Users sync completed. Rows affected: {users_result}")

            # --- Sync ROLES ---
            roles_query = f"""
            INSERT INTO {database_name}.roles (
                roles_id,
                name,
                description,
                permissions,
                is_active,
                created_at,
                updated_at
            )
            SELECT
                roles_id,
                name,
                description,
                permissions,
                is_active,
                created_at,
                updated_at
            FROM onev_portal_database.roles
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                description = VALUES(description),
                permissions = VALUES(permissions),
                is_active = VALUES(is_active),
                created_at = VALUES(created_at),
                updated_at = VALUES(updated_at);
            """

            roles_result = await db_manager.execute(roles_query)
            logger.info(f"Roles sync completed. Rows affected: {roles_result}")

            # --- Sync USER_ROLES ---
            user_roles_query = f"""
            INSERT INTO {database_name}.user_roles (
                user_roles_id,
                users_id,
                roles_id,
                assigned_at,
                is_active
            )
            SELECT
                user_roles_id,
                users_id,
                roles_id,
                assigned_at,
                is_active
            FROM onev_portal_database.user_roles
            ON DUPLICATE KEY UPDATE
                assigned_at = VALUES(assigned_at),
                is_active = VALUES(is_active);
            """

            user_roles_result = await db_manager.execute(user_roles_query)
            logger.info(f"UserRoles sync completed. Rows affected: {user_roles_result}")

        # Return combined summary
        return {
            "message": "Sync completed successfully",
            "rows_affected": {
                "users": users_result,
                "roles": roles_result,
                "user_roles": user_roles_result,
            }
        }

    except Exception as e:
        logger.error(f"Error during sync_from_onev: {e}")
        raise RuntimeError(f"Database sync failed: {e}")

