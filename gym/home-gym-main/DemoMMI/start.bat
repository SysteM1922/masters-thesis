@echo off


rem Run start.bat in folder "FusionEngine"
cd "FusionEngine"
start "" "start.bat"
cd ..


rem Run start.bat in folder "mmiframeworkV2"
cd "mmiframeworkV2"
start "" "start.bat"
cd ..


rem Run start_web_app.bat in folder "WebAppAssistantV2"
cd "WebAppAssistantV2"
start "" "start_web_app.bat"
cd ..


rem anaconda prompt 
start "" %windir%\System32\cmd.exe /K "C:\ProgramData\anaconda3\Scripts\activate.bat && cd rasaDemo && conda activate rasa-env && rasa run --ssl-certificate ..\WebAppAssistantV2\cert.pem --ssl-keyfile ..\WebAppAssistantV2\key.pem --enable-api -m .\models\ --cors "*""