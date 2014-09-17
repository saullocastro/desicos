@echo off
if not defined PYTHONPATH (
	SET PYTHONPATH=%CD%
	SET PYTHONPATH=%PYTHONPATH%;%CD%\gui
) else (
	SET PYTHONPATH=%PYTHONPATH%;%CD%
	SET PYTHONPATH=%PYTHONPATH%;%CD%\gui
)
cd gui
TITLE ABAQUS for DESICOS being started...
abaqus cae -custom prototypeApp -noStartup
::python start_gui.py

