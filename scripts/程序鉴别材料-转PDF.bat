@echo off
chcp 65001 >nul
setlocal

rem 本脚本位于 skill 目录，固定生成 60 页程序鉴别材料
rem 用法: 程序鉴别材料-转PDF.bat <项目根目录> [软件全称]
rem 示例: 程序鉴别材料-转PDF.bat D:\AIProjects\Uni\ILovePoems 艾宾浩斯背诗笔记系统

set "SKILL_DIR=%~dp0"
set "PROJECT_ROOT=%~1"
set "PROJECT_NAME=%~2"

if "%PROJECT_ROOT%"=="" (
  echo [ERROR] 缺少项目根目录参数。
  echo 用法: "%~nx0" ^<项目根目录^> [软件全称]
  echo 示例: "%~nx0" D:\AIProjects\Uni\ILovePoems 艾宾浩斯背诗笔记系统
  exit /b 1
)
if "%PROJECT_NAME%"=="" set "PROJECT_NAME=PROJECT_NAME"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] 未检测到 python，请先安装 Python 3 并加入 PATH。
  exit /b 1
)

echo [1/1] 生成 60 页程序鉴别材料（md / html / pdf）...
python "%SKILL_DIR%generate_program_pdf.py" --project-root "%PROJECT_ROOT%" --project-name "%PROJECT_NAME%"
if errorlevel 1 (
  echo [ERROR] 生成失败。若提示缺少 reportlab，请执行: pip install reportlab
  exit /b 1
)

echo [OK] 输出目录: "%PROJECT_ROOT%\software-copyright\"
exit /b 0
