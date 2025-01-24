# chunk_manager.py
from .chunk_strategies import FixedWindowChunker, SemanticChunker, StructureAwareChunker
from .exceptions import InvalidChunkingMode, ChunkingError
from typing import List

class ChunkManager:
    """分块策略协调器（统一异常处理）"""
    STRATEGY_MAP = {
        "fixed": FixedWindowChunker,
        "semantic": SemanticChunker,
        "structure": StructureAwareChunker
    }

    def __init__(self, mode: str = "structure", **kwargs):
        if mode not in self.STRATEGY_MAP:
            raise InvalidChunkingMode(f"Invalid chunking mode: {mode}")
        try:
            self.strategy = self.STRATEGY_MAP[mode](**kwargs)
        except Exception as e:
            raise ChunkingError(f"策略初始化失败: {str(e)}")

    def chunk_text(self, text: str) -> List[str]:
        """执行分块处理（统一返回非空列表）"""
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        try:
            chunks = self.strategy.chunk(text)
            return [chunk for chunk in chunks if chunk.strip()]
        except Exception as e:
            raise ChunkingError(f"分块失败: {str(e)}")