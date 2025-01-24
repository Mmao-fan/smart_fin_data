from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class TrainingConfig:
    # 数据路径配置
    train_data_path: str = "../data/processed/train.jsonl"
    val_data_path: Optional[str] = None  # 新增验证数据路径

    # 模型与训练配置
    base_model: str = "meta-llama/Llama-2-7b-hf"
    scene_type: str = "customer_service"
    max_seq_length: int = 1024
    batch_size: int = 8
    num_epochs: int = 5

    # LoRA配置
    lora_rank: int = 8
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: Tuple[str] = ("q_proj", "v_proj")

    # 高级配置
    fp16: bool = True
    gradient_accumulation_steps: int = 4
    deepspeed_config: str = "./configs/ds_config.json"