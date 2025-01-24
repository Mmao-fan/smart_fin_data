# exceptions.py
class DocumentProcessingError(Exception):
    """统一文档处理异常，所有处理器均抛出此异常"""
    def __init__(self, message: str):
        super().__init__(message)