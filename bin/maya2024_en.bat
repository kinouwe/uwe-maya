@echo off
REM Maya UIを英語化
SET MAYA_UI_LANGUAGE=en_US

REM 環境変数を初期化（必要に応じて明示）
SETLOCAL

REM 既存のPYTHONPATHに追加
SET PYTHONPATH=%PYTHONPATH%;D:\Projects\uwe-maya\third_party\cymel-main\python
SET PYTHONPATH=%PYTHONPATH%;D:\Projects\uwe-maya\python

REM MAYA_SCRIPT_PATHも既存に追記
SET MAYA_SCRIPT_PATH=%MAYA_SCRIPT_PATH%;C:\Program Files\Autodesk\Maya2024\scripts

REM Mayaの起動
START "" "C:\Program Files\Autodesk\Maya2024\bin\maya.exe"

ENDLOCAL
