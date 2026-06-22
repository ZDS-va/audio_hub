from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
import asyncio
from sqlalchemy.orm import Session

from services.tts_service import generate_tts_audio
from services.video_service import extract_audio_from_video
from services.podcast_service import download_xiaoyuzhou_podcast
from utils.file_utils import get_download_path, DOWNLOAD_DIR, ensure_download_dir
from utils.database import AudioRecord, get_db, SessionLocal
from utils.text_parser import parse_txt, parse_epub

app = FastAPI(
    title="Audio Hub API",
    description="音频下载与处理后端接口",
    version="1.0.0"
)

# 确保下载目录存在并挂载为静态文件目录
ensure_download_dir()
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")

# 确保临时文件目录存在
TEMP_DIR = "data/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# 定义请求数据模型
class TTSRequest(BaseModel):
    text: str

class VideoRequest(BaseModel):
    url: str
    cookie: str = None

class PodcastRequest(BaseModel):
    url: str

# ---------------- 异步后台任务 ----------------

async def process_tts_tasks(tasks_info: list):
    """
    实际的 TTS 队列处理任务，防止并发太高，这里顺序处理同一个文件的切片
    """
    for t in tasks_info:
        db = SessionLocal()
        record = None
        try:
            record = db.query(AudioRecord).filter(AudioRecord.task_id == t["task_id"]).first()
            if not record:
                continue
            
            # 标记为处理中
            record.status = "processing"
            db.commit()
            
            # 生成安全的文件名
            safe_title = "".join([c for c in record.title if c.isalnum() or c in [' ', '-', '_']]).strip()
            filename = f"TTS_{safe_title}_{record.task_id}.mp3".replace(" ", "_")
            filepath = get_download_path(filename)
            
            # 调用 edge-tts 生成音频
            voice = t.get("voice", "zh-CN-XiaoxiaoNeural")
            success = await generate_tts_audio(t["text"], filepath, voice=voice)
            
            if success and os.path.exists(filepath):
                record.status = "completed"
                record.filename = filename
                record.file_size = round(os.path.getsize(filepath) / 1024, 2)
            else:
                record.status = "failed"
                record.error_msg = "TTS 服务生成失败"
            db.commit()
            
            # 稍微休息一下，防止被 edge-tts 频率限制
            await asyncio.sleep(1)
            
        except Exception as e:
            if record:
                record.status = "failed"
                record.error_msg = str(e)
                db.commit()
        finally:
            db.close()

async def mock_background_worker(task_id: str, delay: int = 5):
    """
    模拟其他耗时的后台下载/生成任务
    """
    db = SessionLocal()
    try:
        record = db.query(AudioRecord).filter(AudioRecord.task_id == task_id).first()
        if not record: return
        
        record.status = "processing"
        db.commit()
        
        await asyncio.sleep(delay)
        
        filename = f"{record.source_type}_{task_id}.mp3"
        filepath = get_download_path(filename)
        with open(filepath, "w") as f:
            f.write(f"This is a mock audio file for {record.title}")
        
        record.status = "completed"
        record.filename = filename
        record.file_size = round(os.path.getsize(filepath) / 1024, 2)
        db.commit()
    except Exception as e:
        if record:
            record.status = "failed"
            record.error_msg = str(e)
            db.commit()
    finally:
        db.close()

async def process_video_tasks(tasks_info: list):
    """
    处理视频下载任务
    """
    for t in tasks_info:
        db = SessionLocal()
        record = None
        try:
            record = db.query(AudioRecord).filter(AudioRecord.task_id == t["task_id"]).first()
            if not record: continue
            
            record.status = "processing"
            db.commit()
            
            safe_title = "".join([c for c in record.title if c.isalnum() or c in [' ', '-', '_']]).strip()
            filename = f"Video_{safe_title}_{record.task_id}.mp3".replace(" ", "_")
            filepath = get_download_path(filename)
            
            success = await extract_audio_from_video(t["url"], filepath, t.get("cookie"))
            
            if success and os.path.exists(filepath):
                record.status = "completed"
                record.filename = filename
                record.file_size = round(os.path.getsize(filepath) / 1024, 2)
            else:
                record.status = "failed"
                record.error_msg = "视频下载或音频提取失败"
            db.commit()
            
        except Exception as e:
            if record:
                record.status = "failed"
                record.error_msg = str(e)
                db.commit()
        finally:
            db.close()

# ---------------- 业务接口 ----------------

@app.get("/")
async def root():
    return {"message": "Welcome to Audio Hub API"}

@app.get("/api/tts/voices")
async def list_voices():
    """获取所有中文音色"""
    from services.tts_service import get_chinese_voices
    voices = await get_chinese_voices()
    return {"status": "success", "data": voices}

@app.get("/api/tts/preview")
async def preview_voice(voice: str):
    """动态生成一小段试听音频"""
    temp_filename = f"preview_{voice}.mp3"
    filepath = get_download_path(temp_filename)
    
    # 如果本地已经有该音色的试听文件，直接返回
    if not os.path.exists(filepath):
        success = await generate_tts_audio(f"你好，我是 {voice.split('-')[-1].replace('Neural', '')}，欢迎使用音频下载服务。", filepath, voice)
        if not success:
            raise HTTPException(status_code=500, detail="生成试听音频失败")
            
    return {"status": "success", "url": f"/downloads/{temp_filename}"}

