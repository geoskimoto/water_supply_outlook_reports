@ECHO OFF
call C:\ProgramData\Anaconda3\Scripts\activate.bat
set venv=wsor-env
echo Activating Python Virtual Environment...
call activate %venv%
echo api-env Activated!
call cd %~dp0
cmd /k