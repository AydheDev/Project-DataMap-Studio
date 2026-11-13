from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
import pandas as pd

@dataclass
class ProcessingResult:
    tables: dict[str, pd.DataFrame]
    metrics: dict[str, int]
    notes: list[str]

class FeatureModule(Protocol):
    metadata: dict[str, Any]
    config_model: Any

    def validate(self, inputs: dict[str, pd.DataFrame], config: Any) -> None: ...
    def process(self, inputs: dict[str, pd.DataFrame], config: Any) -> ProcessingResult: ...
    def export(self, result: ProcessingResult, target: Path) -> None: ...
