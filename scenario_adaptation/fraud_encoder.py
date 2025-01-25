# fraud_encoder.py
import networkx as nx
from datetime import datetime, timedelta
#from typing import List, Dict
from .schemas import TransactionGraphNode, TransactionGraphEdge
from information_extraction.schemas import ProcessedChunk

class FraudEncoder:
    def __init__(self, time_window_minutes: int = 15):
        self.graph = nx.MultiDiGraph()
        self.time_window = timedelta(minutes=time_window_minutes)

    def add_transaction_chunk(self, chunk: ProcessedChunk) -> None:
        """将交易数据编码为图谱"""
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
        """添加节点到图谱（使用 model_dump 替代已弃用的 dict 方法）"""
        if not self.graph.has_node(node.node_id):
            self.graph.add_node(node.node_id, **node.model_dump())  # 修复点

    def _add_edge(self, edge: TransactionGraphEdge) -> None:
        """添加边到图谱（使用 model_dump 替代已弃用的 dict 方法）"""
        self.graph.add_edge(edge.source_id, edge.target_id, **edge.model_dump())  # 修复点

    # 其他方法保持不变...