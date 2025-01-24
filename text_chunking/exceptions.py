# exceptions.py
class InvalidChunkingMode(Exception):
    """无效的分块模式异常"""
    def __init__(self, message="Unsupported chunking mode"):
        super().__init__(message)

class ChunkingError(Exception):
    """分块过程通用异常"""
    def __init__(self, message="Text chunking failed"):
        super().__init__(message)