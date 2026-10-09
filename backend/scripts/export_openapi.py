"""Print the OpenAPI contract: `make openapi` writes it to docs/api/openapi.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

print(json.dumps(app.openapi(), ensure_ascii=False, indent=2))
