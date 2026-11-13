from .schemas import MappingConfig, SOURCE_COLUMNS, ROLE_COLUMNS
from .validators import validate_inputs
from .processor import process
from ...services.export import write_workbook

class AccountRoleMapping:
    metadata = {
        "id": "account-role-mapping", "name": "Account Role Mapping", "version": "1.0.0",
        "description": "Approved account roles, unique accounts and auditable market reporting.",
        "enabled": True, "ui_route": "/account-role-mapping",
        "inputs": [
            {"id": "source", "label": "FDS + SSO-EIP workbook", "columns": SOURCE_COLUMNS},
            {"id": "roles", "label": "Approved account roles", "columns": ROLE_COLUMNS},
        ],
    }
    config_model = MappingConfig
    validate = staticmethod(validate_inputs)
    process = staticmethod(process)
    @staticmethod
    def export(result, target):
        write_workbook(result.tables, target)
