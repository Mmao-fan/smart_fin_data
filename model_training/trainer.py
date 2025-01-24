import torch
from transformers import (
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
from .peft_utils import LoRATuner
from .data_utils import FinancialDataProcessor
from .configs.training_config import TrainingConfig
from copy import deepcopy


class FinancialTrainer:
    """金融领域模型训练器"""

    def __init__(self, config: TrainingConfig):
        self.config = config

        # 初始化LoRA微调器
        self.tuner = LoRATuner(config)
        self.model = self.tuner.prepare_model()

        # 加载训练数据
        self.train_data = self._load_data(config.train_data_path)

        # 加载验证数据（如果存在）
        self.val_data = None
        if config.val_data_path:
            self.val_data = self._load_data(config.val_data_path)

        # 初始化数据整理器
        self.data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tuner.tokenizer,
            mlm=False
        )

    def _load_data(self, data_path: str) -> Dataset:
        """加载并预处理数据"""
        # 创建临时配置避免修改原始配置
        temp_config = deepcopy(self.config)
        temp_config.train_data_path = data_path

        # 处理数据
        processor = FinancialDataProcessor(temp_config)
        return processor.process()

    def _get_training_args(self) -> TrainingArguments:
        """生成训练参数"""
        return TrainingArguments(
            output_dir=self.config.output_dir,
            per_device_train_batch_size=self.config.batch_size,
            num_train_epochs=self.config.num_epochs,
            learning_rate=self.config.learning_rate,
            warmup_ratio=self.config.warmup_ratio,
            logging_dir=f"{self.config.output_dir}/logs",
            evaluation_strategy="epoch" if self.val_data else "no",
            save_strategy="epoch",
            fp16=self.config.fp16,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            deepspeed=self.config.deepspeed_config,
            report_to=["tensorboard"]
        )

    def train(self):
        """执行训练流程"""
        training_args = self._get_training_args()

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_data,
            eval_dataset=self.val_data,
            data_collator=self.data_collator
        )

        print(f"可训练参数量: {sum(p.numel() for p in self.model.parameters() if p.requires_grad)}")
        trainer.train()

        # 保存完整模型和分词器
        self.model.save_pretrained(self.config.output_dir)
        self.tuner.tokenizer.save_pretrained(self.config.output_dir)