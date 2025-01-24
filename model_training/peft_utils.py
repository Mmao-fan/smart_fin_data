import torch  # 新增导入
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM


class LoRATuner:
    def __init__(self, config):
        self.config = config

    def prepare_model(self):
        """配置LoRA参数高效微调"""
        model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            torch_dtype=torch.bfloat16,  # 使用 torch 数据类型
            device_map="auto"
        )

        lora_config = LoraConfig(
            r=self.config.lora_rank,
            lora_alpha=self.config.lora_alpha,
            target_modules=self.config.target_modules,
            lora_dropout=self.config.lora_dropout,
            task_type="CAUSAL_LM"
        )

        return get_peft_model(model, lora_config)