"""Tests for domains.py module (Google Workspace domain management)."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCredentialsManager:
    """Tests for CredentialsManager class."""

    def test_get_credentials_file_not_found(self, tmp_path):
        """Test error when service account file doesn't exist."""
        import domains
        
        # Create a fresh manager for each test
        manager = domains.CredentialsManager()
        
        with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_FILE": "/nonexistent/file.json"}):
            with pytest.raises(FileNotFoundError, match="Service account file not found"):
                manager.get_credentials()

    def test_get_credentials_success(self, tmp_path):
        """Test successful credential loading."""
        import domains
        
        # Create a fresh manager for each test
        manager = domains.CredentialsManager()
        
        mock_credentials = MagicMock()
        
        with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_FILE": str(tmp_path / "sa.json")}):
            with patch("os.path.exists", return_value=True):
                with patch("domains.service_account.Credentials.from_service_account_file") as mock_from_file:
                    mock_from_file.return_value = mock_credentials
                    
                    result = manager.get_credentials()
                    
                    assert result == mock_credentials

    def test_get_credentials_cached(self, tmp_path):
        """Test that credentials are cached after first load."""
        import domains
        
        # Create a fresh manager and set credentials directly
        manager = domains.CredentialsManager()
        mock_credentials = MagicMock()
        manager._credentials = mock_credentials
        
        result = manager.get_credentials()
        
        assert result == mock_credentials

    def test_reset_clears_credentials(self):
        """Test that reset() clears cached credentials."""
        import domains
        
        manager = domains.CredentialsManager()
        manager._credentials = MagicMock()
        
        manager.reset()
        
        assert manager._credentials is None

    def test_get_access_token_refresh_needed(self):
        """Test token refresh when credentials are not valid."""
        import domains
        
        manager = domains.CredentialsManager()
        
        mock_credentials = MagicMock()
        mock_credentials.valid = False
        mock_credentials.token = "refreshed_token"
        manager._credentials = mock_credentials
        
        with patch("domains.Request") as mock_request:
            token = manager.get_access_token()
            
            mock_credentials.refresh.assert_called_once()
            assert token == "refreshed_token"

    def test_get_access_token_already_valid(self):
        """Test token retrieval when credentials are already valid."""
        import domains
        
        manager = domains.CredentialsManager()
        
        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_credentials.token = "existing_token"
        manager._credentials = mock_credentials
        
        token = manager.get_access_token()
        
        mock_credentials.refresh.assert_not_called()
        assert token == "existing_token"


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_credentials_uses_default_manager(self):
        """Test that get_credentials uses the default manager."""
        import domains
        
        mock_credentials = MagicMock()
        
        with patch.object(domains._credentials_manager, "get_credentials", return_value=mock_credentials):
            result = domains.get_credentials()
            assert result == mock_credentials

    def test_get_access_token_uses_default_manager(self):
        """Test that get_access_token uses the default manager."""
        import domains
        
        with patch.object(domains._credentials_manager, "get_access_token", return_value="test_token"):
            result = domains.get_access_token()
            assert result == "test_token"

    def test_reset_credentials_resets_default_manager(self):
        """Test that reset_credentials resets the default manager."""
        import domains
        
        with patch.object(domains._credentials_manager, "reset") as mock_reset:
            domains.reset_credentials()
            mock_reset.assert_called_once()


class TestAddDomainAlias:
    """Tests for add_domain_alias function."""

    @pytest.mark.asyncio
    async def test_add_domain_alias_success(self):
        """Test successful domain alias addition."""
        import domains
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session = MagicMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch.object(domains, "get_access_token", return_value="test_token"):
            await domains.add_domain_alias(mock_session, "alias.example.com", "example.com")
            
            mock_session.post.assert_called_once()
            call_kwargs = mock_session.post.call_args
            assert call_kwargs[1]["json"]["domainName"] == "alias.example.com"
            assert call_kwargs[1]["json"]["parentDomainName"] == "example.com"

    @pytest.mark.asyncio
    async def test_add_domain_alias_failure(self, capsys):
        """Test failed domain alias addition."""
        import domains
        
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Bad Request"
        
        mock_session = MagicMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch.object(domains, "get_access_token", return_value="test_token"):
            await domains.add_domain_alias(mock_session, "alias.example.com", "example.com")
            
            captured = capsys.readouterr()
            assert "Failed to add alias.example.com" in captured.out


class TestBulkUploadDomains:
    """Tests for bulk_upload_domains function."""

    @pytest.mark.asyncio
    async def test_bulk_upload_domains(self, tmp_path):
        """Test bulk domain upload from CSV."""
        import domains
        
        # Create a test CSV file
        csv_file = tmp_path / "test_domains.csv"
        csv_file.write_text("alias_domain,primary_domain\nalias1.com,primary.com\nalias2.com,primary.com\n")
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session = MagicMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch("aiohttp.ClientSession") as mock_client:
            mock_client.return_value.__aenter__.return_value = mock_session
            
            with patch.object(domains, "get_access_token", return_value="test_token"):
                await domains.bulk_upload_domains(str(csv_file))
                
                # Should have been called twice (once for each domain)
                assert mock_session.post.call_count == 2

    @pytest.mark.asyncio
    async def test_bulk_upload_domains_empty_csv(self, tmp_path):
        """Test bulk upload with empty CSV."""
        import domains
        
        # Create an empty CSV file with only headers
        csv_file = tmp_path / "empty_domains.csv"
        csv_file.write_text("alias_domain,primary_domain\n")
        
        mock_session = MagicMock()
        
        with patch("aiohttp.ClientSession") as mock_client:
            mock_client.return_value.__aenter__.return_value = mock_session
            
            with patch.object(domains, "get_access_token", return_value="test_token"):
                await domains.bulk_upload_domains(str(csv_file))
                
                # Should not have been called since CSV is empty
                mock_session.post.assert_not_called()
