import jwt

from ..dataclasses import TokenData, TokenPair
from ..exceptions import AuthExceptions
from ..models import UserModel
from ..repositories import RefreshTokenRepository, UserRepository
from ..schemas import LoginDTORequest, RegisterDTORequest
from ..security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class AuthService:
    """
    Authentication business logic: credential checks, password hashing,
    token issuing, rotation and revocation. Returns domain objects
    (UserModel, TokenPair), never response DTOs.
    """

    def __init__(self, users: UserRepository, refresh_tokens: RefreshTokenRepository):
        self.users = users
        self.refresh_tokens = refresh_tokens

    def register(self, dto: RegisterDTORequest) -> tuple[UserModel, TokenPair]:
        if self.users.exists_by_email(dto.email):
            raise AuthExceptions.user_exists()

        user = self.users.create(
            username=dto.username,
            email=dto.email,
            hashed_password=hash_password(dto.password.get_secret_value()),
        )
        return user, self._issue_tokens(user)

    def login(self, dto: LoginDTORequest) -> TokenPair:
        user = self.users.get_by_email(dto.email)

        if user is None or not verify_password(
            plain=dto.password.get_secret_value(),
            hashed=user.password,
        ):
            raise AuthExceptions.invalid_credentials()

        return self._issue_tokens(user)

    def refresh(self, refresh_token: str) -> TokenPair:
        """
        Rotates the refresh token: the presented one is revoked and a new
        pair is issued. Presenting an already revoked token means it leaked,
        so every session of that user is revoked.
        """
        payload = self._decode_refresh(refresh_token)
        user_id = payload.get("user_id", "")

        if not self.refresh_tokens.revoke(payload["jti"]):
            self.refresh_tokens.revoke_all_for_user(user_id)
            raise AuthExceptions.credentials_exceptions()

        user = self.users.get_by_id(user_id)
        if user is None:
            raise AuthExceptions.credentials_exceptions()

        return self._issue_tokens(user)

    def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except jwt.InvalidTokenError:
            return  # already unusable, nothing to revoke
        self.refresh_tokens.revoke(payload["jti"])

    def get_current_user(self, user_id: str) -> UserModel:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise AuthExceptions.credentials_exceptions()
        return user

    def _decode_refresh(self, refresh_token: str) -> dict:
        try:
            return decode_token(refresh_token, expected_type="refresh")
        except jwt.ExpiredSignatureError:
            raise AuthExceptions.token_expired()
        except jwt.InvalidTokenError:
            raise AuthExceptions.invalid_token()

    def _issue_tokens(self, user: UserModel) -> TokenPair:
        data = TokenData(user_id=user.id, username=user.username, email=user.email)

        refresh = create_refresh_token(data)
        self.refresh_tokens.create(
            jti=refresh.jti, user=user, expires_at=refresh.expires_at
        )

        return TokenPair(
            access_token=create_access_token(data), refresh_token=refresh.token
        )
