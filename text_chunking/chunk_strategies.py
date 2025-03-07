# chunk_strategies.py
from abc import ABC, abstractmethod
from typing import List, Optional, Pattern
import re
import logging
from transformers import GPT2TokenizerFast
from .exceptions import ChunkingError


class ChunkStrategy(ABC):
    """分块策略抽象基类"""

    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        pass


class FixedWindowChunker(ChunkStrategy):
    """固定窗口分块（按字符长度分割，允许重叠）"""

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        if chunk_size <= 0 or overlap < 0:
            raise ValueError("chunk_size必须大于0，overlap必须非负")
        self.chunk_size = chunk_size
        self.overlap = min(overlap, chunk_size // 2)  # 限制最大重叠量

    def chunk(self, text: str) -> List[str]:
        """实现固定窗口分块逻辑"""
        if not text.strip():
            return []

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += (self.chunk_size - self.overlap)
        return chunks


class SemanticChunker(ChunkStrategy):
    """语义感知分块（基于Token边界）"""

    def __init__(self, model_name: str = "gpt2", max_tokens: int = 512):
        try:
            self.tokenizer = GPT2TokenizerFast.from_pretrained(model_name)
        except ImportError:
            raise ImportError("请先安装transformers库：pip install transformers")
        except Exception as e:
            raise ChunkingError(f"模型加载失败: {str(e)}")
        self.max_tokens = max_tokens

    def chunk(self, text: str) -> List[str]:
        """使用分词器分割文本"""
        if not text.strip():
            return []

        try:
            tokens = self.tokenizer.tokenize(text)
            chunks = []
            for i in range(0, len(tokens), self.max_tokens):
                chunk_tokens = tokens[i:i + self.max_tokens]
                chunks.append(self.tokenizer.convert_tokens_to_string(chunk_tokens))
            return chunks
        except Exception as e:
            raise ChunkingError(f"语义分块失败: {str(e)}")


class StructureAwareChunker(ChunkStrategy):
    """结构感知分块（适配文档处理模块的标记）"""
    DOC_MARKERS = [
        r'(?:=== Page \d+ ===)',  # PDF分页
        r'(?:=== Sheet \'.+?\' ===)',  # Excel工作表
        r'(?:\n?#{1,6}\s.+?\n)',  # Word标题（支持1-6级）
        r'(?:\[Table Start\])',  # 表格开始
        r'(?:\[Table End\])'  # 表格结束
    ]

    def __init__(self, chunk_size: int = 1024):
        if chunk_size <= 0:
            raise ValueError("chunk_size必须大于0")
        self.chunk_size = chunk_size
        self.pattern = re.compile("|".join(self.DOC_MARKERS))

    def chunk(self, text: str) -> List[str]:
        """混合结构标记和长度限制的分块逻辑"""
        if not text.strip():
            return []

        chunks = []
        current_chunk = []
        current_length = 0

        # 按结构标记分割
        parts = self.pattern.split(text)
        for part in parts:
            if self.pattern.fullmatch(part):  # 结构标记
                if current_chunk:
                    chunks.append("".join(current_chunk))
                    current_chunk = []
                    current_length = 0
                current_chunk.append(part)
                current_length += len(part)
            else:  # 普通文本
                for sentence in re.split(r'(?<=[。！？.?!])', part):  # 按句子分割
                    sent_len = len(sentence)
                    if current_length + sent_len > self.chunk_size:
                        if current_chunk:
                            chunks.append("".join(current_chunk))
                            current_chunk = []
                            current_length = 0
                    current_chunk.append(sentence)
                    current_length += sent_len

        if current_chunk:
            chunks.append("".join(current_chunk))
        return chunks