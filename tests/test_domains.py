"""Tests for domains.py module (Google Workspace domain management)."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# We need to mock the credentials loading before importing
with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_FILE": "/nonexistent/file.json"}):
    with patch("os.path.exists", return_value=False):
        # Import but don't trigger credential loading yet
        pass


class TestGetCredentials:
    """Tests for get_credentials function."""

    def test_get_credentials_file_not_found(self, tmp_path):
        """Test error when service account file doesn't exist."""
        # Import with mocked environment
        import domains
        
        # Reset the module-level credentials
        domains._credentials = None
        
        with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_FILE": "/nonexistent/file.json"}):
            with pytest.raises(FileNotFoundError, match="Service account file not found"):
                domains.get_credentials()

    def test_get_credentials_success(self, tmp_path):
        """Test successful credential loading."""
        import domains
        
        # Reset the module-level credentials
        domains._credentials = None
        
        mock_credentials = MagicMock()
        
        with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_FILE": str(tmp_path / "sa.json")}):
            with patch("os.path.exists", return_value=True):
                with patch("domains.service_account.Credentials.from_service_account_file") as mock_from_file:
                    mock_from_file.return_value = mock_credentials
                    
                    result = domains.get_credentials()
                    
                    assert result == mock_credentials

    def test_get_credentials_cached(self, tmp_path):
        """Test that credentials are cached after first load."""
        import domains
        
        mock_credentials = MagicMock()
        domains._credentials = mock_credentials
        
        result = domains.get_credentials()
        
        assert result == mock_credentials
        
        # Clean up
        domains._credentials = None


class TestGetAccessToken:
    """Tests for get_access_token function."""

    def test_get_access_token_refresh_needed(self):
        """Test token refresh when credentials are not valid."""
        import domains
        
        mock_credentials = MagicMock()
        mock_credentials.valid = False
        mock_credentials.token = "refreshed_token"
        
        with patch.object(domains, "get_credentials", return_value=mock_credentials):
            with patch("domains.Request") as mock_request:
                token = domains.get_access_token()
                
                mock_credentials.refresh.assert_called_once()
                assert token == "refreshed_token"

    def test_get_access_token_already_valid(self):
        """Test token retrieval when credentials are already valid."""
        import domains
        
        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_credentials.token = "existing_token"
        
        with patch.object(domains, "get_credentials", return_value=mock_credentials):
            token = domains.get_access_token()
            
            mock_credentials.refresh.assert_not_called()
            assert token == "existing_token"


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
