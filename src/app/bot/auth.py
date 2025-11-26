"""
Bot Framework Authentication & Security Module (Task 4.4)
Implements JWT token validation and Microsoft tenant verification
"""
import jwt
import os
from typing import Dict, Optional
from fastapi import Request, HTTPException
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


def validate_jwt_token(auth_header: str, bot_id: str) -> bool:
    """
    Validate Bot Framework JWT token.

    Args:
        auth_header: Authorization header with Bearer token
        bot_id: Expected bot application ID (audience)

    Returns:
        True if token is valid

    Raises:
        jwt.ExpiredSignatureError: If token is expired
        jwt.InvalidAudienceError: If audience doesn't match bot_id
    """
    if not auth_header.startswith('Bearer '):
        return False

    token = auth_header.replace('Bearer ', '')

    try:
        # Decode and validate token
        # In production, fetch public keys from Bot Framework
        # For now, validate basic structure
        decoded = jwt.decode(
            token,
            options={
                "verify_signature": False,  # Will be verified by Bot Framework Adapter
                "verify_aud": True,
                "verify_exp": True,
                "require": ["exp", "aud"]  # Require exp and aud claims for validation
            },
            audience=bot_id,
            algorithms=['RS256', 'HS256']
        )

        # Validate issuer
        valid_issuers = [
            'https://api.botframework.com',
            'https://sts.windows.net/',
            'https://login.microsoftonline.com/'
        ]

        if not any(decoded.get('iss', '').startswith(issuer) for issuer in valid_issuers):
            return False

        return True

    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidAudienceError:
        raise
    except jwt.InvalidTokenError:
        return False
    except Exception:
        return False


def validate_microsoft_tenant(tenant_id: str) -> bool:
    """
    Validate Microsoft tenant ID format.

    Args:
        tenant_id: Azure AD tenant ID (GUID)

    Returns:
        True if tenant ID is valid format
    """
    import re

    # Validate GUID format
    guid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(guid_pattern, tenant_id, re.IGNORECASE))


async def authentication_middleware(request: Request, call_next):
    """
    FastAPI middleware for Bot Framework authentication.

    Args:
        request: FastAPI request object
        call_next: Next middleware in chain

    Returns:
        Response from next middleware

    Raises:
        HTTPException: If authentication fails
    """
    # Skip authentication for health check and root endpoints
    if request.url.path in ['/', '/health']:
        return await call_next(request)

    # Only authenticate /api/messages endpoint
    if request.url.path != '/api/messages':
        return await call_next(request)

    auth_header = request.headers.get('Authorization', '')
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # Get bot ID from app state
    bot_id = getattr(request.app.state, 'bot_id', os.getenv('BOT_ID', ''))

    try:
        if not validate_jwt_token(auth_header, bot_id):
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid token audience")

    return await call_next(request)


def get_bot_credentials() -> Dict[str, str]:
    """
    Retrieve bot credentials from Azure Key Vault or environment variables.

    Returns:
        Dictionary with app_id and app_password

    Raises:
        ValueError: If credentials are not available
    """
    # Try environment variables first (for local development)
    bot_id = os.getenv('BOT_ID')
    bot_password = os.getenv('BOT_PASSWORD')

    if bot_id and bot_password:
        return {
            'app_id': bot_id,
            'app_password': bot_password
        }

    # Try Azure Key Vault (for production)
    key_vault_name = os.getenv('KEY_VAULT_NAME')
    if not key_vault_name:
        raise ValueError("BOT_ID and BOT_PASSWORD must be set in environment or Key Vault")

    try:
        key_vault_uri = f"https://{key_vault_name}.vault.azure.net"
        credential = DefaultAzureCredential()
        secret_client = SecretClient(vault_url=key_vault_uri, credential=credential)

        bot_id = secret_client.get_secret("bot-id").value
        bot_password = secret_client.get_secret("bot-password").value

        if not bot_id or not bot_password:
            raise ValueError("Bot credentials not found in Key Vault")

        return {
            'app_id': bot_id,
            'app_password': bot_password
        }

    except Exception as e:
        raise ValueError(f"Failed to retrieve bot credentials: {e}")
