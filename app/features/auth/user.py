

class User:
    def __init__(self, username, email, password):
        self._username = username
        self._email = email
        self._password = password
        
    def username(self) -> str:
        return self._username
    
    def email(self) -> str:
        return self._email