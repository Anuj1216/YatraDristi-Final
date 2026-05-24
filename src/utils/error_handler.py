from __future__ import annotations

import traceback
from typing import Any, Dict


def safe_execute(func, *args, **kwargs) -> Dict[str, Any]:
    try:
        result = func(*args, **kwargs)
        return {
            "success": True,
            "data": result,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "trace": traceback.format_exc(),
        }