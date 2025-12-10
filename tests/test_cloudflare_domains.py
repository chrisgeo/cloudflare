"""Tests for cloudflare_domains.py module."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the module under test
import cloudflare_domains


class TestGetApiConfig:
    """Tests for get_api_config function."""

    def test_get_api_config_success(self):
        """Test successful configuration retrieval."""
        with patch.dict(os.environ, {
            "CLOUDFLARE_API_TOKEN": "test_token",
            "CLOUDFLARE_ACCOUNT_ID": "test_account_id"
        }):
            base_url, headers = cloudflare_domains.get_api_config()
            
            assert base_url == "https://api.cloudflare.com/client/v4/accounts/test_account_id/zones"
            assert headers["Authorization"] == "Bearer test_token"
            assert headers["Content-Type"] == "application/json"

    def test_get_api_config_missing_token(self):
        """Test error when API token is missing."""
        with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "test_account_id"}, clear=True):
            with pytest.raises(ValueError, match="CLOUDFLARE_API_TOKEN"):
                cloudflare_domains.get_api_config()

    def test_get_api_config_missing_account_id(self):
        """Test error when account ID is missing."""
        with patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "test_token"}, clear=True):
            with pytest.raises(ValueError, match="CLOUDFLARE_ACCOUNT_ID"):
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
