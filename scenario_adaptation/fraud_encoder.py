# fraud_encoder.py
import networkx as nx
from datetime import datetime, timedelta
from typing import List, Dict
import logging


class FraudEncoder:
    def __init__(self, time_window_minutes: int = 15):
        self.graph = nx.MultiDiGraph()
        self.time_window = timedelta(minutes=time_window_minutes)

    def add_transaction_chunk(self, chunk) -> Dict:
        """保持接口不变，优化节点处理逻辑"""
        try:
            accounts = {e.text for e in getattr(chunk, "entities", [])
                        if getattr(e, "label", "") == "ACCOUNT"}

            # 添加账户节点（自动去重）
            for acc in accounts:
                if not self.graph.has_node(acc):
                    self.graph.add_node(acc,
                                        node_type="account",
                                        last_activity=datetime.now().isoformat())

            # 处理交易关系
            for rel in getattr(chunk, "relations", []):
                if getattr(rel, "relation_type", "") == "TRANSFER_TO":
                    self._process_transfer(
                        getattr(rel.source, "text", ""),
                        getattr(rel.target, "text", "")
                    )

            return self._generate_output(chunk)

        except Exception as e:
            logging.error(f"交易处理失败: {str(e)}")
            return {}

    def _process_transfer(self, source: str, target: str):
        """封装交易处理逻辑"""
        if not source or not target:
            return

        tx_id = f"tx_{source}_{target}_{datetime.now().timestamp()}"
        tx_data = {
            "node_type": "transaction",
            "timestamp": datetime.now().isoformat()
        }

        # 添加交易节点和边
        self.graph.add_node(tx_id, **tx_data)
        self.graph.add_edge(source, tx_id, relation_type="initiated")
        self.graph.add_edge(tx_id, target, relation_type="sent_to")

    def _generate_output(self, chunk) -> Dict:
        """保持原有输出格式"""
        return {
            "original_text": getattr(chunk, "original_text", ""),
            "nodes": list(self.graph.nodes(data=True)),
            "edges": list(self.graph.edges(data=True)),
            "anomalies": self.detect_suspicious_patterns()
        }

    def detect_suspicious_patterns(self) -> List[Dict]:
        suspicious = []
        for node in self.graph.nodes:
            if self.graph.nodes[node].get("node_type") != "account":
                continue
            incoming_edges = list(self.graph.in_edges(node, data=True))
            if self._is_high_frequency(incoming_edges):
                suspicious.append({
                    "type": "high_frequency_transfer",
                    "account": node,
                    "transaction_count": len(incoming_edges),
                    "time_range": self._get_time_range(incoming_edges)
                })
        return suspicious

    def _is_high_frequency(self, edges: List) -> bool:
        timestamps = [
            datetime.fromisoformat(data.get("timestamp", ""))
            for _, _, data in edges
            if data.get("timestamp")
        ]
        return len(timestamps) >= 3 and (max(timestamps) - min(timestamps)) < self.time_window

    def _get_time_range(self, edges: List) -> str:
        timestamps = [
            datetime.fromisoformat(data.get("timestamp", ""))
            for _, _, data in edges
            if data.get("timestamp")
        ]
        return f"{min(timestamps)} - {max(timestamps)}"