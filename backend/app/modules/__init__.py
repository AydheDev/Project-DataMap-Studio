from ..core.registry import ModuleRegistry
from .account_role_mapping.module import AccountRoleMapping
from .sample.module import SampleModule

def default_registry():
    registry = ModuleRegistry()
    registry.register(AccountRoleMapping())
    registry.register(SampleModule())
    return registry
