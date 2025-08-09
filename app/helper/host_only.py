import asyncio
from fastapi import Request, HTTPException
from functools import wraps

def host_only(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Tìm đối tượng Request trong args hoặc kwargs
        request: Request | None = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        if not request:
            request = kwargs.get("request", None)
        if not request:
            raise HTTPException(status_code=400, detail="Request object not found")

        # Lấy user info đã được middleware xác thực gán vào request.state.user
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Kiểm tra payload có trường 'email' hợp lệ không (host có email)
        email = user.get("email")
        if not email or "@" not in email:
            raise HTTPException(status_code=403, detail="Forbidden: Only host allowed")

        # Nếu OK thì chạy hàm gốc

        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    return wrapper
