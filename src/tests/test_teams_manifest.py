"""
Test Teams App Manifest Generation
Tests manifest generation with environment-specific values
"""
import pytest
import json
from pathlib import Path


class TestTeamsManifest:
    """Test suite for Teams app manifest validation."""

    @pytest.fixture
    def manifest_path(self):
        """Path to Teams manifest file."""
        return Path(__file__).parent.parent.parent / "teams" / "manifest.json"

    @pytest.fixture
    def manifest_data(self, manifest_path):
        """Load manifest data for testing."""
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                return json.load(f)
        return None

    def test_manifest_file_exists(self, manifest_path):
        """Test that manifest.json file exists."""
        assert manifest_path.exists(), "teams/manifest.json must exist"

    def test_manifest_valid_json(self, manifest_path):
        """Test that manifest is valid JSON."""
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        assert data is not None

    def test_manifest_required_fields(self, manifest_data):
        """Test that manifest contains all required fields."""
        assert manifest_data is not None
        required_fields = [
            '$schema',
            'manifestVersion',
            'version',
            'id',
            'packageName',
            'developer',
            'name',
            'description',
            'icons',
            'accentColor',
            'bots',
            'permissions',
            'validDomains'
        ]
        for field in required_fields:
            assert field in manifest_data, f"Manifest missing required field: {field}"

    def test_manifest_schema_version(self, manifest_data):
        """Test manifest uses correct schema version."""
        assert manifest_data is not None
        assert manifest_data['manifestVersion'] >= '1.16'

    def test_manifest_bot_configuration(self, manifest_data):
        """Test bot configuration in manifest."""
        assert manifest_data is not None
        assert 'bots' in manifest_data
        assert len(manifest_data['bots']) > 0

        bot = manifest_data['bots'][0]
        assert 'botId' in bot
        assert 'scopes' in bot
        assert 'personal' in bot['scopes']
        assert 'team' in bot['scopes']

    def test_manifest_bot_capabilities(self, manifest_data):
        """Test bot capabilities configuration."""
        assert manifest_data is not None
        bot = manifest_data['bots'][0]

        # Check command lists exist
        assert 'commandLists' in bot
        assert len(bot['commandLists']) > 0

        # Check personal scope commands
        personal_commands = next(
            (cl for cl in bot['commandLists'] if cl['scopes'] == ['personal']),
            None
        )
        assert personal_commands is not None
        assert 'commands' in personal_commands

    def test_manifest_icons_configuration(self, manifest_data):
        """Test icon configuration in manifest."""
        assert manifest_data is not None
        assert 'icons' in manifest_data

        icons = manifest_data['icons']
        assert 'color' in icons
        assert 'outline' in icons
        assert icons['color'] == 'color.png'
        assert icons['outline'] == 'outline.png'

    def test_manifest_permissions(self, manifest_data):
        """Test permissions configuration."""
        assert manifest_data is not None
        assert 'permissions' in manifest_data

        permissions = manifest_data['permissions']
        assert 'identity' in permissions
        assert 'messageTeamMembers' in permissions

    def test_manifest_valid_domains(self, manifest_data):
        """Test valid domains configuration."""
        assert manifest_data is not None
        assert 'validDomains' in manifest_data
        assert len(manifest_data['validDomains']) > 0

    def test_manifest_developer_info(self, manifest_data):
        """Test developer information."""
        assert manifest_data is not None
        assert 'developer' in manifest_data

        developer = manifest_data['developer']
        assert 'name' in developer
        assert 'websiteUrl' in developer
        assert 'privacyUrl' in developer
        assert 'termsOfUseUrl' in developer

    def test_manifest_placeholder_substitution(self, manifest_data):
        """Test that manifest supports environment variable substitution."""
        assert manifest_data is not None

        # Check for placeholder patterns like {{BOT_ID}}
        manifest_str = json.dumps(manifest_data)

        # Should have placeholders for bot ID and endpoint
        # These will be replaced during deployment
        bot_id = manifest_data['bots'][0]['botId']
        assert '{{BOT_ID}}' in bot_id or bot_id != ''

    def test_manifest_version_format(self, manifest_data):
        """Test version follows semantic versioning."""
        assert manifest_data is not None
        version = manifest_data['version']

        # Should be in format x.y.z
        parts = version.split('.')
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()

    def test_color_icon_exists(self):
        """Test that color icon file exists."""
        icon_path = Path(__file__).parent.parent.parent / "teams" / "color.png"
        assert icon_path.exists(), "teams/color.png must exist"

    def test_outline_icon_exists(self):
        """Test that outline icon file exists."""
        icon_path = Path(__file__).parent.parent.parent / "teams" / "outline.png"
        assert icon_path.exists(), "teams/outline.png must exist"


class TestManifestGeneration:
    """Test suite for manifest generation script."""

    def test_generate_manifest_script_exists(self):
        """Test that manifest generation script exists."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "generate-teams-manifest.sh"
        assert script_path.exists()

    def test_generate_manifest_executable(self):
        """Test that manifest generation script is executable."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "generate-teams-manifest.sh"
        assert script_path.stat().st_mode & 0o111  # Check executable bit

    def test_manifest_template_exists(self):
        """Test that manifest template file exists."""
        template_path = Path(__file__).parent.parent.parent / "teams" / "manifest.template.json"
        # Template is optional, but if it exists, should be valid JSON
        if template_path.exists():
            with open(template_path, 'r') as f:
                data = json.load(f)
            assert data is not None

    def test_manifest_generation_with_env_vars(self):
        """Test manifest generation with environment variables."""
        from app.teams.manifest_generator import generate_manifest
        import os

        # Set test environment variables
        os.environ['BOT_ID'] = 'test-bot-id-12345'
        os.environ['BOT_ENDPOINT'] = 'https://test.azurecontainerapps.io/api/messages'
        os.environ['APP_VERSION'] = '1.0.0'

        manifest = generate_manifest()
        assert manifest is not None
        assert manifest['bots'][0]['botId'] == 'test-bot-id-12345'
        assert manifest['version'] == '1.0.0'


class TestManifestValidation:
    """Test suite for manifest schema validation."""

    def test_validate_manifest_against_schema(self):
        """Test manifest validation against Teams schema."""
        from app.teams.manifest_validator import validate_manifest

        manifest_path = Path(__file__).parent.parent.parent / "teams" / "manifest.json"
        if manifest_path.exists():
            is_valid, errors = validate_manifest(str(manifest_path))
            assert is_valid, f"Manifest validation failed: {errors}"

    def test_validate_manifest_bot_id_format(self):
        """Test bot ID format validation."""
        from app.teams.manifest_validator import validate_bot_id

        valid_id = "12345678-1234-1234-1234-123456789012"
        assert validate_bot_id(valid_id)

        invalid_id = "not-a-valid-uuid"
        assert not validate_bot_id(invalid_id)

    def test_validate_manifest_required_scopes(self):
        """Test that manifest includes required bot scopes."""
        from app.teams.manifest_validator import validate_required_scopes

        manifest = {
            'bots': [{
                'scopes': ['personal', 'team', 'groupchat']
            }]
        }
        assert validate_required_scopes(manifest)

        manifest_missing_scopes = {
            'bots': [{
                'scopes': ['personal']
            }]
        }
        assert not validate_required_scopes(manifest_missing_scopes)
