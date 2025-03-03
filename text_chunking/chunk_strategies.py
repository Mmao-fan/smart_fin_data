# chunk_strategies.py
from abc import ABC, abstractmethod
from typing import List, Optional
import re
from .exceptions import ChunkingError

class ChunkStrategy(ABC):
    """分块策略抽象基类"""
    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        pass

class FixedWindowChunker(ChunkStrategy):
    """固定窗口分块（按字符长度分割，允许重叠）"""
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.chunk_size = chunk_size
        self.overlap = max(0, min(overlap, chunk_size // 2))

    def chunk(self, text: str) -> List[str]:
        if not text:
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
            from transformers import GPT2TokenizerFast
            self.tokenizer = GPT2TokenizerFast.from_pretrained(model_name)
        except ImportError:
            raise ImportError("请先安装 transformers 库：pip install transformers")
        except Exception as e:
            raise ChunkingError(f"模型加载失败: {str(e)}")
        self.max_tokens = max_tokens

    def chunk(self, text: str) -> List[str]:
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
    """结构感知分块（适配文档处理模块的输出格式）"""
    def __init__(self, chunk_size: int = 1024, pattern: Optional[str] = None):
        self.chunk_size = chunk_size
        self.pattern = re.compile(
            pattern or r'(=== Page \d+ ===|=== Sheet \'.+?\' ===|\n#+\s+|\[Table Start\]|\[Table End\])'
        )

    def chunk(self, text: str) -> List[str]:
        if not text:
            return []
        splits = self.pattern.split(text)
        current_chunk = ""
        chunks = []

        for part in splits:
            if self.pattern.match(part):
                # 结构标记优先分割
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                current_chunk = part
            else:
                current_chunk += part

            # 长度超限时强制分割
            if len(current_chunk) >= self.chunk_size:
                chunks.append(current_chunk)
                current_chunk = ""

        if current_chunk:
            chunks.append(current_chunk)
        return chunks