import uuid

from jose import jwt

from app.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    user_id_from_token,
    verify_password,
)
from app.config import settings


class TestPasswordHashing:
    def test_round_trip(self):
        hashed = hash_password("secret123")
        assert verify_password("secret123", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("secret123")
        assert not verify_password("wrong", hashed)


class TestTokens:
    def test_access_token_payload(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    def test_refresh_token_payload(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"


class TestUserIdFromToken:
    def test_valid_access_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        assert user_id_from_token(token, "access") == user_id

    def test_refresh_token_rejected_for_access(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        assert user_id_from_token(token, "access") is None

    def test_malformed_token(self):
        assert user_id_from_token("not.a.token", "access") is None

    def test_wrong_secret(self):
        user_id = uuid.uuid4()
        payload = {"sub": str(user_id), "type": "access", "exp": 9999999999}
        bad_token = jwt.encode(payload, "wrong-secret", algorithm=settings.jwt_algorithm)
        assert user_id_from_token(bad_token, "access") is None
