Write-Host "正在安装 Agent S 依赖..." -ForegroundColor Cyan

# 检查 Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "未检测到 Python，请先安装 Python 3.10-3.12：https://www.python.org/downloads/" -ForegroundColor Red
    pause
    exit
}

$ver = python -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)"
if ($ver -lt 39) {
    Write-Host "Python 版本过低，请安装 3.9 或以上版本" -ForegroundColor Red
    pause
    exit
}

Write-Host "Python 版本正常，开始安装依赖..." -ForegroundColor Green
pip install gui-agents pytesseract -i https://pypi.tuna.tsinghua.edu.cn/simple

Write-Host ""
Write-Host "✅ 安装完成！运行 launcher.bat 启动程序。" -ForegroundColor Green
pause
