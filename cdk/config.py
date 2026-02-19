import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any


@dataclass
class EnvConfig:
    env_name: str
    ssm: Dict[str, str]
    cognito: Dict[str, str]

    @staticmethod
    def load(env_file: str) -> "EnvConfig":
        p = Path(env_file)
        data: Dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
        return EnvConfig(
            env_name=data["envName"],
            ssm=data["ssm"],
            cognito=data.get("cognito", {}),
        )