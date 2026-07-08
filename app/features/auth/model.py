from mongoengine import (
    Document,
    StringField,
    BooleanField,
    DateTimeField
)

from datetime import datetime, timezone

class UserModel(Document):
    
    username= StringField(max_length=255)
    email= StringField(max_length=255)
    password= StringField(max_length=255)
    remember_password= BooleanField(default=False)
    created_at= DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at= DateTimeField(default=lambda: datetime.now(timezone.utc))
    
    meta = {
        "collection": "users",
        "indexes": ["email"]
    }