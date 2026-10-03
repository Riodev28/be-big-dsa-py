from bson import ObjectId

from ..models import UserModel


class UserRepository:
    """Persistence only: no hashing, tokens or HTTP concerns."""

    def get_by_id(self, id: str) -> UserModel | None:
        if not ObjectId.is_valid(id):
            return None
        return UserModel.objects(id=id).first()

    def get_by_email(self, email: str) -> UserModel | None:
        return UserModel.objects(email=email).first()

    def exists_by_email(self, email: str) -> bool:
        return UserModel.objects(email=email).count() > 0

    def create(self, username: str, email: str, hashed_password: str) -> UserModel:
        return UserModel(username=username, email=email, password=hashed_password).save()
