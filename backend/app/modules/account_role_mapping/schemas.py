from pydantic import BaseModel, ConfigDict, Field

class MappingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    include_zero_counts: bool = True
    exclude_invalid_emails: bool = True
    include_full_audit_emails: bool = False
    login_day_first: bool = True

SOURCE_COLUMNS = [
    {"key": "market", "label": "Market", "aliases": ["Market", "Country"]},
    {"key": "role", "label": "Account Role", "aliases": ["FDS JobRole", "JobRole", "Account Role"]},
    {"key": "fds_email", "label": "FDS Email", "aliases": ["FDS Email"]},
    {"key": "eip_email", "label": "EIP Email", "aliases": ["EIP Email"]},
    {"key": "login", "label": "Salesforce Last login", "aliases": ["Salesforce Last login", "Last login"], "forbidden_aliases": ["Salesforce Fed ID", "Salesforce Federation ID"]},
]
ROLE_COLUMNS = [{"key": "role_code", "label": "Approved Role Code", "aliases": ["Role Code"]}]
