# anomaly_detector.py
from datetime import datetime
from typing import List, Optional
from .schemas import FinancialEntity
import pytz

class FraudDetector:
    @staticmethod
    def detect_time_anomalies(entities: List[FinancialEntity], chunk: str) -> List[str]:
        """检测时间矛盾（支持多时区校验）"""
        anomalies = []
        time_entities = [e for e in entities if e.label == "DATE"]
        location_entities = [e for e in entities if e.label == "GEO"]

        # 时区映射表（示例数据）
        timezone_map = {
            "New York": "America/New_York",
            "London": "Europe/London",
            "Tokyo": "Asia/Tokyo"
        }

        for time_ent in time_entities:
            time_str = time_ent.text
            # 尝试多种时间格式解析
            parsed_time = None
            for fmt in ["%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M", "%d-%b-%Y %H:%M"]:
                try:
                    parsed_time = datetime.strptime(time_str, fmt)
                    break
                except ValueError:
                    continue
            if not parsed_time:
                continue

            for loc_ent in location_entities:
                location = loc_ent.text
                if location not in timezone_map:
                    continue
                # 转换时区并验证工作时间
                tz = pytz.timezone(timezone_map[location])
                local_time = parsed_time.astimezone(tz)
                if not (9 <= local_time.hour <= 17):
                    anomalies.append(f"非工作时间交易：{time_str} @ {location} (当地时间 {local_time})")
        return anomalies