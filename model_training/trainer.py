import os
from transformers import TrainingArguments, Trainer
from .peft_utils import LoRATuner
from .data_utils import FinancialDataProcessor
from configs.training_config import TrainingConfig
import logging
from datetime import datetime

class FinancialTrainer:
    def __init__(self, config: TrainingConfig):
        self.config = config
        os.makedirs(config.output_dir, exist_ok=True)
        self._init_logging()

        self.tuner = LoRATuner(config)
        self.model = self.tuner.prepare_model()
        self.train_data = self._load_data(config.train_data_path)
        self.val_data = self._load_data(config.val_data_path) if config.val_data_path else None

    def _init_logging(self):
        log_file = f"{self.config.output_dir}/training_{datetime.now().strftime('%Y%m%d%H%M')}.log"
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def _load_data(self, data_path: str):
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"数据文件不存在: {data_path}")
        return FinancialDataProcessor(self.config).process()

    def _get_training_args(self) -> TrainingArguments:
        return TrainingArguments(
            output_dir=self.config.output_dir,
            per_device_train_batch_size=self.config.batch_size,
            num_train_epochs=self.config.num_epochs,
            learning_rate=3e-4,
            warmup_ratio=0.1,
            logging_dir=f"{self.config.output_dir}/logs",
            evaluation_strategy="epoch" if self.val_data else "no",
            save_strategy="epoch",
            fp16=self.config.fp16,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            deepspeed=self.config.deepspeed_config,
            report_to=["tensorboard"],
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss" if self.val_data else None
        )

    def train(self):
        training_args = self._get_training_args()
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_data,
            eval_dataset=self.val_data,
        )
        trainer.train()
        self.model.save_pretrained(self.config.output_dir)
        logging.info(f"训练完成，模型已保存至 {self.config.output_dir}")