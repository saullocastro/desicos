import os
import inspect

TOL = 1e-9

inspect.getfile(inspect.currentframe())
abspath = os.path.abspath(inspect.getfile(inspect.currentframe()))
DESHOME = os.path.dirname(abspath)

if os.name == 'nt':
    TMP_DIR = r'C:\Temp\desicos'
else:
    TMP_DIR = r'~/tmp/desicos'

FLOAT = 'float64'
