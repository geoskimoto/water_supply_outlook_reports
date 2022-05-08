@ECHO OFF
call C:\ProgramData\Anaconda3\Scripts\activate.bat
set venv=wsor-env
echo Activating Python Virtual Environment...
call activate %venv%
echo api-env Activated!
call cd %~dp0
python generate_static.py --year 2021 --month 10

python generate_static.py --year 2021 --month 11

python generate_static.py --year 2021 --month 12

python generate_static.py --year 2022 --month 1

python generate_static.py --year 2022 --month 2

python generate_static.py --year 2022 --month 3

python generate_static.py --year 2022 --month 4

python generate_static.py --year 2022 --month 5

