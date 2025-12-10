"""Tests for cloudflare_domains_global_key.py module."""

import json
import os
from unittest.mock import MagicMock, patch



# Import the module under test
import cloudflare_domains_global_key


class TestGetAllDomains:
    """Tests for get_all_domains function."""

    def test_get_all_domains_success(self):
        """Test successful domain fetching with SDK."""
        mock_zone1 = MagicMock()
        mock_zone1.name = "example.com"
        mock_zone2 = MagicMock()
        mock_zone2.name = "example.org"
        
        mock_zones = [mock_zone1, mock_zone2]
        
        with patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "test_token"}):
            with patch("cloudflare_domains_global_key.Cloudflare") as mock_cf_class:
                mock_cf = MagicMock()
                mock_cf.zones.list.return_value = mock_zones
                mock_cf_class.return_value = mock_cf
                
                result = cloudflare_domains_global_key.get_all_domains()
                
                assert len(result) == 2
                assert "example.com" in result
                assert "example.org" in result

    def test_get_all_domains_empty(self):
        """Test fetching when no domains exist."""
        with patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "test_token"}):
            with patch("cloudflare_domains_global_key.Cloudflare") as mock_cf_class:
                mock_cf = MagicMock()
                mock_cf.zones.list.return_value = []
                mock_cf_class.return_value = mock_cf
                
                result = cloudflare_domains_global_key.get_all_domains()
                
                assert result == []

    def test_get_all_domains_api_status_error(self):
        """Test handling of API status errors."""
        from cloudflare import APIStatusError
        
        with patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "test_token"}):
            with patch("cloudflare_domains_global_key.Cloudflare") as mock_cf_class:
                mock_cf = MagicMock()
                mock_response = MagicMock()
                mock_response.status_code = 401
                mock_cf.zones.list.side_effect = APIStatusError(
                    "Unauthorized", response=mock_response, body={}
                )
                mock_cf_class.return_value = mock_cf
                
                result = cloudflare_domains_global_key.get_all_domains()
                
                assert result == []

    def test_get_all_domains_connection_error(self):
        """Test handling of connection errors."""
        from cloudflare import APIConnectionError
        
        with patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "test_token"}):
            with patch("cloudflare_domains_global_key.Cloudflare") as mock_cf_class:
                mock_cf = MagicMock()
                mock_cf.zones.list.side_effect = APIConnectionError(
                    request=MagicMock()
                )
                mock_cf_class.return_value = mock_cf
                
                result = cloudflare_domains_global_key.get_all_domains()
                
                assert result == []


class TestSaveDomainsToJson:
    """Tests for save_domains_to_json function."""

    def test_save_domains_to_json(self, tmp_path):
        """Test saving domains to JSON file."""
        domains = ["example.com", "example.org"]
        json_file = tmp_path / "test_domains.json"
        
        cloudflare_domains_global_key.save_domains_to_json(domains, str(json_file))
        
        assert json_file.exists()
        with open(json_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        assert saved_data == domains

    def test_save_empty_domains(self, tmp_path):
        """Test saving empty domains list."""
        domains = []
        json_file = tmp_path / "empty_domains.json"
        
        cloudflare_domains_global_key.save_domains_to_json(domains, str(json_file))
        
        assert json_file.exists()
        with open(json_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        assert saved_data == []


class TestMain:
    """Tests for main function."""

    def test_main_with_domains(self, tmp_path):
        """Test main function when domains are found."""
        mock_zone = MagicMock()
        mock_zone.name = "example.com"
        
        with patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "test_token"}):
            with patch("cloudflare_domains_global_key.Cloudflare") as mock_cf_class:
                mock_cf = MagicMock()
                mock_cf.zones.list.return_value = [mock_zone]
                mock_cf_class.return_value = mock_cf
                
                with patch("cloudflare_domains_global_key.save_domains_to_json") as mock_save:
                    cloudflare_domains_global_key.main()
                    mock_save.assert_called_once_with(["example.com"])

    def test_main_without_domains(self, capsys):
        """Test main function when no domains are found."""
        with patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "test_token"}):
            with patch("cloudflare_domains_global_key.Cloudflare") as mock_cf_class:
                mock_cf = MagicMock()
                mock_cf.zones.list.return_value = []
                mock_cf_class.return_value = mock_cf
                
                cloudflare_domains_global_key.main()
                
                captured = capsys.readouterr()
                assert "No domains found" in captured.out
