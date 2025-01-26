from cryptography.fernet import Fernet
import logging

class EncryptionUtils:
    @staticmethod
    def generate_key() -> str:
        """生成Fernet加密密钥"""
        return Fernet.generate_key().decode()

    @staticmethod
    def decrypt_data(encrypted_text: str, key: str) -> str:
        """解密数据"""
        try:
            fernet = Fernet(key)
            return fernet.decrypt(encrypted_text.encode()).decode()
        except Exception as e:
            logging.error(f"解密失败: {str(e)}")
            raise