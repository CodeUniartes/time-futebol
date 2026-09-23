@echo off
setlocal
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --onefile --windowed --name "Montador de Pedido Futebol" --icon "assets\icon.ico" --add-data "assets;assets" app.py
echo.
echo Executavel gerado em: dist\Montador de Pedido Futebol.exe
pause
