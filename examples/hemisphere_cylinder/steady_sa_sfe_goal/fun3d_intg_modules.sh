#!/usr/bin/env bash

module purge

module use /u/shared/fun3d/fun3d_users/modulefiles
module use /u/shared/fun3d/fun3d_users/test_modulefiles
module load intel_2018.3.222
module load mpt-2.23
module load gcc_6.2.0
module load ESP
module load tetgen
module load refine
module load Python_3.7.1
module load t-infinity/latest
module load FUN3D_INTG
module load git_2.10.1
module load clang_10.0.0