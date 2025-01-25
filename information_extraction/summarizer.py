# summarizer.py
from transformers import pipeline
from typing import Optional
import logging

class ComplianceSummarizer:
    def __init__(self):
        try:
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                min_length=30,
                max_length=150,
                truncation=True
            )
        except Exception as e:
            logging.error(f"摘要模型加载失败: {str(e)}")
            self.summarizer = None

    def summarize_regulation(self, text: str) -> Optional[str]:
        if not self.summarizer or len(text) < 50:
            return None
        try:
            return self.summarizer(text, max_length=150)[0]['summary_text']
        except Exception as e:
            logging.error(f"摘要生成失败: {str(e)}")
            return None