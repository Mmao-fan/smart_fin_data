# exceptions.py
class InvalidChunkingMode(Exception):
    """强化异常信息可读性"""
    def __init__(self, invalid_mode: str):
        modes = ["fixed", "semantic", "structure"]
        super().__init__(
            f"无效分块模式 '{invalid_mode}'。可用模式: {', '.join(modes)}"
        )

class ChunkingError(Exception):
    """保留原始错误信息"""
    def __init__(self, original_error: Exception):
        super().__init__(f"分块过程出错: {str(original_error)}")
        self.original_error = original_error