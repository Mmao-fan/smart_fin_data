# chunk_strategies.py
from abc import ABC, abstractmethod
from typing import List
import re


class ChunkStrategy(ABC):
    """分块策略抽象基类"""

    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        pass


class FixedWindowChunker(ChunkStrategy):
    """固定窗口分块（基础策略）"""

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = max(0, min(overlap, chunk_size // 2))

    def chunk(self, text: str) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += (self.chunk_size - self.overlap)
        return chunks


class SemanticChunker(ChunkStrategy):
    """语义感知分块（使用NLP模型）"""

    def __init__(self, model_name: str = "gpt2"):
        from transformers import GPT2TokenizerFast
        self.tokenizer = GPT2TokenizerFast.from_pretrained(model_name)

    def chunk(self, text: str, max_tokens: int = 512) -> List[str]:
        tokens = self.tokenizer.tokenize(text)
        chunks = []
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunks.append(self.tokenizer.convert_tokens_to_string(chunk_tokens))
        return chunks


class StructureAwareChunker(ChunkStrategy):
    """结构感知分块（专为金融文档优化）"""

    def __init__(self, chunk_size: int = 1024):
        self.structure_pattern = re.compile(
            r'(=== Page \d+ ===|=== Sheet \'.+?\' ===|\n#+\s+)'
        )
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> List[str]:
        # 在结构边界处优先分割
        splits = self.structure_pattern.split(text)
        chunks = []
        current_chunk = ""

        for part in splits:
            if self.structure_pattern.match(part):
                if len(current_chunk) + len(part) > self.chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = part
                else:
                    current_chunk += part
            else:
                current_chunk += part

            if len(current_chunk) >= self.chunk_size:
                chunks.append(current_chunk)
                current_chunk = ""

        if current_chunk:
            chunks.append(current_chunk)
        return chunks