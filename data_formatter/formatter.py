# formatter.py
import json
from typing import List, Dict, Optional
from cryptography.fernet import Fernet, InvalidToken
import logging
import os

class TrainingDataFormatter:
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key
        self._validate_encryption_key()

    def _validate_encryption_key(self) -> None:
        """验证加密密钥格式"""
        if self.encryption_key:
            try:
                Fernet(self.encryption_key.encode())
            except (ValueError, TypeError) as e:
                logging.error(f"无效的加密密钥: {str(e)}")
                raise

    def format_to_jsonl(
        self,
        scene_data: List[Dict],
        output_path: str,
        scene_type: str
    ) -> None:
        """增强异常处理和文件路径校验"""
        if not scene_data:
            logging.warning("输入数据为空，跳过文件生成")
            return

        try:
            formatted_data = []
            for idx, item in enumerate(scene_data):
                try:
                    formatted_item = self._format_item(item, scene_type)
                    formatted_data.append(formatted_item)
                except KeyError as e:
                    logging.error(f"数据项 {idx} 格式错误: 缺少必要字段 {str(e)}")
                    continue

            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 加密处理
            if self.encryption_key:
                self._write_encrypted(formatted_data, output_path)
            else:
                self._write_plaintext(formatted_data, output_path)

        except Exception as e:
            logging.error(f"文件生成失败: {str(e)}")
            raise

    def _format_item(self, item: Dict, scene_type: str) -> Dict:
        """统一格式化入口"""
        formatters = {
            "customer_service": self._format_customer_service,
            "compliance": self._format_compliance,
            "fraud_detection": self._format_fraud_detection
        }
        if scene_type not in formatters:
            raise ValueError(f"未知场景类型: {scene_type}")
        return formatters[scene_type](item)

    def _format_customer_service(self, dialog_data: Dict) -> Dict:
        """增强字段存在性校验"""
        original_text = dialog_data.get("original_text", "")
        dialog = dialog_data.get("dialog", [])

        user_turns = [t for t in dialog if t.get("role") == "user"]
        assistant_turns = [t for t in dialog if t.get("role") == "assistant"]

        return {
            "input": f"场景：客户服务\n输入：{user_turns[0].get('content', '')}" if user_turns else "",
            "target": assistant_turns[0].get('content', "") if assistant_turns else "",
            "original_text": original_text
        }

    def _write_encrypted(self, data: List[Dict], path: str) -> None:
        """封装加密写入逻辑"""
        try:
            fernet = Fernet(self.encryption_key.encode())
            json_str = "\n".join(json.dumps(item, ensure_ascii=False) for item in data)
            encrypted = fernet.encrypt(json_str.encode())
            with open(path, "wb") as f:
                f.write(encrypted)
        except InvalidToken as e:
            logging.error("加密失败: 密钥无效或损坏")
            raise
        except Exception as e:
            logging.error(f"加密写入失败: {str(e)}")
            raise

    # _format_compliance 和 _format_fraud_detection 保持原有逻辑