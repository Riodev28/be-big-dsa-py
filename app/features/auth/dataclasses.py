from dataclasses import dataclass 
from datetime import datetime

@dataclass(frozen=True)
class Claims:
    user_id: str
    username: str
    email: str
    expires_at: datetime
    
@dataclass
class TokenData:
    user_id: str
    username: str
    email: str
    
    def __post_init__(self):
        self.user_id = str(self.user_id)
