import streamlit as st
import requests
import time
import os

st.set_page_config(
    page_title="Audio Hub",
    page_icon="🎧",
    layout="centered"
)

# 读取环境变量，适配 Docker 部署与本地开发
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

st.title("🎧 Audio Hub - 音频下载服务")
st.markdown("欢迎使用音频下载工具。任务已支持后台异步处理，提交后请前往「📂 下载与任务管理」查看进度。")

tab1, tab2, tab3, tab4 = st.tabs([
    "💬 文本转语音", 
    "🎬 视频提取", 
    "🎙️ 播客下载",
    "📂 下载与任务管理"
])

# 辅助函数：提交任务
def submit_task(endpoint, payload):
    try:
        response = requests.post(f"{API_BASE_URL}/{endpoint}", json=payload)
        if response.status_code == 200:
            data = response.json()
            st.success(f"✅ {data['message']} (Task ID: {data['task_id']})")
            st.info("👉 请前往「📂 下载与任务管理」标签页查看任务进度和下载文件。")
        else:
            st.error(f"❌ 提交失败: {response.text}")
    except Exception as e:
        st.error(f"❌ 无法连接到后端服务: {e}")


with tab1:
    st.header("文本转语音 (TTS)")
    
    # 动态获取音色列表
    @st.cache_data(ttl=3600)
    def fetch_voices():
        try:
            res = requests.get(f"{API_BASE_URL}/tts/voices")
            if res.status_code == 200:
                return res.json().get("data", [])
        except:
            pass
        return []
    
    voices = fetch_voices()
    voice_options = {v["ShortName"]: f"{v['FriendlyName']} ({v['Gender']})" for v in voices} if voices else {"zh-CN-XiaoxiaoNeural": "晓晓 (Female)"}
    
    col_v1, col_v2 = st.columns([3, 1])
    with col_v1:
        selected_voice = st.selectbox("选择发音人 (音色)", options=list(voice_options.keys()), format_func=lambda x: voice_options.get(x, x))
    with col_v2:
        st.write("") # 占位对齐
        st.write("")
        if st.button("🔊 试听音色"):
            with st.spinner("生成试听中..."):
                try:
                    preview_res = requests.get(f"{API_BASE_URL}/tts/preview", params={"voice": selected_voice})
                    if preview_res.status_code == 200:
                        preview_url = f"{PUBLIC_BASE_URL}{preview_res.json()['url']}"
                        st.audio(preview_url, format="audio/mp3")
                    else:
                        st.error("试听生成失败")
                except:
                    st.error("无法连接到服务")
    
    st.divider()
    tts_mode = st.radio("选择输入方式", ["文本输入", "文件上传 (.txt / .epub)"])
    
    if tts_mode == "文本输入":
        text_input = st.text_area("请输入要转换的文本")
        if st.button("生成语音"):
            if text_input.strip():
                submit_task("tts", {"text": text_input, "voice": selected_voice})
            else:
                st.warning("请输入需要转换的文本")
    else:
        uploaded_file = st.file_uploader("选择文件", type=["txt", "epub"])
        if st.button("上传并切片生成"):
            if uploaded_file is not None:
                with st.spinner("正在上传并进行切片处理..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {"voice": selected_voice}
                    try:
                        response = requests.post(f"{API_BASE_URL}/tts/file", files=files, data=data)
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ {data['message']}")
                            st.info("👉 请前往「📂 下载与任务管理」标签页查看切片进度。")
                        else:
                            st.error(f"❌ 提交失败: {response.text}")
                    except Exception as e:
                        st.error(f"❌ 无法连接到后端服务: {e}")
            else:
                st.warning("请先上传文件")

with tab2:
    st.header("视频链接提取音频")
    video_url = st.text_input("请输入视频链接 (例如 B站、YouTube 等)")
    if st.button("提取音频"):
        if video_url.strip():
            submit_task("video", {"url": video_url})
        else:
            st.warning("请输入视频链接")

with tab3:
    st.header("小宇宙播客下载")
    podcast_url = st.text_input("请输入小宇宙播客单集链接")
    if st.button("解析并下载"):
        if podcast_url.strip():
            submit_task("podcast", {"url": podcast_url})
        else:
            st.warning("请输入播客链接")

with tab4:
    st.header("下载与任务管理")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.subheader("🔄 任务与文件列表")
    with col2:
        status_filter = st.selectbox("状态筛选", ["all", "pending", "processing", "completed", "failed"], 
                                     format_func=lambda x: {"all": "全部", "pending": "等待中", "processing": "处理中", "completed": "已完成", "failed": "失败"}.get(x))
    with col3:
        st.write("")
        st.write("")
        if st.button("刷新 🔄"):
            pass
            
    # 状态管理分页
    if "page" not in st.session_state:
        st.session_state.page = 1
            
    try:
        tasks_res = requests.get(f"{API_BASE_URL}/tasks", params={"status": status_filter, "page": st.session_state.page, "page_size": 10}).json()
        data = tasks_res.get("data", {})
        tasks = data.get("items", [])
        total_pages = data.get("total_pages", 1)
        
        if tasks:
            for task in tasks:
                tc1, tc2, tc3 = st.columns([3, 1, 1])
                
                # 状态图标与名称
                status = task["status"]
                if status == "pending":
                    status_icon = "⏳ 等待中"
                elif status == "processing":
                    status_icon = "⚙️ 处理中"
                elif status == "completed":
                    status_icon = "✅ 已完成"
                else:
                    status_icon = "❌ 失败"
                    
                size_str = f" ({task['file_size']} KB)" if task.get("file_size") else ""
                tc1.markdown(f"**{status_icon} | {task['title']}**")
                tc1.caption(f"创建时间: {task['created_at']}{size_str}")
                
                # 下载按钮区
                if status == "completed" and task.get("file_url"):
                    download_url = f"{PUBLIC_BASE_URL}{task['file_url']}"
                    tc2.markdown(f"[⬇️ 下载音频]({download_url})")
                else:
                    tc2.write("") # 占位
                
                # 删除按钮区
                if tc3.button("🗑️ 删除", key=f"del_{task['task_id']}"):
                    del_res = requests.delete(f"{API_BASE_URL}/tasks/{task['task_id']}")
                    if del_res.status_code == 200:
                        st.success("已删除任务和对应文件")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("删除失败")
                
                st.divider()
                
            # 分页控件
            if total_pages > 1:
                pc1, pc2, pc3 = st.columns([1, 2, 1])
                with pc1:
                    if st.button("上一页") and st.session_state.page > 1:
                        st.session_state.page -= 1
                        st.rerun()
                with pc2:
                    st.write(f"第 {st.session_state.page} / {total_pages} 页 (共 {data.get('total', 0)} 条)")
                with pc3:
                    if st.button("下一页") and st.session_state.page < total_pages:
                        st.session_state.page += 1
                        st.rerun()
        else:
            st.info("暂无任务记录")
    except Exception as e:
        st.error(f"无法获取任务列表: {e}")
