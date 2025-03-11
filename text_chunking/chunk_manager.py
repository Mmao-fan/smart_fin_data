# chunk_manager.py
from .chunk_strategies import FixedWindowChunker, SemanticChunker, StructureAwareChunker
from .exceptions import InvalidChunkingMode, ChunkingError
from typing import List, Dict, Type

class ChunkManager:
    """分块策略协调器（强化类型安全）"""
    STRATEGY_MAP: Dict[str, Type] = {
        "fixed": FixedWindowChunker,
        "semantic": SemanticChunker,
        "structure": StructureAwareChunker
    }

    def __init__(self, mode: str = "structure", **kwargs):
        if mode not in self.STRATEGY_MAP:
            raise InvalidChunkingMode(mode)
        try:
            self.strategy = self.STRATEGY_MAP[mode](**kwargs)
        except Exception as e:
            raise ChunkingError(e) from e  # 保留原始异常堆栈

    def chunk_text(self, text: str) -> List[str]:
        """执行分块处理（强化输入校验）"""
        if not isinstance(text, str):
            raise TypeError(f"需要字符串输入，得到 {type(text).__name__}")
        try:
            return [chunk for chunk in self.strategy.chunk(text) if chunk.strip()]
        except Exception as e:
            raise ChunkingError(e) from e