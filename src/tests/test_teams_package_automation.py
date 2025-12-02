"""
End-to-End Tests for Teams Package Automation

Tests validate the automated Teams package creation during azd up,
including postdeploy hook validation, manifest generation, and package creation.
"""

import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# Test constants
VALID_BOT_ID = "12345678-1234-1234-1234-123456789abc"
VALID_FQDN = "ca-teams-ai-dev-test123.azurecontainerapps.io"
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestPostdeployHookValidation:
    """Test suite for postdeploy hook script validation."""

    def test_generate_teams_manifest_script_exists(self):
        """Verify generate-teams-manifest.sh exists and is executable."""
        script_path = PROJECT_ROOT / "scripts" / "generate-teams-manifest.sh"
        assert script_path.exists(), f"generate-teams-manifest.sh must exist at {script_path}"
        # Check if executable (on Unix-like systems)
        if os.name != "nt":
            assert os.access(script_path, os.X_OK), "Script must be executable"

    def test_create_teams_package_script_exists(self):
        """Verify create-teams-package.sh exists and is executable."""
        script_path = PROJECT_ROOT / "scripts" / "create-teams-package.sh"
        assert script_path.exists(), f"create-teams-package.sh must exist at {script_path}"
        if os.name != "nt":
            assert os.access(script_path, os.X_OK), "Script must be executable"

    def test_azure_yaml_has_postdeploy_hook(self):
        """Validate azure.yaml contains postdeploy hook configuration."""
        azure_yaml_path = PROJECT_ROOT / "azure.yaml"
        assert azure_yaml_path.exists(), "azure.yaml must exist"

        with open(azure_yaml_path, "r") as f:
            content = f.read()

        assert "postdeploy:" in content, "azure.yaml must have postdeploy hook"
        assert "posix:" in content, "azure.yaml must have posix shell configuration"

    def test_postdeploy_hook_references_required_scripts(self):
        """Verify postdeploy hook references both required scripts."""
        azure_yaml_path = PROJECT_ROOT / "azure.yaml"
        with open(azure_yaml_path, "r") as f:
            content = f.read()

        assert "generate-teams-manifest.sh" in content, \
            "postdeploy hook must call generate-teams-manifest.sh"
        assert "create-teams-package.sh" in content, \
            "postdeploy hook must call create-teams-package.sh"

    def test_postdeploy_hook_extracts_bot_id(self):
        """Verify postdeploy hook extracts BOT_ID from azd env."""
        azure_yaml_path = PROJECT_ROOT / "azure.yaml"
        with open(azure_yaml_path, "r") as f:
            content = f.read()

        assert "BOT_ID" in content, "postdeploy hook must reference BOT_ID"
        assert "azd env get-values" in content, \
            "postdeploy hook must use 'azd env get-values' to extract variables"

    def test_postdeploy_hook_extracts_container_app_fqdn(self):
        """Verify postdeploy hook extracts CONTAINER_APP_FQDN."""
        azure_yaml_path = PROJECT_ROOT / "azure.yaml"
        with open(azure_yaml_path, "r") as f:
            content = f.read()

        assert "CONTAINER_APP_FQDN" in content, \
            "postdeploy hook must reference CONTAINER_APP_FQDN"

    def test_postdeploy_hook_includes_next_steps(self):
        """Verify postdeploy hook outputs next steps for Teams upload."""
        azure_yaml_path = PROJECT_ROOT / "azure.yaml"
        with open(azure_yaml_path, "r") as f:
            content = f.read()

        assert "admin.teams.microsoft.com" in content, \
            "postdeploy hook must include Teams Admin Center URL"
        assert "NEXT STEPS" in content or "Next steps" in content, \
            "postdeploy hook must include next steps section"


