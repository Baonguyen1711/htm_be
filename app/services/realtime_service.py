from database import db

# Cấu hình Realtime Database
def send_realtime_notification(data: dict):
    ref = db.reference("/notifications")
    ref.push(data)
