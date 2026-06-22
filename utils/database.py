import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# 确保 data 目录存在，用于存放 sqlite 数据库文件
os.makedirs("data", exist_ok=True)
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/audio_hub.db"

# 创建引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # SQLite 需要允许跨线程访问
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class AudioRecord(Base):
    """
    音频下载/生成任务记录表
    """
    __tablename__ = "audio_records"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)      # 任务的唯一标识 (UUID)
    title = Column(String)                                 # 显示名称 (视频标题/播客名/TTS文本)
    book_title = Column(String, nullable=True)             # 书籍名称 (用于TTS切片)
    chapter = Column(String, nullable=True)                # 章节名称 (用于TTS切片)
    part_index = Column(Integer, nullable=True)            # 切片序号 (用于TTS切片)
    source_type = Column(String)                           # 来源类型: 'tts', 'video', 'podcast'
    source_url = Column(String)                            # 原始链接或原始文本
    filename = Column(String, nullable=True)               # 服务器上保存的 mp3 文件名
    file_size = Column(Float, nullable=True)               # 文件大小 (KB)
    status = Column(String, default="pending")             # 状态: pending, processing, completed, failed, deleted
    error_msg = Column(String, nullable=True)              # 如果失败，记录错误信息
    created_at = Column(DateTime, default=datetime.utcnow) # 创建时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # 更新时间

# 创建表
Base.metadata.create_all(bind=engine)

# 依赖注入函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
