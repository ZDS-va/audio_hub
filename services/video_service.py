import yt_dlp
import asyncio

def extract_video_info(url: str) -> list:
    """
    使用 yt-dlp 解析视频或播放列表的信息
    Returns:
        [{"title": "Video 1", "url": "http..."}, ...]
    """
    ydl_opts = {
        'extract_flat': True, # 只提取信息，不下载，速度快
        'quiet': True,
        'no_warnings': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        entries = []
        if 'entries' in info:
            # 这是一个播放列表
            for idx, entry in enumerate(info['entries']):
                title = entry.get('title', f'Video_{idx+1}')
                entry_url = entry.get('url') or entry.get('webpage_url')
                # 有些平台的 entry url 是相对路径或 id，需要拼装或直接传回
                if not entry_url and entry.get('id'):
                    entry_url = f"https://www.youtube.com/watch?v={entry['id']}" # 假设是youtube
                entries.append({"title": title, "url": entry_url or url})
        else:
            entries.append({"title": info.get('title', 'Unknown Video'), "url": url})
            
        return entries

async def extract_audio_from_video(video_url: str, output_path: str) -> bool:
    """
    从视频链接中提取音频并保存为 mp3 文件
    
    Args:
        video_url (str): 视频链接
        output_path (str): mp3 文件的保存路径
        
    Returns:
        bool: 是否成功提取
    """
    def _download():
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # yt-dlp 会自动加 .mp3，所以去掉传入路径的后缀
            'outtmpl': output_path.replace('.mp3', ''),
            'quiet': True,
            'no_warnings': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            
    try:
        await asyncio.to_thread(_download)
        return True
    except Exception as e:
        print(f"yt-dlp Download Error: {e}")
        return False
