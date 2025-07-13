@echo off
chcp 65001 >nul
echo ===================================
echo 开始打包 EinsteinAI 双方程序
echo ===================================

rem 清理之前的构建
if exist "dist" (
    echo 清理旧的构建文件...
    rmdir /s /q dist
)
if exist "build" (
    rmdir /s /q build  
)
if exist "*.spec" (
    del *.spec
)

echo.
echo 打包蓝方AI...
pyinstaller --onefile --noconsole --name="EinsteinAI_Blue" ai_blue.py

echo.
echo 打包红方AI...
pyinstaller --onefile --noconsole --name="EinsteinAI_Red" ai_red.py

if exist "dist/EinsteinAI_Blue.exe" if exist "dist/EinsteinAI_Red.exe" (
    echo.
    echo ===================================
    echo 打包成功！
    echo ===================================
    
    echo 文件清单:
    dir dist\*.exe
    
    rem 复制测试文件到dist目录
    echo.
    echo 复制测试文件...
    xcopy "test_files\*" "dist\" /Y
    
    echo.
    echo 测试蓝方AI...
    cd dist
    copy JavaOut.txt temp_test.txt >nul
    EinsteinAI_Blue.exe
    if exist "JavaIn.txt" (
        echo 蓝方AI测试成功！
        echo 输出: 
        type JavaIn.txt
    ) else (
        echo 蓝方AI测试失败！
    )
    
    echo.
    echo 测试红方AI...
    copy JavaOut1.txt JavaOut.txt >nul
    EinsteinAI_Red.exe
    if exist "JavaIn1.txt" (
        echo 红方AI测试成功！
        echo 输出:
        type JavaIn1.txt
    ) else (
        echo 红方AI测试失败！
    )
    
    cd ..
    
) else (
    echo.
    echo ===================================
    echo 打包失败！请检查错误信息
    echo ===================================
)

echo.
echo 按任意键结束...
pause >nul