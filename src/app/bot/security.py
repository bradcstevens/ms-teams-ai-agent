"""
Security Headers and CORS Configuration
Implements production-grade security headers and CORS settings
"""
from typing import Dict, List


def get_security_headers() -> Dict[str, str]:
    """
    Get security headers for HTTP responses.

    Returns:
        Dictionary of security headers

    Security headers implemented:
    - HSTS: Enforce HTTPS connections
    - CSP: Content Security Policy
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-XSS-Protection: Enable XSS filter
    """
    return {
        # Strict-Transport-Security: Enforce HTTPS for 1 year
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',

        # Content-Security-Policy: Restrict resource loading
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://api.botframework.com https://*.teams.microsoft.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),

        # X-Frame-Options: Prevent embedding in iframes
        'X-Frame-Options': 'DENY',

        # X-Content-Type-Options: Prevent MIME type sniffing
        'X-Content-Type-Options': 'nosniff',

        # X-XSS-Protection: Enable XSS filter (legacy support)
        'X-XSS-Protection': '1; mode=block',

        # Referrer-Policy: Control referrer information
        'Referrer-Policy': 'strict-origin-when-cross-origin',

        # Permissions-Policy: Control browser features
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }


def get_cors_config() -> Dict[str, List[str]]:
    """
    Get CORS configuration for Bot Framework integration.

    Returns:
        Dictionary with CORS configuration

    CORS Configuration:
    - Allowed origins: Microsoft Teams and Bot Framework domains
    - Allowed methods: POST, GET for bot messages
    - Allowed headers: Authorization, Content-Type
    """
    return {
        'allowed_origins': [
            'https://teams.microsoft.com',
            'https://*.teams.microsoft.com',
            'https://api.botframework.com',
            'https://*.botframework.com',
            'https://smba.trafficmanager.net',
            'https://*.smba.trafficmanager.net'
        ],
        'allowed_methods': [
            'GET',
            'POST',
            'OPTIONS'
        ],
        'allowed_headers': [
            'Authorization',
            'Content-Type',
            'Accept',
            'Origin',
            'User-Agent',
            'X-Requested-With'
        ],
        'allow_credentials': True,
        'max_age': 600  # 10 minutes
    }


def get_rate_limit_config() -> Dict[str, int]:
    """
    Get rate limiting configuration.

    Returns:
        Dictionary with rate limit settings

    Rate Limits:
    - messages_per_minute: Maximum messages per minute per user
    - messages_per_hour: Maximum messages per hour per user
    - burst_size: Maximum burst size
    """
    return {
        'messages_per_minute': 10,
        'messages_per_hour': 100,
        'burst_size': 5,
        'window_size_seconds': 60
    }


def get_waf_rules() -> List[Dict[str, str]]:
    """
    Get Web Application Firewall rule definitions.

    Returns:
        List of WAF rule configurations

    WAF Rules (for Azure Front Door/Application Gateway):
    - SQL injection protection
    - XSS protection
    - Protocol enforcement
    - Rate limiting
    - Bot detection
    """
    return [
        {
            'name': 'SQLInjectionProtection',
            'priority': 100,
            'rule_type': 'MatchRule',
            'match_conditions': [
                {
                    'match_variable': 'RequestBody',
                    'operator': 'Contains',
                    'match_values': ['union', 'select', 'insert', 'drop', 'delete'],
                    'transforms': ['Lowercase']
                }
            ],
            'action': 'Block'
        },
        {
            'name': 'XSSProtection',
            'priority': 200,
            'rule_type': 'MatchRule',
            'match_conditions': [
                {
                    'match_variable': 'RequestBody',
                    'operator': 'Contains',
                    'match_values': ['<script', 'javascript:', 'onerror='],
                    'transforms': ['Lowercase']
                }
            ],
            'action': 'Block'
        },
        {
            'name': 'RateLimitByIP',
            'priority': 300,
            'rule_type': 'RateLimitRule',
            'rate_limit_duration': 'OneMinute',
            'rate_limit_threshold': 100,
            'action': 'Block'
        },
        {
            'name': 'EnforceHTTPS',
            'priority': 400,
            'rule_type': 'MatchRule',
            'match_conditions': [
                {
                    'match_variable': 'RequestScheme',
                    'operator': 'Equal',
                    'match_values': ['http']
                }
            ],
            'action': 'Redirect',
            'redirect_url': 'https://{host}{path}'
        }
    ]


def get_ddos_protection_config() -> Dict[str, any]:
    """
    Get DDoS protection configuration.

    Returns:
        Dictionary with DDoS protection settings
    """
    return {
        'enabled': True,
        'protection_mode': 'VirtualNetworkInherited',
        'ddos_custom_policy': None,  # Use Azure DDoS Protection Standard
        'alert_threshold_multiplier': 5
    }
