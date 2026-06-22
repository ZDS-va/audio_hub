import os

DOWNLOAD_DIR = "downloads"

def ensure_download_dir():
    """
    确保下载目录存在
    """
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

def get_download_path(filename: str) -> str:
    """
    获取安全的下载文件路径，并确保目录存在
    
    Args:
        filename (str): 文件名，例如 'audio.mp3'
        
    Returns:
        str: 完整的文件路径
    """
    ensure_download_dir()
    return os.path.join(DOWNLOAD_DIR, filename)
