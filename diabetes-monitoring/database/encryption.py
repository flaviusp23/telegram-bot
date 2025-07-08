from cryptography.fernet import Fernet
from sqlalchemy import TypeDecorator, String
from config import ENCRYPTION_KEY

cipher = Fernet(ENCRYPTION_KEY.encode())

def encrypt_data(data):
    """Encrypt sensitive data before storing"""
    if data:
        return cipher.encrypt(data.encode()).decode()
    return None

def decrypt_data(encrypted_data):
    """Decrypt data when retrieving"""
    if encrypted_data:
        return cipher.decrypt(encrypted_data.encode()).decode()
    return None

class EncryptedType(TypeDecorator):
    """SQLAlchemy type for automatic encryption/decryption"""
    impl = String
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """Encrypt on save"""
        if value is not None:
            return encrypt_data(value)
        return value
    
    def process_result_value(self, value, dialect):
        """Decrypt on load"""
        if value is not None:
            return decrypt_data(value)
        return value