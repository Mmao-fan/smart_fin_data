# chunk_manager.py
from .chunk_strategies import FixedWindowChunker, SemanticChunker, StructureAwareChunker
from .exceptions import InvalidChunkingMode
from typing import List


class ChunkManager:
    """分块策略协调器"""
    STRATEGY_MAP = {
        "fixed": FixedWindowChunker,
        "semantic": SemanticChunker,
        "structure": StructureAwareChunker
    }

    def __init__(self, mode: str = "structure", **kwargs):
        if mode not in self.STRATEGY_MAP:
            raise InvalidChunkingMode(f"Invalid chunking mode: {mode}")

        self.strategy = self.STRATEGY_MAP[mode](**kwargs)

    def chunk_text(self, text: str) -> List[str]:
        """执行分块处理"""
        if not isinstance(text, str):
            raise ValueError("Input must be a string")

        return self.strategy.chunk(text)