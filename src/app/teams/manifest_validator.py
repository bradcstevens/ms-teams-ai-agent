"""
Teams App Manifest Validator
Validates Teams manifest against schema and best practices
"""
import json
import re
from typing import Tuple, List, Dict, Any


def validate_manifest(manifest_path: str) -> Tuple[bool, List[str]]:
    """
    Validate Teams app manifest.

    Args:
        manifest_path: Path to manifest.json file

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]
    except FileNotFoundError:
        return False, ["Manifest file not found"]

    # Validate required fields
    required_fields = [
        '$schema', 'manifestVersion', 'version', 'id', 'packageName',
        'developer', 'name', 'description', 'icons', 'accentColor'
    ]

    for field in required_fields:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")

    # Validate manifest version
    if 'manifestVersion' in manifest:
        if manifest['manifestVersion'] < '1.16':
            errors.append(f"Manifest version {manifest['manifestVersion']} is outdated. Use 1.16 or higher.")

    # Validate bot configuration
    if 'bots' in manifest and len(manifest['bots']) > 0:
        bot = manifest['bots'][0]
        if 'botId' not in bot:
            errors.append("Bot configuration missing botId")
        if 'scopes' not in bot:
            errors.append("Bot configuration missing scopes")

    # Validate developer info
    if 'developer' in manifest:
        dev = manifest['developer']
        required_dev_fields = ['name', 'websiteUrl', 'privacyUrl', 'termsOfUseUrl']
        for field in required_dev_fields:
            if field not in dev:
                errors.append(f"Developer section missing {field}")

    # Validate icons
    if 'icons' in manifest:
        icons = manifest['icons']
        if 'color' not in icons or 'outline' not in icons:
            errors.append("Icons section must include both color and outline icons")

    return len(errors) == 0, errors


def validate_bot_id(bot_id: str) -> bool:
    """
    Validate bot ID format (GUID).

    Args:
        bot_id: Bot application ID

    Returns:
        True if valid GUID format
    """
    guid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(guid_pattern, bot_id, re.IGNORECASE))


def validate_required_scopes(manifest: Dict[str, Any]) -> bool:
    """
    Validate that manifest includes required bot scopes.

    Args:
        manifest: Manifest dictionary

    Returns:
        True if required scopes are present
    """
    if 'bots' not in manifest or len(manifest['bots']) == 0:
        return False

    bot = manifest['bots'][0]
    if 'scopes' not in bot:
        return False

    required_scopes = ['personal', 'team']
    bot_scopes = bot['scopes']

    return all(scope in bot_scopes for scope in required_scopes)


def validate_version_format(version: str) -> bool:
    """
    Validate semantic version format (x.y.z).

    Args:
        version: Version string

    Returns:
        True if valid semantic version
    """
    version_pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(version_pattern, version))


def validate_icon_dimensions(icon_path: str, expected_size: Tuple[int, int]) -> Tuple[bool, str]:
    """
    Validate icon dimensions.

    Args:
        icon_path: Path to icon file
        expected_size: Tuple of (width, height)

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        from PIL import Image
        with Image.open(icon_path) as img:
            if img.size != expected_size:
                return False, f"Icon size {img.size} does not match expected {expected_size}"
        return True, ""
    except ImportError:
        # PIL not available, skip dimension check
        return True, ""
    except FileNotFoundError:
        return False, f"Icon file not found: {icon_path}"
    except Exception as e:
        return False, f"Error validating icon: {e}"
