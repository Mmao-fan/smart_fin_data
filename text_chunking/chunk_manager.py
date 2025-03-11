# chunk_manager.py
from .chunk_strategies import FixedWindowChunker, SemanticChunker, StructureAwareChunker
from .exceptions import InvalidChunkingMode, ChunkingError
from typing import List, Dict, Type, Optional
import re
import logging

class ChunkManager:
    """文本分块管理器，用于将长文本分割成适当大小的块"""
    
    def __init__(self, max_chunk_size: int = 1000, overlap: int = 100):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.logger = logging.getLogger(__name__)
    
    def split_text(self, text: str) -> List[str]:
        """将文本分割成块"""
        try:
            if not text:
                return []
            
            # 按段落分割
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
            
            chunks = []
            current_chunk = []
            current_size = 0
            
            for para in paragraphs:
                para_size = len(para)
                
                # 如果当前段落加上已有内容超过最大大小，保存当前块并开始新块
                if current_size + para_size > self.max_chunk_size and current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    # 保留最后一个段落作为重叠部分
                    if current_chunk and self.overlap > 0:
                        current_chunk = [current_chunk[-1]]
                        current_size = len(current_chunk[-1])
                    else:
                        current_chunk = []
                        current_size = 0
                
                current_chunk.append(para)
                current_size += para_size
            
            # 添加最后一个块
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"文本分块失败: {str(e)}")
            return [text]  # 如果分块失败，返回原始文本作为单个块

    def chunk_text(self, text: str) -> List[str]:
        """执行分块处理（强化输入校验）"""
        if not isinstance(text, str):
            raise TypeError(f"需要字符串输入，得到 {type(text).__name__}")
        try:
            return [chunk for chunk in self.strategy.chunk(text) if chunk.strip()]
        except Exception as e:
            raise ChunkingError(e) from e