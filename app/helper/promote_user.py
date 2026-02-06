import firebase_admin
from firebase_admin import credentials, auth
import os
from dotenv import load_dotenv

uid = "IBiR8kZCkPQj0maSO8tLIgND3n12"
load_dotenv()

# SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


# if not firebase_admin._apps:
#     cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
#     firebase_admin.initialize_app(cred)

def promote_user_to_host(uid:str):
    auth.set_custom_user_claims(uid, {
        "role": "MC",
        "roomId": "211123"
    })

def create_new_user(email: str, password: str):
    user = auth.create_user(
        email=email,
        password=password,
        email_verified=False,
        disabled=False,
    )

    return {
        "message": "user created",
        "user": user
    }

# promote_user_to_host(uid)
    

# print(f"role granted for {uid}")
