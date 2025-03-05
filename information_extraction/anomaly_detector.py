# anomaly_detector.py
import logging
import datetime
import pytz
from typing import List, Optional, Dict

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class FinancialEntity:
    def __init__(self, label: str, text: str):
        self.label = label
        self.text = text


class FraudDetector:
    timezone_map = {
        "New York": "America/New_York",
        "London": "Europe/London",
        "Tokyo": "Asia/Tokyo"
    }

    @staticmethod
    def detect_time_anomalies(entities: List[FinancialEntity], chunk: str, timezone_mapping: Optional[Dict[str, str]] = None) -> List[str]:
        """检测时间矛盾（支持多时区校验）"""
        anomalies = []
        time_entities = [e for e in entities if e.label == "DATE"]
        location_entities = [e for e in entities if e.label == "GEO"]

        if timezone_mapping is None:
            timezone_mapping = FraudDetector.timezone_map

        for time_ent in time_entities:
            time_str = time_ent.text
            # 尝试多种时间格式解析
            parsed_time = None
            # 这里添加了 %Y-%m-%d 格式
            for fmt in ["%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M", "%d-%b-%Y %H:%M", "%Y-%m-%d"]:
                try:
                    parsed_time = datetime.datetime.strptime(time_str, fmt)
                    break
                except ValueError:
                    logging.warning(f"无法解析时间格式: {time_str}")
                    continue
            if not parsed_time:
                continue

            for loc_ent in location_entities:
                location = loc_ent.text
                if location not in timezone_mapping:
                    continue
                # 转换时区并验证工作时间
                tz = pytz.timezone(timezone_mapping[location])
                local_time = parsed_time.astimezone(tz)
                if not (9 <= local_time.hour <= 17):
                    anomalies.append(f"非工作时间交易：{time_str} @ {location} (当地时间 {local_time})")
        return anomalies

    @staticmethod
    def extract_entities(chunk: str) -> List[FinancialEntity]:
        """
        从文本块中提取实体（简单示例，可替换为更复杂的 NLP 方法）
        """
        import re
        entities = []
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', chunk)
        for date in dates:
            entities.append(FinancialEntity(label="DATE", text=date))
        locations = re.findall(r'(New York|London|Tokyo)', chunk)
        for location in locations:
            entities.append(FinancialEntity(label="GEO", text=location))
        return entities


class AnomalyDetector:
    def __init__(self):
        self.fraud_detector = FraudDetector()

    def process_chunk(self, chunk: str) -> List[str]:
        """
        处理文本块，提取实体并检测时间异常
        """
        entities = self.fraud_detector.extract_entities(chunk)
        anomalies = self.fraud_detector.detect_time_anomalies(entities, chunk)
        return anomalies
