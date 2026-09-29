from mongoengine import (
    Document,
    StringField,
    BooleanField,
    DateTimeField,
    ReferenceField,
)

from app.shared.helpers.datetime_helper import utcnow


class UserModel(Document):
    username = StringField(max_length=255)
    email = StringField(max_length=255)
    password = StringField(max_length=255)
    remember_password = BooleanField(default=False)
    created_at = DateTimeField(default=utcnow)
    updated_at = DateTimeField(default=utcnow)

    meta = {"collection": "users", "indexes": ["email"]}


class FileModel(Document):
    title = StringField(max_length=100)
    content = StringField()

    created_at = DateTimeField(default=utcnow)
    updated_at = DateTimeField(default=utcnow)

    owner = ReferenceField(UserModel)

    def save(self, *args, **kwargs):
        self.updated_at = utcnow()
        return super().save(*args, **kwargs)
