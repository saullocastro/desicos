import sys
import os
import time
def check_stop(rf3s):
    criterion1 = 0.01 # % to consider a local  buckling drop
    criterion2 = 0.30 # % to consider a global buckling drop
    if len(rf3s) < 2:
        return False
    rf3s = [abs(rf3) for rf3 in rf3s]
    rf3_max = max(rf3s)
    rf3s = [rf3/rf3_max for rf3 in rf3s] # normalizing 0. to 1.
    drops = 0
    grow = True
    peak = rf3s[0]
    nadir = rf3s[0]
    for i,rf3 in enumerate(rf3s[1:]):
        if grow and rf3s[i] < (1-criterion1)*peak:
            grow  = False
            nadir = peak
            drops += 1
        if not grow and rf3s[i] < (1-criterion2)*peak:
            return True # global buckling
        if grow and rf3s[i] > peak:
            peak = rf3s[i]
        if not grow and rf3s[i] < nadir:
            nadir = rf3s[i]
        if not grow and rf3s[i] > (1+criterion1)*nadir:
            peak = nadir
            grow = True
    if drops > 1:
        return True
    else:
        return False

def read_rf3( output_dir, jobname ):
    dat_path = os.path.join( output_dir, jobname + '.dat')
    if not os.path.isfile( dat_path ):
        return []
    dat_file = open( dat_path, 'r' )
    lines = iter(dat_file.readlines())
    rf3s = []
    while True:
        try:
            line = lines.next()
        except StopIteration:
            break
        if line.find('NODE FOOT-') > -1:
            lines.next()
            lines.next()
            line = lines.next()
            rf3s.append( float(line.split()[2]) )
    return rf3s

def stopper( output_dir, jobname ):
    if jobname[-3:] == '_lb':
        return False
    rf3s = read_rf3( output_dir, jobname )
    if check_stop(rf3s):
        os.system('abaqus terminate job=%s' % jobname)
        time.sleep(30)
        dat_path = os.path.join( output_dir, jobname + '.dat')
        if os.name == 'nt':
            os.system('del %s' % dat_path)
        else:
            os.system('rm %s' % dat_path)

if __name__ == '__main__':
    output_dir, jobname = sys.argv[1:]
    stopper( output_dir, jobname )


