from datetime import datetime

from ..models import RefreshTokenModel, UserModel


class RefreshTokenRepository:
    def create(
        self, jti: str, user: UserModel, expires_at: datetime
    ) -> RefreshTokenModel:
        return RefreshTokenModel(jti=jti, user=user, expires_at=expires_at).save()

    def revoke(self, jti: str) -> bool:
        """
        Atomically flips an active token to revoked. Returns False when the
        token is unknown or was already revoked, so two concurrent refreshes
        with the same token can never both succeed.
        """
        updated = RefreshTokenModel.objects(jti=jti, revoked=False).update_one(
            set__revoked=True
        )
        return updated == 1

    def revoke_all_for_user(self, user_id: str) -> None:
        RefreshTokenModel.objects(user=user_id, revoked=False).update(set__revoked=True)
