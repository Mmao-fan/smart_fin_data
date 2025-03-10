# fraud_encoder.py
# -*- coding: utf-8 -*-
import networkx as nx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Union
import logging
import pandas as pd


class FraudEncoder:
    def __init__(self, time_window_minutes: int = 15):
        self.graph = nx.MultiDiGraph()
        self.time_window = timedelta(minutes=time_window_minutes)
        self.transactions = []

    def add_transaction_chunk(self, chunk: Union[Dict[str, Any], pd.Series]) -> Dict:
        """处理交易数据块，构建交易关系图"""
        try:
            # 如果是pandas Series，转换为字典
            if isinstance(chunk, pd.Series):
                return self._process_dataframe_row(chunk)
                
            # 如果是文本块，提取实体和关系
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
            logging.error(f"交易处理失败: {str(e)}", exc_info=True)
            return {}

    def _process_dataframe_row(self, row: pd.Series) -> Dict:
        """处理DataFrame中的交易数据行"""
        try:
            # 获取必要的字段
            source_acc = str(row.get('AccountID', ''))
            if not source_acc:
                logging.warning("交易数据缺少AccountID字段")
                return {}
                
            # 获取交易金额
            try:
                amount = float(row.get('TransactionAmount', 0))
            except (ValueError, TypeError):
                amount = 0
                logging.warning(f"交易金额转换失败: {row.get('TransactionAmount')}")
            
            # 获取交易时间
            try:
                if pd.isna(row.get('TransactionDate')):
                    timestamp = datetime.now()
                else:
                    timestamp = pd.to_datetime(row.get('TransactionDate'))
            except Exception:
                timestamp = datetime.now()
                logging.warning(f"交易时间转换失败: {row.get('TransactionDate')}")
            
            # 添加账户节点
            if not self.graph.has_node(source_acc):
                self.graph.add_node(source_acc,
                                  node_type="account",
                                  last_activity=timestamp.isoformat())

            # 添加交易节点
            tx_id = f"tx_{source_acc}_{timestamp.timestamp()}"
            tx_data = {
                "node_type": "transaction",
                "amount": amount,
                "timestamp": timestamp.isoformat(),
                "transaction_type": row.get('TransactionType', ''),
                "location": row.get('Location', ''),
                "device_id": row.get('DeviceID', '')
            }
            
            self.graph.add_node(tx_id, **tx_data)
            self.graph.add_edge(source_acc, tx_id, relation_type="initiated")
            
            # 存储交易记录
            self.transactions.append({
                "transaction_id": tx_id,
                "account_id": source_acc,
                "amount": amount,
                "timestamp": timestamp,
                "type": row.get('TransactionType', ''),
                "location": row.get('Location', ''),
                "device_id": row.get('DeviceID', '')
            })
            
            return self._generate_output(row)

        except Exception as e:
            logging.error(f"DataFrame行处理失败: {str(e)}", exc_info=True)
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
        """生成输出结果"""
        if isinstance(chunk, pd.Series):
            original_data = chunk.to_dict()
        else:
            original_data = getattr(chunk, "original_text", str(chunk))
            
        return {
            "original_data": original_data,
            "nodes_count": len(self.graph.nodes),
            "edges_count": len(self.graph.edges),
            "transactions_count": len(self.transactions)
        }

    def detect_suspicious_patterns(self) -> List[Dict]:
        """检测可疑交易模式"""
        suspicious = []
        
        # 检查高频交易
        account_transactions = {}
        for tx in self.transactions:
            acc_id = tx["account_id"]
            if acc_id not in account_transactions:
                account_transactions[acc_id] = []
            account_transactions[acc_id].append(tx)
        
        # 检查每个账户的交易
        for acc_id, txs in account_transactions.items():
            # 按时间排序
            txs.sort(key=lambda x: x["timestamp"])
            
            # 检查高频交易
            if len(txs) >= 3:
                time_diff = (txs[-1]["timestamp"] - txs[0]["timestamp"]).total_seconds() / 60
                if time_diff < self.time_window.total_seconds() / 60:
                    suspicious.append({
                        "type": "high_frequency_transfer",
                        "account": acc_id,
                        "transaction_count": len(txs),
                        "time_range": f"{txs[0]['timestamp']} - {txs[-1]['timestamp']}"
                    })
            
            # 检查大额交易
            for tx in txs:
                if tx["amount"] > 1000:  # 设置大额交易阈值
                    suspicious.append({
                        "type": "large_amount_transaction",
                        "transaction_id": tx["transaction_id"],
                        "account": acc_id,
                        "amount": tx["amount"],
                        "timestamp": tx["timestamp"].isoformat() if isinstance(tx["timestamp"], datetime) else tx["timestamp"]
                    })

        return suspicious