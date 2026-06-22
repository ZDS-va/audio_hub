import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# 10-20分钟的语音大约对应 3000-4000 个中文字符 (假设语速 ~200字/分钟)
MAX_CHUNK_LENGTH = 3500

def chunk_text(text: str, max_len: int = MAX_CHUNK_LENGTH) -> list:
    """
    将长文本切片为不超过 max_len 的段落列表
    """
    # 按照换行符切分段落
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
            
        # 如果单个段落就超过了最大长度（极端情况），强行按字符切分
        if len(p) > max_len:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            for i in range(0, len(p), max_len):
                chunks.append(p[i:i+max_len])
            continue
            
        if len(current_chunk) + len(p) > max_len:
            chunks.append(current_chunk)
            current_chunk = p
        else:
            current_chunk += "\n" + p if current_chunk else p
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def parse_txt(file_path: str) -> list:
    """
    解析 txt 文件并切片
    Returns:
        [{"chapter": "全文本", "chunks": ["段落1", "段落2", ...]}]
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    # 对于纯文本，如果没有明显的章节标记，我们就当作只有一章
    # 复杂情况可以使用正则匹配 "第x章" 进行拆分，此处保持通用简单实现
    return [{"chapter": "默认章节", "chunks": chunk_text(text)}]

def parse_epub(file_path: str) -> list:
    """
    解析 epub 文件并按章节切片
    Returns:
        [{"chapter": "第一章", "chunks": ["段落1", "段落2", ...]}, ...]
    """
    book = epub.read_epub(file_path)
    chapters = []
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            html = item.get_content().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator='\n')
            
            # 尝试提取章节标题
            title = item.get_name() # 默认使用内部文件名
            h = soup.find(['h1', 'h2', 'h3'])
            if h and h.get_text().strip():
                title = h.get_text().strip()
                
            chunks = chunk_text(text)
            if chunks:
                chapters.append({
                    "chapter": title[:50], # 限制标题长度
                    "chunks": chunks
                })
                
    return chapters
