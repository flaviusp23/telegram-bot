"""Encryption module for sensitive data protection.

This module provides encryption and decryption functionality for sensitive
data stored in the database using Fernet symmetric encryption.
"""
import logging
from typing import Optional, Union
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import TypeDecorator, String
from config import ENCRYPTION_KEY

logger = logging.getLogger(__name__)

# Initialize cipher with validation
try:
    if not ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY is not set in configuration")
    
    # Validate the key format
    if isinstance(ENCRYPTION_KEY, str):
        cipher = Fernet(ENCRYPTION_KEY.encode())
    else:
        cipher = Fernet(ENCRYPTION_KEY)
        
    # Test the cipher to ensure it's working
    test_data = b"test"
    cipher.decrypt(cipher.encrypt(test_data))
    
except Exception as e:
    logger.error(f"Failed to initialize encryption cipher: {e}")
    raise RuntimeError(f"Encryption initialization failed: {e}")


def encrypt_data(data: Optional[Union[str, bytes]]) -> Optional[str]:
    """Encrypt sensitive data before storing.
    
    Args:
        data: The data to encrypt. Can be string or bytes.
        
    Returns:
        Encrypted data as a string, or None if input is None.
        
    Raises:
        ValueError: If encryption fails.
    """
    if data is None:
        return None
        
    try:
        # Convert to bytes if string
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data
            
        # Encrypt and return as string
        encrypted = cipher.encrypt(data_bytes)
        return encrypted.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise ValueError(f"Failed to encrypt data: {e}")


def decrypt_data(encrypted_data: Optional[Union[str, bytes]]) -> Optional[str]:
    """Decrypt data when retrieving.
    
    Args:
        encrypted_data: The encrypted data to decrypt. Can be string or bytes.
        
    Returns:
        Decrypted data as a string, or None if input is None.
        
    Raises:
        ValueError: If decryption fails (e.g., invalid token, corrupted data).
    """
    if encrypted_data is None:
        return None
        
    try:
        # Convert to bytes if string
        if isinstance(encrypted_data, str):
            encrypted_bytes = encrypted_data.encode('utf-8')
        else:
            encrypted_bytes = encrypted_data
            
        # Decrypt and return as string
        decrypted = cipher.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
        
    except InvalidToken as e:
        logger.error(f"Invalid encryption token: {e}")
        raise ValueError("Failed to decrypt data: Invalid or corrupted encryption token")
        
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise ValueError(f"Failed to decrypt data: {e}")


class EncryptedType(TypeDecorator):
    """SQLAlchemy type for automatic encryption/decryption.
    
    This type decorator automatically encrypts data when saving to the database
    and decrypts it when loading from the database.
    """
    impl = String
    cache_ok = True
    
    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Encrypt data before saving to database.
        
        Args:
            value: The value to encrypt.
            dialect: The database dialect (unused).
            
        Returns:
            Encrypted value or None.
        """
        if value is not None:
            try:
                return encrypt_data(value)
            except ValueError as e:
                logger.error(f"Failed to encrypt field value: {e}")
                # Re-raise to prevent saving unencrypted data
                raise
        return value
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Decrypt data when loading from database.
        
        Args:
            value: The encrypted value from database.
            dialect: The database dialect (unused).
            
        Returns:
            Decrypted value or None.
        """
        if value is not None:
            try:
                return decrypt_data(value)
            except ValueError as e:
                logger.error(f"Failed to decrypt field value: {e}")
                # Return None to prevent application crash, but log the error
                return None
        return value