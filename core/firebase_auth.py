import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
if not os.path.exists(cred_path):
    raise RuntimeError(f"Firebase credentials file not found at path: {cred_path}")

try:
    cred = credentials.Certificate(cred_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
except Exception as e:
    raise RuntimeError(f"Failed to load Firebase credentials: {e}")

http_bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(http_bearer)
) -> dict:
    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = cred.credentials
        decoded_token = auth.verify_id_token(token)
        
        if not decoded_token.get('email_verified'):
            if decoded_token.get('firebase', {}).get('sign_in_provider') == 'password':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email not verified. Please verify your email before proceeding."
                )
        
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )