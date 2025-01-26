import json
from typing import List, Dict
from cryptography.fernet import Fernet
from scenario_adaptation.schemas import ComplianceClause, DialogTurn
from information_extraction.schemas import ProcessedChunk

class TrainingDataFormatter:
    def __init__(self, encryption_key: str = None):
        self.encryption_key = encryption_key

    def format_to_jsonl(
        self,
        scene_data: List[Dict],
        output_path: str,
        scene_type: str
    ) -> None:
        """将场景数据转换为JSONL格式并保存（可选加密）"""
        formatted_data = []
        for item in scene_data:
            if scene_type == "customer_service":
                formatted_item = self._format_customer_service(item)
            elif scene_type == "compliance":
                formatted_item = self._format_compliance(item)
            elif scene_type == "fraud_detection":
                formatted_item = self._format_fraud_detection(item)
            else:
                raise ValueError(f"未知场景类型: {scene_type}")
            formatted_data.append(formatted_item)

        # 加密数据（如果启用）
        if self.encryption_key:
            encrypted_data = self._encrypt_data(formatted_data)
            with open(output_path, "w") as f:
                f.write(encrypted_data)
        else:
            with open(output_path, "w") as f:
                for item in formatted_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def _format_customer_service(self, dialog_data: Dict) -> Dict:
        """客户服务对话格式化"""
        user_input = next(
            turn["content"] for turn in dialog_data["dialog"]
            if turn["role"] == "user"
        )
        assistant_response = next(
            turn["content"] for turn in dialog_data["dialog"]
            if turn["role"] == "assistant"
        )
        return {
            "input": f"场景：客户服务\n输入：{user_input}",
            "target": assistant_response,
            "original_text": dialog_data["original_text"]
        }

    def _format_compliance(self, clause_data: Dict) -> Dict:
        """合规摘要格式化"""
        return {
            "input": f"条款原文：{clause_data['original_text']}",
            "target": clause_data["clause"].summary,
            "original_text": clause_data["original_text"]
        }

    def _format_fraud_detection(self, graph_data: Dict) -> Dict:
        """欺诈检测图谱格式化"""
        return {
            "input": f"分析交易记录：{graph_data['original_text']}",
            "target": "\n".join(graph_data["anomalies"]),
            "original_text": graph_data["original_text"]
        }

    def _encrypt_data(self, data: List[Dict]) -> str:
        """加密JSONL数据"""
        fernet = Fernet(self.encryption_key)
        json_str = "\n".join([json.dumps(item) for item in data])
        return fernet.encrypt(json_str.encode()).decode()