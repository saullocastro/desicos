import os
from multiprocessing import cpu_count
import __main__

def write_job(self, submit=False, wait=True, multiple_cores=False):
    os.chdir(self.output_dir)
    self.job = __main__.mdb.jobs[ self.jobname ]
    self.job.writeInput()
    inppath = self.jobname + '.inp'
    if submit:
        # the function below was commented because
        # the GUI writes another input file
        # overwriting the customized one
        #self.job.submit(consistencyChecking = OFF)
        if multiple_cores:
            cpus = cpu_count() - 1
            os.system('abaqus job={0} input={1} cpus={2}'.format(self.jobname,
                      inppath, cpus))
        else:
            os.system('abaqus job={0} input={1}'.format(self.jobname,
                      inppath))
        self.check_completed(wait=wait)
        self.read_walltime()
    os.chdir(self.tmp_dir)
    return True
