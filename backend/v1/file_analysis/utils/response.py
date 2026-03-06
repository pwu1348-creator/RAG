import json
from datetime import datetime, date
from fastapi.responses import JSONResponse
from typing import Any


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def success_response(data: Any = None, message: str = "success", code: int = 200):
    content = {
        "code": code,
        "message": message,
        "data": data
    }
    return JSONResponse(
        content=json.loads(json.dumps(content, cls=DateTimeEncoder, ensure_ascii=False)),
        status_code=code,
        media_type="application/json; charset=utf-8"
    )


def error_response(message: str = "error", code: int = 500, data: Any = None):
    content = {
        "code": code,
        "message": message,
        "data": data
    }
    return JSONResponse(
        content=json.loads(json.dumps(content, cls=DateTimeEncoder, ensure_ascii=False)),
        status_code=code,
        media_type="application/json; charset=utf-8"
    )
