.\venv\Scripts\activate
#conda activate rasa-env

Set-Location -Path .\DemoMMI\mmiframeworkV2
Start-Process -FilePath .\start.bat

Set-Location -Path ..\FusionEngine
Start-Process -FilePath .\start.bat

Set-Location -Path ..\rasaDemo
Start-Process -FilePath rasa -ArgumentList 'run', '--ssl-certificate', '..\WebAppAssistantV2\cert.pem', '--ssl-keyfile', '..\WebAppAssistantV2\key.pem', '--enable-api', '-m', '.\models\', '--cors', '*'

Set-Location -Path ..\WebAppAssistantV2
Start-Process -FilePath .\start_web_app.bat

Set-Location -Path ..\..\serverAPP
Start-Process -FilePath python -ArgumentList 'server.py'

Set-Location -Path ..\homegym
Start-Process -FilePath flask -ArgumentList 'run', '-h', 'localhost', '--cert', 'cert.pem', '--key', 'key.pem'

Start-Sleep -Seconds 3

Start-Process "msedge.exe" "https://127.0.0.1:8082/index.htm"
Start-Process "msedge.exe" "https://localhost:5000"
