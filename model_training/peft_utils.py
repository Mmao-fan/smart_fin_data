import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM
import logging

class LoRATuner:
    def __init__(self, config):
        self.config = config

    def prepare_model(self):
        """加载模型并注入LoRA适配器"""
        try:
            # 自动选择计算精度
            torch_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float32
            model = AutoModelForCausalLM.from_pretrained(
                self.config.base_model,
                torch_dtype=torch_dtype,
                device_map="auto"
            )
            # 配置LoRA
            lora_config = LoraConfig(
                r=self.config.lora_rank,
                lora_alpha=self.config.lora_alpha,
                target_modules=self.config.target_modules,
                lora_dropout=self.config.lora_dropout,
                task_type="CAUSAL_LM"
            )
            return get_peft_model(model, lora_config)
        except Exception as e:
            logging.error(f"模型初始化失败: {e}")
            raise