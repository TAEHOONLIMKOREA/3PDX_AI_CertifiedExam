@echo off
echo ==========================================
echo Vision AD GUI - EXE 빌드 스크립트
echo ==========================================
echo.

REM 1. 가상환경 생성
echo [1/4] 가상환경 생성 중...
python -m venv venv
if %errorlevel% neq 0 (
    echo 오류: 가상환경 생성 실패
    pause
    exit /b 1
)
echo 가상환경 생성 완료!
echo.

REM 2. 가상환경 활성화 및 의존성 설치
echo [2/4] 의존성 설치 중...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 오류: 의존성 설치 실패
    pause
    exit /b 1
)
echo 의존성 설치 완료!
echo.

REM 3. PyInstaller 설치
echo [3/4] PyInstaller 설치 중...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo 오류: PyInstaller 설치 실패
    pause
    exit /b 1
)
echo PyInstaller 설치 완료!
echo.

REM 4. EXE 파일 빌드
echo [4/4] EXE 파일 빌드 중...
pyinstaller --onefile --windowed --name="VisionAD_Test" --icon=NONE app.py
if %errorlevel% neq 0 (
    echo 오류: EXE 빌드 실패
    pause
    exit /b 1
)
echo.
echo ==========================================
echo 빌드 완료!
echo 실행 파일 위치: dist\VisionAD_Test.exe
echo ==========================================
pause
