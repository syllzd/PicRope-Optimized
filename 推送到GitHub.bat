@echo off
chcp 65001 >nul
echo ============================================================
echo  图绳优化版 - 推送到 GitHub 仓库
echo ============================================================
echo.
echo  仓库已创建：https://github.com/syllzd/PicRope-Optimized
echo  可见性：Public（必须公开，否则检查更新失效）
echo.
echo  本脚本通过 GitHub API 推送，绕开本机 Git 的 TLS 兼容问题。
echo  需要一个 Fine-grained PAT，授权该仓库 Contents: Read and write。
echo  生成地址：https://github.com/settings/personal-access-tokens
echo.
set /p TOKEN="请粘贴 PAT（输入时不显示，直接回车即可）："
if "%TOKEN%"=="" (
  echo 未输入 Token，已取消。
  pause
  exit /b 1
)

"C:\Users\syllz\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0推送到GitHub.py" "%TOKEN%"

echo.
pause
