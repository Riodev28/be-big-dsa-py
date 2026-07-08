from fastapi import HTTPException, status

class AuthExceptions:
    
    def credentials_exceptions() -> None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        
    def user_exists() -> None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user already exists",
            headers={"WWW-Authenticate": "Bearer"},
        )