from __future__ import annotations

import json
import sys
from typing import Any


def log(level: str, msg: str, **fields: Any) -> None:
    payload = {"level": level, "msg": msg, **fields}
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()








