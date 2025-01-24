import torch  # 新增导入
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import pipeline


class FinancialEvaluator:
    def __init__(self, model_path, tokenizer_path):
        self.pipeline = pipeline(
            "text-generation",
            model=model_path,
            tokenizer=tokenizer_path,
            device=0 if torch.cuda.is_available() else -1  # 使用 torch 的 GPU 检测
        )

    def evaluate(self, test_data, scene_type):
        # 原有评估逻辑...
        pass