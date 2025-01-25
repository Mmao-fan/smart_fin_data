from sklearn.metrics import precision_score, recall_score
from transformers import pipeline
from typing import List, Dict
from configs.training_config import SceneType
import logging
from rouge import Rouge  # 添加Rouge导入
import torch
class FinancialEvaluator:
    def __init__(self, model_path: str, tokenizer_path: str):
        self.pipeline = pipeline(
            "text-generation",
            model=model_path,
            tokenizer=tokenizer_path,
            device=0 if torch.cuda.is_available() else -1
        )

    def evaluate(self, test_data: List[Dict], scene_type: SceneType) -> Dict:
        """场景化评估"""
        results = []
        for item in test_data:
            prompt = item["input"]
            generated = self.pipeline(prompt, max_length=512)[0]['generated_text']
            results.append({
                "pred": generated[len(prompt):].strip(),
                "true": item["target"]
            })

        if scene_type == SceneType.CUSTOMER_SERVICE:
            return self._calc_accuracy(results)
        elif scene_type == SceneType.FRAUD_DETECTION:
            return self._calc_fraud_metrics(results)
        elif scene_type == SceneType.COMPLIANCE:
            return self._calc_rouge(results)
        else:
            logging.warning(f"未知场景类型: {scene_type}")
            return {}

    def _calc_accuracy(self, results: List[Dict]) -> Dict:
        correct = sum(1 for r in results if r["pred"] == r["true"])
        return {"accuracy": correct / len(results)}

    def _calc_fraud_metrics(self, results: List[Dict]) -> Dict:
        y_true = [1 if r["true"] != "" else 0 for r in results]
        y_pred = [1 if r["pred"] != "" else 0 for r in results]
        return {
            "precision": precision_score(y_true, y_pred),
            "recall": recall_score(y_true, y_pred)
        }

    def _calc_rouge(self, results: List[Dict]) -> Dict:
        rouge = Rouge()
        scores = rouge.get_scores(
            [r["pred"] for r in results],
            [r["true"] for r in results],
            avg=True
        )
        return {k: v["f"] for k, v in scores.items()}