# summarizer.py
from typing import Optional
import logging
import re

class ComplianceSummarizer:
    """离线文本摘要生成器"""
    
    def __init__(self):
        self.default_max_length = 512
        logging.info("使用离线摘要生成模式")
        
    def _calculate_target_length(self, text: str) -> int:
        """计算目标摘要长度"""
        text_length = len(text)
        if text_length <= 100:
            return text_length  # 文本很短时不做摘要
        elif text_length <= 500:
            return text_length // 2  # 中等长度文本压缩一半
        else:
            return min(text_length // 3, self.default_max_length)  # 长文本压缩为1/3，但不超过默认最大长度

    def summarize_regulation(self, text: str) -> Optional[str]:
        """生成文本摘要"""
        if not text or len(text) < 50:
            return None
            
        target_length = self._calculate_target_length(text)
        return self._generate_offline_summary(text, target_length)
        
    def _generate_offline_summary(self, text: str, target_length: int) -> str:
        """生成离线摘要"""
        try:
            # 1. 分割文本为句子
            sentences = re.split(r'(?<=[。！？.!?])\s*', text)
            if not sentences:
                return self._truncate_text(text, target_length)
                
            # 过滤空句子和过短句子
            sentences = [s for s in sentences if s and len(s.strip()) > 5]
            if not sentences:
                return self._truncate_text(text, target_length)
                
            # 2. 计算每个句子的重要性分数
            word_freq = {}
            for sentence in sentences:
                for word in re.findall(r'[\w\u4e00-\u9fa5]+', sentence):
                    word = word.lower()
                    word_freq[word] = word_freq.get(word, 0) + 1
                    
            # 3. 计算句子得分
            sentence_scores = []
            for i, sentence in enumerate(sentences):
                score = 0
                words = re.findall(r'[\w\u4e00-\u9fa5]+', sentence.lower())
                if not words:
                    continue
                    
                for word in words:
                    score += word_freq.get(word, 0)
                
                # 归一化
                score = score / len(words)
                
                # 给文档开头和结尾的句子加权
                if i < len(sentences) * 0.2:  # 前20%的句子
                    score *= 1.2
                elif i > len(sentences) * 0.8:  # 后20%的句子
                    score *= 1.1
                    
                sentence_scores.append((i, sentence, score))
                
            # 4. 选择得分最高的句子
            if not sentence_scores:
                return self._truncate_text(text, target_length)
                
            sentence_scores.sort(key=lambda x: x[2], reverse=True)
            
            # 5. 根据目标长度选择合适数量的句子
            selected_indices = []
            current_length = 0
            
            for i, sentence, score in sentence_scores:
                if current_length + len(sentence) > target_length:
                    break
                selected_indices.append(i)
                current_length += len(sentence)
            
            # 6. 按原文顺序排列
            selected_indices.sort()
            summary_sentences = [sentences[i] for i in selected_indices]
            
            # 7. 组合摘要
            summary = " ".join(summary_sentences)
            if len(summary) > target_length:
                summary = self._truncate_text(summary, target_length)
                
            return summary
        except Exception as e:
            logging.error(f"摘要生成失败: {str(e)}")
            return self._truncate_text(text, target_length)

    def _truncate_text(self, text: str, max_length: int) -> str:
        """智能截断文本"""
        if len(text) <= max_length:
            return text
            
        # 按句子分割
        sentences = re.split(r'(?<=[。！？.!?])\s*', text)
        truncated_text = ""
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) > max_length - 3:  # 预留"..."的空间
                break
            truncated_text += sentence
            current_length += len(sentence)
            
        return truncated_text + "..."