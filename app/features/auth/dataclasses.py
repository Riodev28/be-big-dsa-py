from dataclasses import dataclass 
from datetime import datetime

@dataclass(frozen=True)
class Claims:
    user_id: str
    username: str
    email: str
    expires_at: datetime
    
@dataclass(frozen=True)
class TokenData:
    user_id: str
    username: str
    email: str
