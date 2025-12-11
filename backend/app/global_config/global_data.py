from app.db import db_manager
from typing import Dict, Any, Optional


database_dict = {
    "onev_portal_database": "onev_portal_database",
    "organization_setup_database": "organization_setup_database",
    "timesheet_database": "timesheet_database"
}


app_dict = {
    "onev": "OneV Portal",
    "organization_setup": "Organization Setup",
    "timesheet" : "Timesheet App ",
    "expense": "Expense Tracker",
    
}

app_db_mapping = {
    "onev": "onev_portal_database", 
    "organization_setup": "organization_setup_database",
    "timesheet": "timesheet_database",
}