from dataclasses import dataclass 
from datetime import datetime

@dataclass(frozen=True)
class Claims:
    expires_at: datetime
    email: str
