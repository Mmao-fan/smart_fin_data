# fraud_encoder.py
import networkx as nx
from datetime import datetime, timedelta
from typing import List, Dict
from .schemas import TransactionGraphNode, TransactionGraphEdge
from information_extraction.schemas import ProcessedChunk


class FraudEncoder:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.time_window = timedelta(minutes=15)

    def add_transaction_chunk(self, chunk: ProcessedChunk) -> None:
        """将信息提取结果编码为图谱"""
        # 添加账户节点
        accounts = [e for e in chunk.entities if e.label == "ACCOUNT"]
        for acc in accounts:
            node = TransactionGraphNode(
                node_id=acc.text,
                node_type="account",
                properties={"balance": "N/A"}
            )
            self._add_node(node)

        # 添加交易关系
        for rel in chunk.relations:
            if rel.relation_type == "TRANSFER_TO":
                tx_id = f"tx_{len(self.graph.nodes)}"
                tx_node = TransactionGraphNode(
                    node_id=tx_id,
                    node_type="transaction",
                    properties={
                        "amount": rel.source.text,
                        "time": datetime.now().isoformat()
                    }
                )
                self._add_node(tx_node)

                self._add_edge(TransactionGraphEdge(
                    source_id=rel.source.text,
                    target_id=tx_id,
                    relation_type="initiated",
                    properties={}
                ))

                self._add_edge(TransactionGraphEdge(
                    source_id=tx_id,
                    target_id=rel.target.text,
                    relation_type="sent_to",
                    properties={}
                ))

    def detect_suspicious_patterns(self) -> List[Dict]:
        """检测可疑交易模式"""
        patterns = []
        # 模式1：短时间内多笔交易
        for node in self.graph.nodes(data=True):
            if node[1]['node_type'] == 'account':
                edges = list(self.graph.in_edges(node[0], data=True))
                if self._is_high_frequency(edges):
                    patterns.append({
                        "type": "fast_transfer",
                        "account": node[0],
                        "count": len(edges),
                        "time_span": self._get_time_span(edges)
                    })
        return patterns

    def _add_node(self, node: TransactionGraphNode):
        if not self.graph.has_node(node.node_id):
            self.graph.add_node(node.node_id, **node.dict())

    def _add_edge(self, edge: TransactionGraphEdge):
        self.graph.add_edge(
            edge.source_id,
            edge.target_id,
            **edge.dict()
        )

    def _is_high_frequency(self, edges) -> bool:
        times = [e[2].get('properties', {}).get('time') for e in edges]
        valid_times = [datetime.fromisoformat(t) for t in times if t]
        if len(valid_times) < 2:
            return False
        time_diff = max(valid_times) - min(valid_times)
        return time_diff < self.time_window

    def _get_time_span(self, edges) -> str:
        times = [datetime.fromisoformat(e[2].get('properties', {}).get('time')) for e in edges]
        return f"{min(times)} - {max(times)}"