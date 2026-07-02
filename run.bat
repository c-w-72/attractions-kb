@echo off
chcp 65001 >nul
echo 🏯 中国旅游景点知识库 - 启动中...
echo.
echo 安装依赖...
pip install -r requirements.txt
echo.
echo 启动应用...
streamlit run app.py --server.port 8501
pause
