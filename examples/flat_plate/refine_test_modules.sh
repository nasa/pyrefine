#!/usr/bin/env bash
module purge

module use /u/shared/fun3d/fun3d_users/modulefiles
module use /u/shared/fun3d/fun3d_users/test_modulefiles
module use /u/shared/slwood2/fun3d_users/test_modulefiles/
module load intel_2018.3.222
module load mpt-2.19
module load ParMETIS/4.0.3-mpt-2.19-intel_2018.3.222
module load gcc_6.2.0
module load ESP/119-beta.2020.09.29.1106
module load tetgen
module load refine
module load t-infinity/latest
module load Python_3.7.1
module load FUN3D_SFE_EXP_AVX512

