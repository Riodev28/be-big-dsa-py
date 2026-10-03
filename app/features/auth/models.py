from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    ReferenceField,
    StringField,
    CASCADE,
)

from app.shared.helpers.datetime_helper import utcnow


class UserModel(Document):
    username = StringField(max_length=255)
    email = StringField(max_length=255)
    password = StringField(max_length=255)
    remember_password = BooleanField(default=False)
    created_at = DateTimeField(default=utcnow)
    updated_at = DateTimeField(default=utcnow)

    meta = {
        "collection": "users",
        "indexes": ["email"],
    }


class RefreshTokenModel(Document):
    """
    Server-side record of an issued refresh token, keyed by its JWT `jti`.
    Lets us rotate tokens, revoke them on logout and detect reuse of a
    token that was already rotated (a sign it was stolen).
    """

    jti = StringField(required=True, unique=True)
    user = ReferenceField(UserModel, required=True, reverse_delete_rule=CASCADE)
    revoked = BooleanField(default=False)
    created_at = DateTimeField(default=utcnow)
    expires_at = DateTimeField(required=True)

    meta = {
        "collection": "refresh_tokens",
        "indexes": [
            "user",
            {"fields": ["expires_at"], "expireAfterSeconds": 0},
        ],
    }
