import pytest


@pytest.mark.integration
def test_register_login_and_me(client, unique_email):
    password = "testpassword123"

    register = client.post(
        "/v1/auth/register",
        json={"email": unique_email, "password": password},
    )
    assert register.status_code == 200
    tokens = register.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    login = client.post(
        "/v1/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login.status_code == 200
    access_token = login.json()["access_token"]

    me = client.get("/v1/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me.status_code == 200
    assert me.json()["email"] == unique_email


@pytest.mark.integration
def test_login_invalid_credentials(client, unique_email):
    client.post(
        "/v1/auth/register",
        json={"email": unique_email, "password": "testpassword123"},
    )
    login = client.post(
        "/v1/auth/login",
        json={"email": unique_email, "password": "wrongpassword"},
    )
    assert login.status_code == 401
