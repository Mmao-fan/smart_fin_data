from datasets import Dataset
from transformers import AutoTokenizer
import json
import logging
from cryptography.fernet import Fernet  # 添加Fernet导入


class FinancialDataProcessor:
    def __init__(self, config):
        self.config = config
        self.tokenizer = AutoTokenizer.from_pretrained(config.base_model)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.max_length = config.max_seq_length

    def _decrypt_data(self, encrypted_text: str) -> str:
        """解密数据"""
        if not self.config.data_encryption_key:
            return encrypted_text
        try:
            fernet = Fernet(self.config.data_encryption_key)
            return fernet.decrypt(encrypted_text.encode()).decode()
        except Exception as e:
            logging.error(f"数据解密失败: {e}")
            raise

    def process(self) -> Dataset:
        """加载并预处理数据"""
        try:
            data = []
            with open(self.config.train_data_path, "r") as f:
                for line in f:
                    encrypted_item = json.loads(line)
                    item = {k: self._decrypt_data(v) if isinstance(v, str) else v
                            for k, v in encrypted_item.items()}
                    prompt = self.config.prompt_templates[self.config.scene_type].format(
                        text=item["original_text"]
                    )
                    target = item.get("summary", item.get("anomalies", ""))
                    data.append({"input": prompt, "target": target})

            def encode(examples):
                model_inputs = self.tokenizer(
                    examples["input"],
                    max_length=self.config.max_seq_length,
                    truncation=True,
                    padding="max_length"
                )
                labels = self.tokenizer(
                    examples["target"],
                    max_length=self.config.max_seq_length,
                    truncation=True,
                    padding="max_length"
                )
                model_inputs["labels"] = labels["input_ids"]
                return model_inputs

            return Dataset.from_list(data).map(encode, batched=True)

        except Exception as e:
            logging.error(f"数据处理失败: {e}")
            raise