class TTSRequest(BaseModel):
    text: str
    voice: str = "zh-CN-XiaoxiaoNeural"

@app.post("/api/tts")
async def tts(req: TTSRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task_id = str(uuid.uuid4())[:8]
    
    new_record = AudioRecord(
        task_id=task_id,
        title=f"纯文本: {req.text[:15]}...",
        source_type="tts",
        source_url=req.text
    )
    db.add(new_record)
    db.commit()
    
    # 提交到后台真实的 TTS 任务执行
    tasks = [{"task_id": task_id, "text": req.text, "voice": req.voice}]
    background_tasks.add_task(process_tts_tasks, tasks)
    return {"status": "success", "message": "TTS任务已提交", "task_id": task_id}

from fastapi import Form
@app.post("/api/tts/file")
async def tts_file(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    voice: str = Form("zh-CN-XiaoxiaoNeural"),
    db: Session = Depends(get_db)
):
    # 保存上传的文件到临时目录
    temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex[:8]}_{file.filename}")
    with open(temp_path, "wb") as f:
        f.write(await file.read())
        
    # 解析和切片
    book_title = os.path.splitext(file.filename)[0]
    try:
        if file.filename.lower().endswith(".epub"):
            chapters = parse_epub(temp_path)
        else:
            chapters = parse_txt(temp_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")
        
    # 批量创建数据库记录和任务信息
    tasks_info = []
    for ch in chapters:
        for part_idx, chunk_text in enumerate(ch["chunks"]):
            task_id = str(uuid.uuid4())[:8]
            
            # 格式化标题：书名 - 章节 (序号)
            part_str = f" (Part {part_idx+1})" if len(ch["chunks"]) > 1 else ""
            title = f"《{book_title}》 {ch['chapter']}{part_str}"
            
            new_record = AudioRecord(
                task_id=task_id,
                title=title[:100],  # 防止标题过长
                book_title=book_title,
                chapter=ch["chapter"],
                part_index=part_idx + 1,
                source_type="tts",
                source_url=file.filename,
                status="pending"
            )
            db.add(new_record)
            tasks_info.append({"task_id": task_id, "text": chunk_text, "voice": voice})
            
    db.commit()
    
    # 异步执行真正的切片 TTS 任务
    if tasks_info:
        background_tasks.add_task(process_tts_tasks, tasks_info)
        
    return {
        "status": "success", 
        "message": f"文件上传成功！已自动拆分为 {len(tasks_info)} 个任务，正在后台排队生成中。"
    }

@app.post("/api/video")
async def video(req: VideoRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    from services.video_service import extract_video_info
    
    try:
        # 提取视频/播放列表信息
        video_entries = await asyncio.to_thread(extract_video_info, req.url, req.cookie)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析视频链接失败: {str(e)}")
        
    tasks_info = []
    for entry in video_entries:
        task_id = str(uuid.uuid4())[:8]
        new_record = AudioRecord(
            task_id=task_id,
            title=f"Video: {entry['title'][:50]}",
            source_type="video",
            source_url=entry['url'],
            status="pending"
        )
        db.add(new_record)
        tasks_info.append({"task_id": task_id, "url": entry['url'], "cookie": req.cookie})
        
    db.commit()
    
    if tasks_info:
        background_tasks.add_task(process_video_tasks, tasks_info)
        
    msg = f"已解析出 {len(tasks_info)} 个视频提取任务并进入后台排队。" if len(tasks_info) > 1 else "视频提取任务已提交。"
    return {"status": "success", "message": msg, "task_id": tasks_info[0]["task_id"] if tasks_info else ""}

@app.post("/api/podcast")
async def podcast(req: PodcastRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task_id = str(uuid.uuid4())[:8]
    
    new_record = AudioRecord(
        task_id=task_id,
        title=f"Podcast: {req.url}",
        source_type="podcast",
        source_url=req.url
    )
    db.add(new_record)
    db.commit()
    
    background_tasks.add_task(mock_background_worker, task_id, 4)
    return {"status": "success", "message": "播客下载任务已提交", "task_id": task_id}

# ---------------- 任务与文件管理接口 ----------------

@app.get("/api/tasks")
async def get_tasks(status: str = "all", page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    query = db.query(AudioRecord)
    
    if status != "all":
        query = query.filter(AudioRecord.status == status)
        
    total = query.count()
    records = query.order_by(AudioRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for r in records:
        result.append({
            "task_id": r.task_id,
            "title": r.title,
            "source_type": r.source_type,
            "status": r.status,
            "file_size": r.file_size,
            "file_url": f"/downloads/{r.filename}" if r.filename and r.status == "completed" else None,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    return {
        "status": "success", 
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "items": result
        }
    }

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    record = db.query(AudioRecord).filter(AudioRecord.task_id == task_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 物理删除文件
    if record.filename:
        filepath = os.path.join(DOWNLOAD_DIR, record.filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
            
    # 彻底从数据库删除记录，防止后台任务还能查到并继续处理
    db.delete(record)
    db.commit()
    return {"status": "success", "message": "任务及文件已彻底删除"}
