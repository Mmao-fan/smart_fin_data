# fraud_encoder.py
import networkx as nx
from datetime import datetime, timedelta
from typing import List, Dict
from .schemas import TransactionGraphNode, TransactionGraphEdge
from information_extraction.schemas import ProcessedChunk

class FraudEncoder:
    def __init__(self, time_window_minutes: int = 15):
        self.graph = nx.MultiDiGraph()  # 初始化图谱
        self.time_window = timedelta(minutes=time_window_minutes)

    def add_transaction_chunk(self, chunk: ProcessedChunk) -> Dict:
        """处理交易分块数据"""
        # 添加账户节点
        accounts = [e for e in chunk.entities if e.label == "ACCOUNT"]
        for acc in accounts:
            self._add_node(TransactionGraphNode(
                node_id=acc.text,
                node_type="account",
                properties={"last_activity": datetime.now().isoformat()}
            ))

        # 添加交易关系
        for rel in chunk.relations:
            if rel.relation_type == "TRANSFER_TO":
                tx_id = f"tx_{rel.source.text}_{rel.target.text}_{datetime.now().timestamp()}"
                self._add_transaction(tx_id, rel.source.text, rel.target.text)

        return {
            "original_text": chunk.original_text,
            "graph": self.graph,
            "anomalies": self.detect_suspicious_patterns()
        }

    def _add_transaction(self, tx_id: str, source: str, target: str) -> None:
        """添加交易节点和边"""
        tx_node = TransactionGraphNode(
            node_id=tx_id,
            node_type="transaction",
            properties={"timestamp": datetime.now().isoformat()}
        )
        self._add_node(tx_node)
        self._add_edge(TransactionGraphEdge(
            source_id=source,
            target_id=tx_id,
            relation_type="initiated"
        ))
        self._add_edge(TransactionGraphEdge(
            source_id=tx_id,
            target_id=target,
            relation_type="sent_to"
        ))

    def _add_node(self, node: TransactionGraphNode) -> None:
        """添加节点到图谱"""
        if not self.graph.has_node(node.node_id):
            self.graph.add_node(node.node_id, **node.model_dump())

    def _add_edge(self, edge: TransactionGraphEdge) -> None:
        """添加边到图谱"""
        self.graph.add_edge(edge.source_id, edge.target_id, **edge.model_dump())

    def detect_suspicious_patterns(self) -> List[Dict]:
        """检测可疑交易模式"""
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
        """判断交易是否高频"""
        timestamps = [
            datetime.fromisoformat(data.get("timestamp", ""))
            for _, _, data in edges
            if data.get("timestamp")
        ]
        if len(timestamps) < 3:
            return False
        return (max(timestamps) - min(timestamps)) < self.time_window

    def _get_time_range(self, edges: List) -> str:
        """获取交易时间范围"""
        timestamps = [
            datetime.fromisoformat(data.get("timestamp", ""))
            for _, _, data in edges
            if data.get("timestamp")
        ]
        return f"{min(timestamps)} - {max(timestamps)}"