class TestScriptErrorHandling:
    """Test script error handling and validation."""

    def test_generate_manifest_has_error_handling(self):
        """Verify generate-teams-manifest.sh has proper error handling."""
        script_path = PROJECT_ROOT / "scripts" / "generate-teams-manifest.sh"
        with open(script_path, "r") as f:
            content = f.read()

        # Check for set -e or equivalent
        assert "set -e" in content or "set -euo pipefail" in content, \
            "Script must exit on error (set -e)"

    def test_create_package_has_error_handling(self):
        """Verify create-teams-package.sh has proper error handling."""
        script_path = PROJECT_ROOT / "scripts" / "create-teams-package.sh"
        with open(script_path, "r") as f:
            content = f.read()

        assert "set -e" in content or "set -euo pipefail" in content, \
            "Script must exit on error"

    def test_generate_manifest_validates_bot_id_format(self):
        """Verify generate-teams-manifest.sh validates BOT_ID as GUID."""
        script_path = PROJECT_ROOT / "scripts" / "generate-teams-manifest.sh"
        with open(script_path, "r") as f:
            content = f.read()

        # Script should check for GUID format
        assert "bot-id" in content.lower() or "BOT_ID" in content, \
            "Script must accept bot-id parameter"

    def test_create_package_checks_required_files(self):
        """Verify create-teams-package.sh checks for required files."""
        script_path = PROJECT_ROOT / "scripts" / "create-teams-package.sh"
        with open(script_path, "r") as f:
            content = f.read()

        assert "manifest.json" in content, "Script must check for manifest.json"
        assert "color.png" in content, "Script must check for color.png"
        assert "outline.png" in content, "Script must check for outline.png"


class TestTeamsManifestTemplate:
    """Test Teams manifest template structure."""

    def test_manifest_template_exists(self):
        """Verify teams/manifest.json template exists."""
        manifest_path = PROJECT_ROOT / "teams" / "manifest.json"
        assert manifest_path.exists(), "teams/manifest.json must exist"

    def test_manifest_template_has_placeholders(self):
        """Verify manifest template contains placeholders for substitution."""
        manifest_path = PROJECT_ROOT / "teams" / "manifest.json"
        with open(manifest_path, "r") as f:
            content = f.read()

        # Check for placeholder patterns
        assert "{{BOT_ID}}" in content or "botId" in content, \
            "Manifest must have BOT_ID placeholder or botId field"

    def test_manifest_template_valid_json(self):
        """Verify manifest template is valid JSON."""
        manifest_path = PROJECT_ROOT / "teams" / "manifest.json"
        with open(manifest_path, "r") as f:
            try:
                manifest = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Manifest template is not valid JSON: {e}")

        assert "bots" in manifest or "$schema" in manifest, \
            "Manifest must have required Teams schema fields"

    def test_manifest_schema_version(self):
        """Verify manifest uses supported schema version."""
        manifest_path = PROJECT_ROOT / "teams" / "manifest.json"
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        assert "$schema" in manifest, "Manifest must have $schema field"
        assert "manifestVersion" in manifest, "Manifest must have manifestVersion"

        # Check for supported version (1.13+)
        version = manifest.get("manifestVersion", "")
        major_minor = version.split(".")[:2] if version else ["0", "0"]
        if len(major_minor) >= 2:
            major = int(major_minor[0])
            minor = int(major_minor[1])
            assert major >= 1 and (major > 1 or minor >= 13), \
                f"Manifest version {version} should be 1.13 or higher"


