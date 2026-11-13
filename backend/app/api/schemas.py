from pydantic import BaseModel, ConfigDict, Field

class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    upload_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    sheet: str = Field(min_length=1, max_length=128)
    header_row: int = Field(default=1, ge=1, le=100)
    mapping: dict[str, str]

class JobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    module_id: str = "account-role-mapping"
    inputs: dict[str, Selection]
    config: dict = Field(default_factory=dict)

class TemplateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    module_id: str
    config: dict
    inputs: dict

class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    include_zero_counts: bool = True
    exclude_invalid_emails: bool = True
    include_full_audit_emails: bool = False
    login_day_first: bool = True
