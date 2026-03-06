import os
from typing import Tuple

from config import config


async def validate_file(file) -> Tuple[bool, str]:
    if not file or not file.filename:
        return False, "Empty filename"
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in config.parser.SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type: {ext}"
    
    await file.seek(0)
    content = await file.read()
    file_size = len(content)
    await file.seek(0)
    
    max_size = config.parser.MAX_FILE_SIZE * 1024 * 1024
    if file_size > max_size:
        return False, f"File size exceeds limit: {config.parser.MAX_FILE_SIZE}MB"
    
    if file_size == 0:
        return False, "Empty file"
    
    return True, ""
