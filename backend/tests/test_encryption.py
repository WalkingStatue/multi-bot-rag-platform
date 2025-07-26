"""
Unit tests for encryption utilities.
"""
import pytest
from unittest.mock import patch

from app.utils.encryption import encrypt_api_key, decrypt_api_key, _get_encryption_key


class TestEncryption:
    """Test cases for encryption utilities."""
    
    def test_get_encryption_key_consistent(self):
        """Test that encryption key generation is consistent."""
        # Act
        key1 = _get_encryption_key()
        key2 = _get_encryption_key()
        
        # Assert
        assert key1 == key2
        assert len(key1) == 44  # Base64 encoded 32 bytes
    
    def test_encrypt_decrypt_api_key(self):
        """Test API key encryption and decryption."""
        # Arrange
        original_key = "sk-test123456789abcdef"
        
        # Act
        encrypted = encrypt_api_key(original_key)
        decrypted = decrypt_api_key(encrypted)
        
        # Assert
        assert encrypted != original_key
        assert decrypted == original_key
        assert isinstance(encrypted, str)
        assert isinstance(decrypted, str)
    
    def test_encrypt_api_key_different_results(self):
        """Test that encryption produces different results each time."""
        # Arrange
        api_key = "sk-test123456789abcdef"
        
        # Act
        encrypted1 = encrypt_api_key(api_key)
        encrypted2 = encrypt_api_key(api_key)
        
        # Assert
        assert encrypted1 != encrypted2  # Fernet includes random IV
        assert decrypt_api_key(encrypted1) == api_key
        assert decrypt_api_key(encrypted2) == api_key
    
    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        # Arrange
        empty_key = ""
        
        # Act
        encrypted = encrypt_api_key(empty_key)
        decrypted = decrypt_api_key(encrypted)
        
        # Assert
        assert decrypted == empty_key
    
    def test_encrypt_unicode_string(self):
        """Test encryption of unicode string."""
        # Arrange
        unicode_key = "sk-test-🔑-unicode"
        
        # Act
        encrypted = encrypt_api_key(unicode_key)
        decrypted = decrypt_api_key(encrypted)
        
        # Assert
        assert decrypted == unicode_key
    
    def test_decrypt_invalid_data(self):
        """Test decryption with invalid encrypted data."""
        # Arrange
        invalid_encrypted = "invalid_encrypted_data"
        
        # Act & Assert
        with pytest.raises(Exception):
            decrypt_api_key(invalid_encrypted)
    
    def test_decrypt_corrupted_data(self):
        """Test decryption with corrupted encrypted data."""
        # Arrange
        api_key = "sk-test123456789abcdef"
        encrypted = encrypt_api_key(api_key)
        
        # Corrupt the encrypted data
        corrupted = encrypted[:-5] + "xxxxx"
        
        # Act & Assert
        with pytest.raises(Exception):
            decrypt_api_key(corrupted)
    
    @patch('app.utils.encryption.settings')
    def test_encryption_with_different_secret_keys(self, mock_settings):
        """Test that different secret keys produce different encryption results."""
        # Arrange
        api_key = "sk-test123456789abcdef"
        
        # First encryption with secret key 1
        mock_settings.secret_key = "secret_key_1"
        encrypted1 = encrypt_api_key(api_key)
        
        # Second encryption with secret key 2
        mock_settings.secret_key = "secret_key_2"
        encrypted2 = encrypt_api_key(api_key)
        
        # Assert
        assert encrypted1 != encrypted2
        
        # Verify each can be decrypted with its respective key
        mock_settings.secret_key = "secret_key_1"
        assert decrypt_api_key(encrypted1) == api_key
        
        mock_settings.secret_key = "secret_key_2"
        assert decrypt_api_key(encrypted2) == api_key
    
    @patch('app.utils.encryption.settings')
    def test_decrypt_with_wrong_secret_key(self, mock_settings):
        """Test that decryption fails with wrong secret key."""
        # Arrange
        api_key = "sk-test123456789abcdef"
        
        # Encrypt with secret key 1
        mock_settings.secret_key = "secret_key_1"
        encrypted = encrypt_api_key(api_key)
        
        # Try to decrypt with secret key 2
        mock_settings.secret_key = "secret_key_2"
        
        # Act & Assert
        with pytest.raises(Exception):
            decrypt_api_key(encrypted)