# anomaly_detector.py
import logging
import datetime
import pytz
import re
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
        "Tokyo": "Asia/Tokyo",
        "Singapore": "Asia/Singapore"
    }

    @staticmethod
    def detect_time_anomalies(entities: List[FinancialEntity], chunk: str, timezone_mapping: Optional[dict] = None) -> List[str]:
        anomalies = []
        time_entities = [e for e in entities if e.label == "DATE"]
        location_entities = [e for e in entities if e.label == "GEO"]

        timezone_mapping = timezone_mapping or FraudDetector.timezone_map

        for time_ent in time_entities:
            time_str = time_ent.text
            parsed_time = None
            # 支持 ISO 8601 和更多格式
            for fmt in ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M", "%d-%b-%Y %H:%M", "%Y-%m-%d"]:
                try:
                    parsed_time = datetime.datetime.strptime(time_str, fmt)
                    if fmt == "%Y-%m-%d":
                        parsed_time = parsed_time.replace(tzinfo=datetime.timezone.utc)
                    break
                except ValueError:
                    continue
            if not parsed_time:
                logging.warning(f"时间格式无法解析: {time_str}")
                continue

            for loc_ent in location_entities:
                location = loc_ent.text
                if location not in timezone_mapping:
                    continue
                try:
                    tz = pytz.timezone(timezone_mapping[location])
                    local_time = parsed_time.astimezone(tz)
                    if not (9 <= local_time.hour <= 17):
                        anomalies.append(f"非工作时间交易：{time_str} @ {location} (当地时间 {local_time.strftime('%Y-%m-%d %H:%M')})")
                except pytz.exceptions.UnknownTimeZoneError:
                    logging.error(f"未知时区配置: {location}")

        return anomalies

    @staticmethod
    def extract_entities(chunk: str) -> List[FinancialEntity]:
        entities = []
        # 增强日期识别
        date_pattern = r'\d{4}[-/]\d{2}[-/]\d{2}(?:T\d{2}:\d{2})?'
        dates = re.findall(date_pattern, chunk)
        for date in dates:
            entities.append(FinancialEntity(label="DATE", text=date))
        # 扩展地点识别
        locations = re.findall(r'\b(New York|London|Tokyo|Singapore|Hong Kong)\b', chunk, re.IGNORECASE)
        for loc in locations:
            entities.append(FinancialEntity(label="GEO", text=loc.title()))
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