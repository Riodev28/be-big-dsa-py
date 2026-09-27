from mongoengine import (
    Document,
    StringField,
    BooleanField,
    DateTimeField,
    ReferenceField
)

from datetime import datetime, timezone

class UserModel(Document):
    id = StringField(primary_key=True)
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
    
    
class FileModel(Document):
    title= StringField(max_length=100)
    content= StringField()
    
    created_at= DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at= DateTimeField(default=lambda: datetime.now(timezone.utc))
    
    owner= ReferenceField(UserModel)