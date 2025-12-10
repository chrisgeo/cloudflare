"""Tests for cloudflare_domains.py module."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the module under test
import cloudflare_domains


class TestLoadCredentialsFromJson:
    """Tests for load_credentials_from_json function."""

    def test_load_credentials_from_json_success(self, tmp_path):
        """Test successful loading of credentials from JSON file."""
        json_file = tmp_path / "credentials.json"
        json_file.write_text('{"api_token": "json_token", "account_id": "json_account"}')

        api_token, account_id = cloudflare_domains.load_credentials_from_json(str(json_file))

        assert api_token == "json_token"
        assert account_id == "json_account"

    def test_load_credentials_from_json_missing_fields(self, tmp_path):
        """Test loading credentials when fields are missing."""
        json_file = tmp_path / "credentials.json"
        json_file.write_text('{"api_token": "json_token"}')

        api_token, account_id = cloudflare_domains.load_credentials_from_json(str(json_file))

        assert api_token == "json_token"
        assert account_id is None


class TestLoadCredentialsFromIni:
    """Tests for load_credentials_from_ini function."""

    def test_load_credentials_from_ini_success(self, tmp_path):
        """Test successful loading of credentials from INI file."""
        ini_file = tmp_path / "credentials.ini"
        ini_file.write_text("[cloudflare]\napi_token = ini_token\naccount_id = ini_account\n")

        api_token, account_id = cloudflare_domains.load_credentials_from_ini(str(ini_file))

        assert api_token == "ini_token"
        assert account_id == "ini_account"

    def test_load_credentials_from_ini_missing_section(self, tmp_path):
        """Test loading credentials when cloudflare section is missing."""
        ini_file = tmp_path / "credentials.ini"
        ini_file.write_text("[other]\nkey = value\n")

        api_token, account_id = cloudflare_domains.load_credentials_from_ini(str(ini_file))

        assert api_token is None
        assert account_id is None


class TestGetApiConfig:
    """Tests for get_api_config function."""

    def test_get_api_config_from_env_success(self):
        """Test successful configuration retrieval from environment variables."""
        with patch.dict(os.environ, {
            "CLOUDFLARE_API_TOKEN": "test_token",
            "CLOUDFLARE_ACCOUNT_ID": "test_account_id"
        }, clear=True):
            with patch("os.path.exists", return_value=False):
                base_url, headers = cloudflare_domains.get_api_config()
                
                assert base_url == "https://api.cloudflare.com/client/v4/accounts/test_account_id/zones"
                assert headers["Authorization"] == "Bearer test_token"
                assert headers["Content-Type"] == "application/json"

    def test_get_api_config_from_json_file(self, tmp_path, monkeypatch):
        """Test loading configuration from JSON credentials file."""
        json_file = tmp_path / "cloudflare_credentials.json"
        json_file.write_text('{"api_token": "json_token", "account_id": "json_account"}')

        monkeypatch.chdir(tmp_path)
        with patch.dict(os.environ, {}, clear=True):
            base_url, headers = cloudflare_domains.get_api_config()
            
            assert base_url == "https://api.cloudflare.com/client/v4/accounts/json_account/zones"
            assert headers["Authorization"] == "Bearer json_token"

    def test_get_api_config_from_ini_file(self, tmp_path, monkeypatch):
        """Test loading configuration from INI credentials file."""
        ini_file = tmp_path / "cloudflare_credentials.ini"
        ini_file.write_text("[cloudflare]\napi_token = ini_token\naccount_id = ini_account\n")

        monkeypatch.chdir(tmp_path)
        with patch.dict(os.environ, {}, clear=True):
            base_url, headers = cloudflare_domains.get_api_config()
            
            assert base_url == "https://api.cloudflare.com/client/v4/accounts/ini_account/zones"
            assert headers["Authorization"] == "Bearer ini_token"

    def test_get_api_config_json_takes_precedence_over_ini(self, tmp_path, monkeypatch):
        """Test that JSON file takes precedence over INI file."""
        json_file = tmp_path / "cloudflare_credentials.json"
        json_file.write_text('{"api_token": "json_token", "account_id": "json_account"}')
        
        ini_file = tmp_path / "cloudflare_credentials.ini"
        ini_file.write_text("[cloudflare]\napi_token = ini_token\naccount_id = ini_account\n")

        monkeypatch.chdir(tmp_path)
        with patch.dict(os.environ, {}, clear=True):
            base_url, headers = cloudflare_domains.get_api_config()
            
            # JSON should take precedence
            assert headers["Authorization"] == "Bearer json_token"

    def test_get_api_config_custom_credentials_file(self, tmp_path):
        """Test loading configuration from custom JSON credentials file path."""
        json_file = tmp_path / "custom_creds.json"
        json_file.write_text('{"api_token": "custom_token", "account_id": "custom_account"}')

        with patch.dict(os.environ, {"CLOUDFLARE_CREDENTIALS_FILE": str(json_file)}, clear=True):
            base_url, headers = cloudflare_domains.get_api_config()
            
            assert headers["Authorization"] == "Bearer custom_token"

    def test_get_api_config_custom_ini_credentials_file(self, tmp_path):
        """Test loading configuration from custom INI credentials file path."""
        ini_file = tmp_path / "custom_creds.ini"
        ini_file.write_text("[cloudflare]\napi_token = custom_ini_token\naccount_id = custom_ini_account\n")

        with patch.dict(os.environ, {"CLOUDFLARE_CREDENTIALS_FILE": str(ini_file)}, clear=True):
            base_url, headers = cloudflare_domains.get_api_config()
            
            assert headers["Authorization"] == "Bearer custom_ini_token"
            assert base_url == "https://api.cloudflare.com/client/v4/accounts/custom_ini_account/zones"

    def test_get_api_config_custom_file_takes_precedence(self, tmp_path, monkeypatch):
        """Test that custom file takes precedence over default files."""
        # Create default JSON file
        default_json = tmp_path / "cloudflare_credentials.json"
        default_json.write_text('{"api_token": "default_token", "account_id": "default_account"}')
        
        # Create custom file in different location
        custom_file = tmp_path / "custom" / "creds.json"
        custom_file.parent.mkdir(parents=True, exist_ok=True)
        custom_file.write_text('{"api_token": "custom_token", "account_id": "custom_account"}')

        monkeypatch.chdir(tmp_path)
        with patch.dict(os.environ, {"CLOUDFLARE_CREDENTIALS_FILE": str(custom_file)}, clear=True):
            base_url, headers = cloudflare_domains.get_api_config()
            
            # Custom file should take precedence
            assert headers["Authorization"] == "Bearer custom_token"

    def test_get_api_config_missing_token(self):
        """Test error when API token is missing."""
        with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "test_account_id"}, clear=True):
            with patch("os.path.exists", return_value=False):
                with pytest.raises(ValueError, match="API token not found"):
                    cloudflare_domains.get_api_config()

    def test_get_api_config_missing_account_id(self):
        """Test error when account ID is missing."""
        with patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "test_token"}, clear=True):
            with patch("os.path.exists", return_value=False):
                with pytest.raises(ValueError, match="account ID not found"):
                    cloudflare_domains.get_api_config()


class TestFetchDomains:
    """Tests for fetch_domains function."""

    @pytest.mark.asyncio
    async def test_fetch_domains_success(self):
        """Test successful domain fetching."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "success": True,
            "result": [{"name": "example.com"}, {"name": "example.org"}]
        }
        
        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        base_url = "https://api.cloudflare.com/client/v4/accounts/test/zones"
        headers = {"Authorization": "Bearer test"}
        
        result = await cloudflare_domains.fetch_domains(mock_session, base_url, headers, page=1)
        
        assert len(result) == 2
        assert result[0]["name"] == "example.com"

    @pytest.mark.asyncio
    async def test_fetch_domains_empty_result(self):
        """Test fetching when no domains are returned."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "success": True,
            "result": []
        }
        
        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        base_url = "https://api.cloudflare.com/client/v4/accounts/test/zones"
        headers = {"Authorization": "Bearer test"}
        
        result = await cloudflare_domains.fetch_domains(mock_session, base_url, headers)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_domains_api_error(self):
        """Test handling of API errors."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "success": False,
            "errors": [{"message": "Invalid API token"}]
        }
        
        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        base_url = "https://api.cloudflare.com/client/v4/accounts/test/zones"
        headers = {"Authorization": "Bearer test"}
        
        result = await cloudflare_domains.fetch_domains(mock_session, base_url, headers)
        
        assert result == []


