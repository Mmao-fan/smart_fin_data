# utils.py
from cryptography.fernet import Fernet, InvalidToken
import logging

class EncryptionUtils:
    @staticmethod
    def generate_key() -> str:
        """生成标准Fernet密钥"""
        try:
            return Fernet.generate_key().decode("utf-8")
        except Exception as e:
            logging.error(f"密钥生成失败: {str(e)}")
            raise

    @staticmethod
    def decrypt_data(encrypted_text: str, key: str) -> str:
        """增强解密错误处理"""
        if not key or not encrypted_text:
            logging.error("解密参数缺失")
            raise ValueError("密钥和加密文本不能为空")

        try:
            fernet = Fernet(key.encode())
            return fernet.decrypt(encrypted_text.encode()).decode("utf-8")
        except InvalidToken:
            logging.error("解密失败: 无效的密钥或损坏的密文")
            raise
        except Exception as e:
            logging.error(f"解密过程中发生意外错误: {str(e)}")
            raise