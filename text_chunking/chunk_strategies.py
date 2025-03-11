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
    """结构感知分块（基于文档结构特征）"""

    def __init__(self, max_chunk_size: int = 1000, min_chunk_size: int = 100):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        # 增强结构识别模式
        self.section_patterns = [
            # 标题模式
            r'(?:^|\n)#+\s+(.+?)(?:\n|$)',  # Markdown标题
            r'(?:^|\n)第[一二三四五六七八九十\d]+[章节]\s*(.+?)(?:\n|$)',  # 中文章节标题
            r'(?:^|\n)[\d.]+\s+(.+?)(?:\n|$)',  # 数字编号标题
            # 分隔符模式
            r'(?:^|\n)-{3,}(?:\n|$)',  # 短横线分隔符
            r'(?:^|\n)\*{3,}(?:\n|$)',  # 星号分隔符
            r'(?:^|\n)={3,}(?:\n|$)',  # 等号分隔符
            # 特殊结构
            r'(?:^|\n)>(.+?)(?:\n|$)',  # 引用块
            r'(?:^|\n)```.*?```(?:\n|$)',  # 代码块
            r'(?:^|\n)\|.+?\|.+?\|(?:\n|$)'  # 表格行
        ]
        # 优化段落识别
        self.paragraph_pattern = r'(?:^|\n)(.+?)(?:\n\s*\n|$)'
        
    def chunk(self, text: str) -> List[str]:
        """实现结构感知分块逻辑"""
        if not text.strip():
            return []
            
        # 1. 首先按主要结构分割
        sections = self._split_by_structure(text)
        
        # 2. 处理每个结构块
        chunks = []
        for section in sections:
            # 如果部分太大，进一步分割
            if len(section) > self.max_chunk_size:
                sub_chunks = self._split_large_section(section)
                chunks.extend(sub_chunks)
            elif len(section) >= self.min_chunk_size:
                chunks.append(section)
            else:
                # 对于太小的块，尝试与前一个合并
                if chunks and len(chunks[-1]) + len(section) <= self.max_chunk_size:
                    chunks[-1] = chunks[-1] + "\n" + section
                else:
                    chunks.append(section)
                    
        # 3. 确保每个块都有足够的上下文
        chunks = self._ensure_context(chunks)
        
        return chunks
        
    def _split_by_structure(self, text: str) -> List[str]:
        """按文档结构分割文本"""
        # 合并所有结构模式
        combined_pattern = '|'.join(self.section_patterns)
        
        # 找到所有结构边界
        matches = list(re.finditer(combined_pattern, text, re.MULTILINE | re.DOTALL))
        
        if not matches:
            # 如果没有找到结构边界，按段落分割
            return self._split_by_paragraphs(text)
            
        # 按结构边界分割
        sections = []
        start_pos = 0
        
        for match in matches:
            # 添加当前边界前的内容
            if match.start() > start_pos:
                section_text = text[start_pos:match.start()].strip()
                if section_text:
                    sections.append(section_text)
                    
            # 添加当前边界的内容
            section_text = match.group(0).strip()
            if section_text:
                sections.append(section_text)
                
            start_pos = match.end()
            
        # 添加最后一个边界后的内容
        if start_pos < len(text):
            section_text = text[start_pos:].strip()
            if section_text:
                sections.append(section_text)
                
        return sections
        
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        paragraphs = re.findall(self.paragraph_pattern, text, re.MULTILINE | re.DOTALL)
        return [p.strip() for p in paragraphs if p.strip()]
        
    def _split_large_section(self, section: str) -> List[str]:
        """分割大型段落"""
        # 首先尝试按句子分割
        sentences = re.split(r'(?<=[.!?。！？])\s+', section)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 如果当前句子本身就超过最大块大小，直接添加为一个块
            if len(sentence) > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                # 按字符分割超长句子
                for i in range(0, len(sentence), self.max_chunk_size):
                    chunks.append(sentence[i:i+self.max_chunk_size])
            # 否则尝试添加到当前块
            elif len(current_chunk) + len(sentence) <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            # 如果添加会超过最大块大小，创建新块
            else:
                chunks.append(current_chunk)
                current_chunk = sentence
                
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
        
    def _ensure_context(self, chunks: List[str]) -> List[str]:
        """确保每个块都有足够的上下文"""
        if len(chunks) <= 1:
            return chunks
            
        enhanced_chunks = []
        overlap_size = min(50, self.min_chunk_size // 2)
        
        for i, chunk in enumerate(chunks):
            # 添加前一个块的结尾作为上下文
            if i > 0:
                prev_context = chunks[i-1][-overlap_size:] if len(chunks[i-1]) > overlap_size else chunks[i-1]
                chunk = f"[前文] {prev_context}\n\n{chunk}"
                
            # 添加后一个块的开头作为上下文
            if i < len(chunks) - 1:
                next_context = chunks[i+1][:overlap_size] if len(chunks[i+1]) > overlap_size else chunks[i+1]
                chunk = f"{chunk}\n\n[后文] {next_context}"
                
            enhanced_chunks.append(chunk)
            
        return enhanced_chunks