class TestSaveDomainsToJson:
    """Tests for save_domains_to_json function."""

    def test_save_domains_to_json(self, tmp_path):
        """Test saving domains to JSON file."""
        domains = [{"name": "example.com"}, {"name": "example.org"}]
        json_file = tmp_path / "test_domains.json"
        
        cloudflare_domains.save_domains_to_json(domains, str(json_file))
        
        assert json_file.exists()
        with open(json_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        assert saved_data == domains

    def test_save_empty_domains(self, tmp_path):
        """Test saving empty domains list."""
        domains = []
        json_file = tmp_path / "empty_domains.json"
        
        cloudflare_domains.save_domains_to_json(domains, str(json_file))
        
        assert json_file.exists()
        with open(json_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        assert saved_data == []


class TestGetAllDomains:
    """Tests for get_all_domains function."""

    @pytest.mark.asyncio
    async def test_get_all_domains_single_page(self):
        """Test fetching all domains when there's only one page."""
        with patch.dict(os.environ, {
            "CLOUDFLARE_API_TOKEN": "test_token",
            "CLOUDFLARE_ACCOUNT_ID": "test_account_id"
        }):
            mock_response_page1 = AsyncMock()
            mock_response_page1.json.return_value = {
                "success": True,
                "result": [{"name": "example.com"}]
            }
            
            mock_response_page2 = AsyncMock()
            mock_response_page2.json.return_value = {
                "success": True,
                "result": []
            }
            
            mock_session = MagicMock()
            mock_session.get.return_value.__aenter__.side_effect = [
                mock_response_page1,
                mock_response_page2
            ]
            
            with patch("aiohttp.ClientSession") as mock_client:
                mock_client.return_value.__aenter__.return_value = mock_session
                
                result = await cloudflare_domains.get_all_domains()
                
                assert len(result) == 1
                assert result[0]["name"] == "example.com"

    @pytest.mark.asyncio
    async def test_get_all_domains_multiple_pages(self):
        """Test fetching all domains with pagination."""
        with patch.dict(os.environ, {
            "CLOUDFLARE_API_TOKEN": "test_token",
            "CLOUDFLARE_ACCOUNT_ID": "test_account_id"
        }):
            mock_response_page1 = AsyncMock()
            mock_response_page1.json.return_value = {
                "success": True,
                "result": [{"name": "example.com"}]
            }
            
            mock_response_page2 = AsyncMock()
            mock_response_page2.json.return_value = {
                "success": True,
                "result": [{"name": "example.org"}]
            }
            
            mock_response_page3 = AsyncMock()
            mock_response_page3.json.return_value = {
                "success": True,
                "result": []
            }
            
            mock_session = MagicMock()
            mock_session.get.return_value.__aenter__.side_effect = [
                mock_response_page1,
                mock_response_page2,
                mock_response_page3
            ]
            
            with patch("aiohttp.ClientSession") as mock_client:
                mock_client.return_value.__aenter__.return_value = mock_session
                
                result = await cloudflare_domains.get_all_domains()
                
                assert len(result) == 2
                assert result[0]["name"] == "example.com"
                assert result[1]["name"] == "example.org"
