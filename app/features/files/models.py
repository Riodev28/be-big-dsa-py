from mongoengine import CASCADE, DateTimeField, Document, ReferenceField, StringField

from app.features.auth.models import UserModel
from app.shared.helpers.datetime_helper import utcnow


class FileModel(Document):
    title = StringField(max_length=100)
    algorithm_name = StringField(max_length=100)
    content = StringField()

    created_at = DateTimeField(default=utcnow)
    updated_at = DateTimeField(default=utcnow)

    owner = ReferenceField(UserModel, reverse_delete_rule=CASCADE)

    meta = {
        "collection": "file_model",
        "indexes": ["owner"],
    }

    def save(self, *args, **kwargs):
        self.updated_at = utcnow()
        return super().save(*args, **kwargs)
