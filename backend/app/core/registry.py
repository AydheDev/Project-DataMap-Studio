from .contracts import FeatureModule

class ModuleRegistry:
    def __init__(self):
        self._modules: dict[str, FeatureModule] = {}

    def register(self, module: FeatureModule):
        key = module.metadata["id"]
        if key in self._modules:
            raise ValueError(f"Module already registered: {key}")
        self._modules[key] = module

    def get(self, key: str) -> FeatureModule:
        if key not in self._modules:
            raise ValueError("Unknown feature module.")
        return self._modules[key]

    def describe(self):
        return [{**m.metadata, "configuration_schema": m.config_model.model_json_schema()}
                for m in self._modules.values()]
