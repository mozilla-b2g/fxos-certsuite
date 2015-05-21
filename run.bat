@echo off
set find=c:\windows\system32\find.exe
set rndfile=%temp%\%random%.txt
set venv_dir=certsuite_venv
set has_choco=
set has_python=
set has_pip=
set has_virtualenv=
set has_adb=
set has_powershell=

rem main

call:check_powershell has_powershell
if not "%has_powershell%" == "1" echo Please install powershell manually and run again. & goto:eof

call:check_choco has_choco
if not "%has_choco%" == "1" call:install_choco has_choco
if not "%has_choco%" == "1" echo Install chocolatey failed. Find solutions on http://chocolatey.org and run again & goto:eof

call:check_pip has_pip
if not "%has_pip%" == "1" call:install_pip has_pip
if not "%has_pip%" == "1" echo Install easy_install failed. Find solutions on https://chocolatey.org/packages/easy.install and run again & goto:eof

call:check_virtualenv has_virtualenv
if not "%has_virtualenv%" == "1" call:install_virtualenv has_virtualenv
if not "%has_virtualenv%" == "1" echo Install virtualenv failed. Find solutions on https://virtualenv.pypa.io/en/latest/ and run again & goto:eof

call:check_adb has_adb
if not "%has_adb%" == "1" call:install_adb has_adb
if not "%has_adb%" == "1" echo Install adb failed. Find solutions on https://developer.android.com/tools/help/adb.html and run again & goto:eof

if not exist %venv_dir%\nul virtualenv --no-site-packages %venv_dir%
if not exist %venv_dir%\nul echo error creating virtualenv %venv_dir%, resovle this issue and run again & goto:eof

call %venv_dir%\Scripts\activate.bat
python setup.py install
echo "Done, running the suite"
runcertsuite %*
deactivate

set find=
set rndfile=
set has_choco=
set has_python=
set has_pip=
set has_virtualenv=
set has_adb=
set has_powershell=
set venv_dir=

rem end of main
goto:eof

rem temparory code
if "%has_powershell%" == "1" echo has powershell
if "%has_choco%" == "1" echo has choco
if "%has_python%" == "1" echo has python
if "%has_pip%" == "1" echo has pip
if "%has_adb%" == "1" echo has adb
if "%has_virtualenv%" == "1" echo has virtualenv
if not "%has_choco%" == "1" call:install_choco has_choco
if "%has_choco%" == "1" echo has choco
goto:eof

rem local function defines

:install_choco - passing a variable by reference
echo installing chocolatey
rem @powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1'))" && SET PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin
call:check_choco %~1
goto:eof

:install_python - passing a variable by reference
echo installing python
cinst python2
call:check_python %~1
goto:eof

:install_pip - passing a variable by reference
echo installing pip
cinst easy.install
call:check_pip %~1
goto:eof

:install_virtualenv - passing a variable by reference
echo installing virtualenv
pip install virtualenv
call:check_virtualenv %~1
goto:eof

:check_choco - passing a variable by reference
set "%~1=0"
choco > %rndfile% 2>&1
for /F %%i in ('type %rndfile% ^| %find% "Chocolatey"') do set "%~1=1"
goto:eof

:check_python - passing a variable by reference
set "%~1=0"
python --version > %rndfile% 2>&1
for /F %%i in ('type %rndfile% ^| %find% "Python"') do set "%~1=1"
goto:eof

:check_pip - passing a variable by reference
set "%~1=0"
pip list > %rndfile% 2>&1
for /F %%i in ('type %rndfile%  ^| %find% "pip"') do set "%~1=1"
goto:eof

:check_virtualenv - passing a variable by reference
set "%~1=0"
virtualenv > %rndfile% 2>&1
for /F %%i in ('type %rndfile%  ^| %find% "You must provide a DEST_DIR"') do set "%~1=1"
goto:eof

:check_adb - passing a variable by reference
set "%~1=0"
adb devices > %rndfile% 2>&1
for /F %%i in ('type %rndfile% ^| %find% "attached"') do set "%~1=1"
goto:eof

:check_powershell - passing a variable by reference
set "%~1=0"
powershell -h > %rndfile% 2>&1
for /F %%i in ('type %rndfile% ^| %find% "Windows PowerShell"') do set "%~1=1" & goto:eof
goto:eof