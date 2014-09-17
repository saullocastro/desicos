import os
import sys

desicos_folder = os.path.realpath('../..')
os.environ['PYTHONPATH'] += ';' + desicos_folder
sys.path.append(desicos_folder)
from desicos.abaqus.constants import DAHOME
os.environ['PYTHONPATH'] += ';' + os.path.join(DAHOME)
os.environ['PYTHONPATH'] += ';' + os.path.join(DAHOME, 'gui')
os.chdir(os.path.join(DAHOME,'gui'))
os.system('abaqus cae -custom prototypeApp -noStartup')
