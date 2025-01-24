from dataclasses import dataclass, field  # 添加 field 的导入
from typing import Dict, List


@dataclass
class EvaluationMetric:
    """单条评估指标配置"""
    name: str
    threshold: float
    weight: float
    higher_better: bool = True


@dataclass
class EvaluationConfig:
    """全局评估配置"""
    scene_metrics: Dict[str, List[EvaluationMetric]] = field(
        default_factory=lambda: {
            "customer_service": [
                EvaluationMetric(
                    name="intent_accuracy",
                    threshold=0.9,
                    weight=0.4
                ),
                EvaluationMetric(
                    name="response_safety",
                    threshold=1.0,
                    weight=0.6
                )
            ],
            "fraud_detection": [
                EvaluationMetric(
                    name="recall",
                    threshold=0.85,
                    weight=0.7
                ),
                EvaluationMetric(
                    name="false_positive_rate",
                    threshold=0.05,
                    weight=0.3,
                    higher_better=False
                )
            ]
        }
    )

    report_settings: Dict = field(
        default_factory=lambda: {
            "format": "markdown",
            "output_dir": "./eval_reports"
        }
    )

    def get_metrics(self, scene_type: str) -> List[EvaluationMetric]:
        return self.scene_metrics.get(scene_type, [])