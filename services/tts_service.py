import edge_tts

def translate_voice_name(voice: dict) -> str:
    short_name = voice['ShortName']
    gender = "女声" if voice['Gender'] == "Female" else "男声"
    
    locale_map = {
        "zh-CN": "大陆普通话",
        "zh-HK": "香港粤语",
        "zh-TW": "台湾普通话",
        "zh-CN-shaanxi": "陕西话",
        "zh-CN-liaoning": "辽宁话",
    }
    locale = voice['Locale']
    locale_str = locale_map.get(locale, locale)
    
    name_part = short_name.replace(f"{locale}-", "").replace("Neural", "")
    name_map = {
        "Xiaoxiao": "晓晓 (温柔亲切)",
        "Yunxi": "云希 (阳光男声/解说)",
        "Yunjian": "云健 (沉稳男声)",
        "Xiaoyi": "晓伊 (亲切女声)",
        "Yunxia": "云夏 (可爱男童)",
        "Yunyao": "云扬 (专业男声)",
        "Xiaochen": "晓辰 (清脆女声)",
        "Xiaohan": "晓涵 (温暖女声)",
        "Xiaomeng": "晓梦 (女童声)",
        "Xiaomo": "晓墨 (清晰女声)",
        "Xiaoqiu": "晓秋 (成熟女声)",
        "Xiaorui": "晓睿 (知性女声)",
        "Xiaoshuang": "晓双 (甜美女声)",
        "Xiaoyan": "晓颜 (自然女声)",
        "Xiaoyou": "晓悠 (活力女声)",
        "Xiaozhen": "晓甄 (干练女声)",
        "Yunfeng": "云枫 (热情男声)",
        "Yunhao": "云皓 (自然男声)",
        "Yunze": "云泽 (悦耳男声)",
        "HiuGaai": "晓佳 (粤语女声)",
        "HiuMaan": "晓曼 (粤语女声)",
        "WanLung": "云龙 (粤语男声)",
        "HsiaoChen": "晓臻 (台腔女声)",
        "HsiaoYu": "晓雨 (台腔女声)",
        "YunJhe": "云哲 (台腔男声)",
    }
    chinese_name = name_map.get(name_part, name_part)
    
    return f"{chinese_name} | {locale_str}·{gender}"

async def get_chinese_voices() -> list:
    """
    获取所有中文音色列表
    """
    try:
        voices = await edge_tts.list_voices()
        # 筛选 zh-CN, zh-HK, zh-TW 等中文音色
        cn_voices = []
        for v in voices:
            if v.get("Locale", "").startswith("zh-"):
                v["DisplayName"] = translate_voice_name(v)
                cn_voices.append(v)
        return cn_voices
    except Exception as e:
        print(f"Failed to list voices: {e}")
        return []

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
