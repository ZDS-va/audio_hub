import subprocess
import sys
import time
import os

def main():
    print("🚀 正在启动 Audio Hub 服务...\n")
    
    # 启动 FastAPI 后端
    print(">>> 启动 FastAPI 后端 (Port: 8000)")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    )
    
    # 给后端一点时间启动
    time.sleep(2)
    
    # 启动 Streamlit 前端
    print("\n>>> 启动 Streamlit 前端 (Port: 8501)")
    frontend = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py"]
    )
    
    try:
        # 保持主进程运行
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 正在关闭服务...")
        backend.terminate()
        frontend.terminate()
        backend.wait()
        frontend.wait()
        print("服务已关闭。")

if __name__ == "__main__":
    main()
