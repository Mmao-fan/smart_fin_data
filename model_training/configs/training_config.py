from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict
from enum import Enum

class SceneType(str, Enum):
    CUSTOMER_SERVICE = "customer_service"
    FRAUD_DETECTION = "fraud_detection"
    COMPLIANCE = "compliance"

@dataclass
class TrainingConfig:
    # 数据路径与安全配置
    train_data_path: str = "../data/processed/train.jsonl"
    val_data_path: Optional[str] = None
    data_encryption_key: Optional[str] = None

    # 模型与训练配置
    base_model: str = "meta-llama/Llama-2-7b-hf"
    scene_type: SceneType = SceneType.CUSTOMER_SERVICE
    max_seq_length: int = 1024
    batch_size: int = 8
    num_epochs: int = 5

    # LoRA配置
    lora_rank: int = 8
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: Tuple[str, ...] = ("q_proj", "v_proj")

    # 高级配置
    fp16: bool = True
    gradient_accumulation_steps: int = 4
    deepspeed_config: Optional[str] = None
    output_dir: str = "./output"

    # 场景化提示词模板
    prompt_templates: Dict[SceneType, str] = field(
        default_factory=lambda: {
            SceneType.CUSTOMER_SERVICE: "场景：客户服务\n输入：{text}\n回答：",
            SceneType.FRAUD_DETECTION: "分析交易记录：{text}\n异常检测结果：",
            SceneType.COMPLIANCE: "条款原文：{text}\n合规摘要："
        }
    )