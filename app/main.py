from fastapi import FastAPI
from app.routes.tests import test_routers
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Đăng ký router từ module routes
app.include_router(test_routers)

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI with Firestore and Realtime DB"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn (hoặc chỉ định các domain cụ thể)
    allow_methods=["*"],  # Cho phép tất cả các phương thức HTTP (GET, POST, v.v.)
    allow_headers=["*"],  # Cho phép tất cả các headers

)
