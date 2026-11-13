from pydantic import BaseModel
from ...core.contracts import ProcessingResult

class SampleConfig(BaseModel):
    pass

class SampleModule:
    """Trusted source-code example. Disabled; never accepts executable uploads."""
    metadata = {"id": "sample", "name": "Sample extension", "version": "0.1.0",
                "description": "Developer template for a future independent feature.",
                "enabled": False, "ui_route": "/modules", "inputs": []}
    config_model = SampleConfig
    def validate(self, inputs, config):
        raise ValueError("This example module is disabled.")
    def process(self, inputs, config) -> ProcessingResult:
        raise ValueError("Implement the module before enabling it.")
    def export(self, result, target):
        raise ValueError("Implement an exporter before enabling the module.")
