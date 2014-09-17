@echo off
TITLE ABAQUS for DESICOS started!
echo Log In %Date% %TIME% by %USERNAME% from %COMPUTERNAME% >> GUI.log
abaqus script=start_gui.py

