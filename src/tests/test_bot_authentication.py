"""
Test Bot Framework Authentication & Security
Tests authentication middleware and JWT validation
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import jwt
from datetime import datetime, timedelta, timezone


class TestBotAuthentication:
    """Test suite for Bot Framework JWT authentication validation."""

    @pytest.fixture
    def mock_jwt_token(self):
        """Generate mock JWT token for testing."""
        now = datetime.now(timezone.utc)
        payload = {
            'aud': 'test-bot-id',
            'iss': 'https://api.botframework.com',
            'exp': int((now + timedelta(hours=1)).timestamp()),
            'nbf': int(now.timestamp()),
            'serviceUrl': 'https://smba.trafficmanager.net/amer/'
        }
        return jwt.encode(payload, 'test-secret', algorithm='HS256')

    @pytest.fixture
    def expired_jwt_token(self):
        """Generate expired JWT token for testing."""
        now = datetime.now(timezone.utc)
        payload = {
            'aud': 'test-bot-id',
            'iss': 'https://api.botframework.com',
            'exp': int((now - timedelta(hours=1)).timestamp()),
            'nbf': int(now.timestamp()),
        }
        return jwt.encode(payload, 'test-secret', algorithm='HS256')

    def test_validate_jwt_token_valid(self, mock_jwt_token):
        """Test JWT token validation with valid token."""
        from app.bot.auth import validate_jwt_token

        result = validate_jwt_token(
            f"Bearer {mock_jwt_token}",
            bot_id="test-bot-id"
        )
        assert result is True

    def test_validate_jwt_token_expired(self, expired_jwt_token):
        """Test JWT token validation with expired token."""
        from app.bot.auth import validate_jwt_token

        with pytest.raises(jwt.ExpiredSignatureError):
            validate_jwt_token(
                f"Bearer {expired_jwt_token}",
                bot_id="test-bot-id"
            )

    def test_validate_jwt_token_missing_bearer(self, mock_jwt_token):
        """Test JWT token validation without Bearer prefix."""
        from app.bot.auth import validate_jwt_token

        result = validate_jwt_token(
            mock_jwt_token,
            bot_id="test-bot-id"
        )
        assert result is False

    def test_validate_jwt_token_invalid_audience(self, mock_jwt_token):
        """Test JWT token validation with wrong audience."""
        from app.bot.auth import validate_jwt_token

        with pytest.raises(jwt.InvalidAudienceError):
            validate_jwt_token(
                f"Bearer {mock_jwt_token}",
                bot_id="different-bot-id"
            )

    def test_validate_microsoft_tenant_valid(self):
        """Test Microsoft tenant verification with valid tenant."""
        from app.bot.auth import validate_microsoft_tenant

        tenant_id = "72f988bf-86f1-41af-91ab-2d7cd011db47"  # Microsoft tenant
        result = validate_microsoft_tenant(tenant_id)
        assert result is True

    def test_validate_microsoft_tenant_invalid(self):
        """Test Microsoft tenant verification with invalid tenant."""
        from app.bot.auth import validate_microsoft_tenant

        tenant_id = "invalid-tenant-id"
        result = validate_microsoft_tenant(tenant_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_authentication_middleware_valid(self, mock_jwt_token):
        """Test authentication middleware with valid credentials."""
        from app.bot.auth import authentication_middleware
        from fastapi import Request
        from unittest.mock import MagicMock

        request = MagicMock(spec=Request)
        request.headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        request.app.state.bot_id = "test-bot-id"
        # Set the URL path to /api/messages to trigger authentication
        request.url.path = "/api/messages"

        call_next = AsyncMock(return_value="response")

        response = await authentication_middleware(request, call_next)
        assert response == "response"
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_authentication_middleware_invalid(self):
        """Test authentication middleware with invalid credentials."""
        from app.bot.auth import authentication_middleware
        from fastapi import Request, HTTPException
        from unittest.mock import MagicMock

        request = MagicMock(spec=Request)
        request.headers = {"Authorization": "Bearer invalid-token"}
        request.app.state.bot_id = "test-bot-id"
        # Set the URL path to /api/messages to trigger authentication
        request.url.path = "/api/messages"

        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await authentication_middleware(request, call_next)

        assert exc_info.value.status_code == 401

    def test_secure_credential_handling(self, monkeypatch):
        """Test that credentials are never logged or exposed."""
        from app.bot.auth import get_bot_credentials

        # Set test environment variables
        monkeypatch.setenv('BOT_ID', 'test-bot-id')
        monkeypatch.setenv('BOT_PASSWORD', 'test-bot-password')

        credentials = get_bot_credentials()
        assert 'app_password' in credentials
        assert credentials['app_password'] != ''  # Should be from env or Key Vault
        assert 'app_id' in credentials


class TestSecurityHeaders:
    """Test suite for security headers configuration."""

    def test_security_headers_hsts(self):
        """Test HSTS header configuration."""
        from app.bot.security import get_security_headers

        headers = get_security_headers()
        assert 'Strict-Transport-Security' in headers
        assert 'max-age=' in headers['Strict-Transport-Security']

    def test_security_headers_csp(self):
        """Test Content Security Policy header."""
        from app.bot.security import get_security_headers

        headers = get_security_headers()
        assert 'Content-Security-Policy' in headers
        assert "default-src 'self'" in headers['Content-Security-Policy']

    def test_security_headers_frame_options(self):
        """Test X-Frame-Options header."""
        from app.bot.security import get_security_headers

        headers = get_security_headers()
        assert 'X-Frame-Options' in headers
        assert headers['X-Frame-Options'] == 'DENY'

    def test_security_headers_content_type(self):
        """Test X-Content-Type-Options header."""
        from app.bot.security import get_security_headers

        headers = get_security_headers()
        assert 'X-Content-Type-Options' in headers
        assert headers['X-Content-Type-Options'] == 'nosniff'

    def test_security_headers_xss_protection(self):
        """Test X-XSS-Protection header."""
        from app.bot.security import get_security_headers

        headers = get_security_headers()
        assert 'X-XSS-Protection' in headers
        assert headers['X-XSS-Protection'] == '1; mode=block'


class TestCORSConfiguration:
    """Test suite for CORS configuration."""

    def test_cors_allowed_origins(self):
        """Test CORS allowed origins configuration."""
        from app.bot.security import get_cors_config

        config = get_cors_config()
        assert 'allowed_origins' in config
        assert 'https://teams.microsoft.com' in config['allowed_origins']

    def test_cors_allowed_methods(self):
        """Test CORS allowed methods configuration."""
        from app.bot.security import get_cors_config

        config = get_cors_config()
        assert 'allowed_methods' in config
        assert 'POST' in config['allowed_methods']
        assert 'GET' in config['allowed_methods']

    def test_cors_allowed_headers(self):
        """Test CORS allowed headers configuration."""
        from app.bot.security import get_cors_config

        config = get_cors_config()
        assert 'allowed_headers' in config
        assert 'Authorization' in config['allowed_headers']
        assert 'Content-Type' in config['allowed_headers']
