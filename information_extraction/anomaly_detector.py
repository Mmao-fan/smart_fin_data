# anomaly_detector.py
from datetime import datetime
from typing import List
from .schemas import FinancialEntity  # 确保导入 FinancialEntity


class FraudDetector:
    @staticmethod
    def detect_time_anomalies(entities: List[FinancialEntity], chunk: str) -> List[str]:
        """检测时间矛盾（如交易时间与位置时区不符）"""
        anomalies = []
        time_entities = [e for e in entities if e.label == "DATE"]
        location_entities = [e for e in entities if e.label == "GEO"]

        for time_ent in time_entities:
            time_str = time_ent.text
            try:
                trans_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                for loc_ent in location_entities:
                    if "New York" in loc_ent.text and not (9 <= trans_time.hour <= 17):
                        anomalies.append(f"非工作时间交易：{time_str} @ {loc_ent.text}")
            except ValueError:
                continue
        return anomalies