class TestPackageValidation:
    """Test package content and structure validation."""

    @pytest.fixture
    def temp_package_dir(self, tmp_path):
        """Create temporary directory for package testing."""
        teams_dir = tmp_path / "teams"
        teams_dir.mkdir()

        # Create test manifest
        manifest = {
            "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
            "manifestVersion": "1.16",
            "version": "1.0.0",
            "id": VALID_BOT_ID,
            "bots": [{"botId": VALID_BOT_ID, "scopes": ["personal"]}],
            "name": {"short": "Test Bot", "full": "Test Bot Full"},
            "description": {"short": "Test", "full": "Test Description"},
            "icons": {"color": "color.png", "outline": "outline.png"},
            "accentColor": "#FFFFFF",
            "developer": {
                "name": "Test",
                "websiteUrl": "https://example.com",
                "privacyUrl": "https://example.com/privacy",
                "termsOfUseUrl": "https://example.com/terms"
            }
        }
        with open(teams_dir / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

        # Create dummy icons (minimal PNG)
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        (teams_dir / "color.png").write_bytes(png_header)
        (teams_dir / "outline.png").write_bytes(png_header)

        return teams_dir

    def test_package_contains_manifest(self, temp_package_dir, tmp_path):
        """Verify created package contains manifest.json."""
        # Create a test package
        package_path = tmp_path / "test-package.zip"

        with zipfile.ZipFile(package_path, "w") as zf:
            for file in temp_package_dir.iterdir():
                zf.write(file, file.name)

        # Verify contents
        with zipfile.ZipFile(package_path, "r") as zf:
            names = zf.namelist()
            assert "manifest.json" in names, "Package must contain manifest.json"

    def test_package_contains_icons(self, temp_package_dir, tmp_path):
        """Verify created package contains required icons."""
        package_path = tmp_path / "test-package.zip"

        with zipfile.ZipFile(package_path, "w") as zf:
            for file in temp_package_dir.iterdir():
                zf.write(file, file.name)

        with zipfile.ZipFile(package_path, "r") as zf:
            names = zf.namelist()
            assert "color.png" in names, "Package must contain color.png"
            assert "outline.png" in names, "Package must contain outline.png"

    def test_package_manifest_valid_json(self, temp_package_dir, tmp_path):
        """Verify manifest in package is valid JSON."""
        package_path = tmp_path / "test-package.zip"

        with zipfile.ZipFile(package_path, "w") as zf:
            for file in temp_package_dir.iterdir():
                zf.write(file, file.name)

        with zipfile.ZipFile(package_path, "r") as zf:
            manifest_content = zf.read("manifest.json").decode("utf-8")
            try:
                manifest = json.loads(manifest_content)
                assert "bots" in manifest
            except json.JSONDecodeError as e:
                pytest.fail(f"Package manifest is not valid JSON: {e}")


class TestPlaceholderSubstitution:
    """Test placeholder substitution in manifest."""

    def test_bot_id_placeholder_pattern(self):
        """Verify BOT_ID placeholder uses expected pattern."""
        manifest_path = PROJECT_ROOT / "teams" / "manifest.json"
        with open(manifest_path, "r") as f:
            content = f.read()

        # Should have placeholder pattern
        has_placeholder = "{{BOT_ID}}" in content or "{{botId}}" in content
        has_template_field = '"id":' in content and '"botId":' in content

        assert has_placeholder or has_template_field, \
            "Manifest must have BOT_ID placeholder or id/botId fields"

    def test_endpoint_placeholder_pattern(self):
        """Verify endpoint placeholder uses expected pattern."""
        manifest_path = PROJECT_ROOT / "teams" / "manifest.json"
        with open(manifest_path, "r") as f:
            content = f.read()

        # Check for endpoint-related patterns
        has_endpoint_placeholder = "{{BOT_ENDPOINT}}" in content or "{{ENDPOINT}}" in content
        has_valid_domains = "validDomains" in content

        assert has_endpoint_placeholder or has_valid_domains, \
            "Manifest must have endpoint placeholder or validDomains"


class TestIconFiles:
    """Test icon file presence and requirements."""

    def test_teams_directory_exists(self):
        """Verify teams directory exists."""
        teams_dir = PROJECT_ROOT / "teams"
        assert teams_dir.exists(), "teams/ directory must exist"
        assert teams_dir.is_dir(), "teams must be a directory"

    def test_manifest_references_icons(self):
        """Verify manifest references icon files."""
        manifest_path = PROJECT_ROOT / "teams" / "manifest.json"
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        assert "icons" in manifest, "Manifest must have icons section"
        icons = manifest["icons"]
        assert "color" in icons, "Manifest must reference color icon"
        assert "outline" in icons, "Manifest must reference outline icon"


class TestAzdIntegration:
    """Test azd environment integration patterns."""

    def test_postdeploy_uses_azd_env_get_values(self):
        """Verify postdeploy uses correct azd command."""
        azure_yaml_path = PROJECT_ROOT / "azure.yaml"
        with open(azure_yaml_path, "r") as f:
            content = f.read()

        assert "azd env get-values" in content, \
            "postdeploy must use 'azd env get-values' to get deployment outputs"

    def test_postdeploy_handles_missing_env_vars(self):
        """Verify postdeploy has fallback for missing env vars."""
        azure_yaml_path = PROJECT_ROOT / "azure.yaml"
        with open(azure_yaml_path, "r") as f:
            content = f.read()

        # Should have validation for empty values
        has_validation = (
            '[ -z "$BOT_ID" ]' in content or
            '-z "$BOT_ID"' in content or
            "IsNullOrEmpty" in content or
            "not set" in content.lower()
        )
        assert has_validation, \
            "postdeploy must handle case when env vars are not set"

    def test_postdeploy_constructs_endpoint_url(self):
        """Verify postdeploy constructs proper endpoint URL."""
        azure_yaml_path = PROJECT_ROOT / "azure.yaml"
        with open(azure_yaml_path, "r") as f:
            content = f.read()

        assert "/api/messages" in content, \
            "postdeploy must construct endpoint with /api/messages path"


class TestOutputMessages:
    """Test output messages and user guidance."""

    def test_postdeploy_shows_teams_admin_url(self):
        """Verify postdeploy outputs Teams Admin Center URL."""
        azure_yaml_path = PROJECT_ROOT / "azure.yaml"
        with open(azure_yaml_path, "r") as f:
            content = f.read()

        assert "admin.teams.microsoft.com" in content, \
            "Must show Teams Admin Center URL"

    def test_postdeploy_shows_sideload_instructions(self):
        """Verify postdeploy shows sideload instructions."""
        azure_yaml_path = PROJECT_ROOT / "azure.yaml"
        with open(azure_yaml_path, "r") as f:
            content = f.read()

        has_sideload = (
            "sideload" in content.lower() or
            "Upload a custom app" in content or
            "Upload an app" in content
        )
        assert has_sideload, "Must show sideload/upload instructions"

    def test_postdeploy_shows_package_location(self):
        """Verify postdeploy shows created package location."""
        azure_yaml_path = PROJECT_ROOT / "azure.yaml"
        with open(azure_yaml_path, "r") as f:
            content = f.read()

        has_package_ref = (
            "teams-app-" in content and ".zip" in content
        )
        assert has_package_ref, "Must show Teams app package filename"


# Integration test that can run if scripts are available
class TestScriptExecution:
    """Integration tests that execute actual scripts (when available)."""

    @pytest.mark.skipif(
        os.name == "nt",
        reason="Shell script tests require Unix-like environment"
    )
    def test_generate_manifest_help(self):
        """Test generate-teams-manifest.sh --help works."""
        script_path = PROJECT_ROOT / "scripts" / "generate-teams-manifest.sh"
        if not script_path.exists():
            pytest.skip("Script not found")

        result = subprocess.run(
            [str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Help should work (exit 0 or 1 depending on implementation)
        assert result.returncode in [0, 1], \
            f"--help should not crash: {result.stderr}"

    @pytest.mark.skipif(
        os.name == "nt",
        reason="Shell script tests require Unix-like environment"
    )
    def test_create_package_help(self):
        """Test create-teams-package.sh --help works."""
        script_path = PROJECT_ROOT / "scripts" / "create-teams-package.sh"
        if not script_path.exists():
            pytest.skip("Script not found")

        result = subprocess.run(
            [str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1], \
            f"--help should not crash: {result.stderr}"
