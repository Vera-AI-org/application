import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from api.services.user.user_service import get_or_create_user
from models.user_model import User

try:
    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
except Exception as e:
    raise RuntimeError(f"Falha ao inicializar o Firebase Admin SDK: {e}")


http_bearer = HTTPBearer()

def get_current_user(
    db: Session = Depends(get_db),
    token_cred: HTTPAuthorizationCredentials = Depends(http_bearer)
) -> User:
    if token_cred is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        id_token = token_cred.credentials
        decoded_token = auth.verify_id_token(id_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido ou expirado: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not decoded_token.get('email_verified'):
        if decoded_token.get('firebase', {}).get('sign_in_provider') == 'password':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Por favor, verifique seu e-mail para continuar."
            )
        
    db_user = get_or_create_user(db=db, firebase_user=decoded_token)
    
    return db_user