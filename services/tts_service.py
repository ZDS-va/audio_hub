import edge_tts

async def generate_tts_audio(text: str, output_path: str, voice: str = "zh-CN-XiaoxiaoNeural") -> bool:
    """
    将文本转换为语音并保存为 mp3 文件，使用 edge-tts
    
    Args:
        text (str): 需要转换的文本
        output_path (str): mp3 文件的保存路径
        voice (str): 音色选择，默认晓晓
        
    Returns:
        bool: 是否成功生成
    """
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"Edge-TTS Generation Error: {e}")
        return False
