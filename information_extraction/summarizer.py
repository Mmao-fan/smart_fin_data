# summarizer.py
from transformers import pipeline
from typing import Optional

class ComplianceSummarizer:
    def __init__(self):
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            min_length=30,
            max_length=100
        )

    def summarize_regulation(self, text: str) -> Optional[str]:
        try:
            return self.summarizer(text)[0]['summary_text']
        except:
            return None