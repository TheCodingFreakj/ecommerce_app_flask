# test_auth.py
import pytest
import jwt
from app import app

@pytest.mark.asyncio
async def test_login(auth_headers):
    assert 'Authorization' in auth_headers
    token = auth_headers['Authorization'].split(' ')[1]
    decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    assert decoded['user'] == 'user'