#!/usr/bin/env bash
# see infinity/src/utilities/cli_testing/metric.bats

# inf metric
# inf adapt

# see MetricManipulator.h

module purge
module load FUN3D_INTG_AVX512
module load --auto t-infinity

inf extensions --load adaptation

ref translate om6ste01.meshb om6ste01.lb8.ugrid

cp fun3d_forward.nml fun3d.nml
cp sfe_forward.cfg sfe.cfg
mpiexec_mpt nodet_mpi |& tee om6_forward01.out
# save the forward solution csv
mpiexec_mpt inf csv-to-snap --file om6ste01_volume.csv --only mach -o om6_forward01.snap

cp fun3d_adjoint.nml fun3d.nml
cp sfe_adjoint.cfg sfe.cfg
mpiexec_mpt nodet_mpi |& tee om6_adjoint01.out
# save the adjoint solution csv
mpiexec_mpt inf csv-to-snap --file om6ste01_volume.csv --only mach -o om6_adjoint01.snap

# import the snap file as a T-inf field, take the Hessian and output the
# upper-triagular part of the 3x3 metric tensor
mpiexec_mpt inf metric --mesh om6ste01.lb8.ugrid --snap om6_forward01.snap \
    -o om6_forward01_metric.snap --target-node-count 15000

mpiexec_mpt inf metric --mesh om6ste01.lb8.ugrid --snap om6_adjoint01.snap \
    -o om6_adjoint01_metric.snap --target-node-count 15000

# combine the metric fields
mpiexec_mpt inf metric --mesh om6ste01.lb8.ugrid --metrics om6_forward01_metric.snap \
    om6_adjoint01_metric.snap -o om6_combined01_metric.snap --intersect

# adapt mesh
mpiexec_mpt inf adapt --mesh om6ste01.meshb --metric om6_combined01_metric.snap \
    -o om6ste02.meshb
ref translate om6ste02.meshb om6ste02.lb8.ugrid

# interpolate solution
mpiexec_mpt inf interpolate --source om6ste01.meshb --target om6ste02.meshb \
    --fields rho u v w p turb1 --snap om6ste01_solution.solb -o om6ste02_solution.solb



# ============

cp om6ste01.mapbc om6ste02.mapbc
cp fun3d_forward_warm_restart.nml fun3d.nml
cp sfe_forward.cfg sfe.cfg
mpiexec_mpt nodet_mpi |& tee om6_forward02.out

inf plot --mesh om6ste02.meshb -o om6ste02_mesh.vtk