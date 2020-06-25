#!/bin/bash
#!/usr/bin/python3
#PBS -V
#PBS -q corei7
#PBS -l nodes=1:ppn=1
#PBS -l pmem=3500mb

#### cd working directory (where you submitted your job)
cd ${PBS_O_WORKDIR}

#### load module
module load matlab/R2019a

#### Executable Line
matlab -nodisplay -nodesktop -nojvm -nosplash -r 'run cyl_1d_interior_point_algo.m; exit'