# exceptions.py
class DocumentProcessingError(Exception):
    """增强版异常（自动捕获上下文）"""
    def __init__(self, message: str, file_path: str = None):
        if file_path:
            filename = f"[文件: {file_path.split('/')[-1]}] "
            super().__init__(filename + message)
        else:
            super().__init__(message)