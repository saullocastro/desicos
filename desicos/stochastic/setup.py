from distutils.core import setup
import py2exe

from distutils.filelist import findall
import os

##### include mydir in distribution #######
def extra_datas(mydir):
    def rec_glob(p, files):
        import os
        import glob
        for d in glob.glob(p):
            if os.path.isfile(d):
                files.append(d)
            rec_glob("%s/*" % d, files)
    files = []
    rec_glob("%s/*" % mydir, files)
    extra_datas = []
    for f in files:
        extra_datas.append(f)

    return extra_datas
###########################################

addFiles = []
#for f in matplotlibdata:
#    dirname = os.path.join('matplotlibdata', f[len(matplotlibdatadir)+1:])
#    addFiles.append((os.path.split(dirname)[0], [f]))

addFiles.append('msvcp90.dll')
addFiles.append('msvcm90.dll')
addFiles.append('msvcr90.dll')
#addFiles+=extra_datas('gui')
setup(
    windows=['desicosST03.py'],
	name='DESICOS stochastic v0.3',
    options={
             'py2exe': {
                        'packages' : [],
			"includes" : ['scipy.sparse.csgraph._validation','numpy','scipy','atexit','PySide.QtNetwork','stochastic','st_utils','multiprocessing','threading', 'pytz','json'],
            "optimize": 2,
			},
			
            },
    data_files=addFiles
)

