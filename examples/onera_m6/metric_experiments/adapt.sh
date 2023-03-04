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

for i in {01..10}
do

if [[ "${i}" -eq 1 ]]; then
    cp fun3d_forward.nml fun3d.nml
else
    cp fun3d_forward_warm_restart.nml fun3d.nml
    sed -i -e 's?import_from =.*?import_from = '"om6ste${i}_solution.solb"'?g' fun3d.nml
    ln -sf om6ste01.mapbc om6ste${i}.mapbc
fi

sed -i -e 's?project_rootname =.*?project_rootname = '"om6ste${i}"'?g' fun3d.nml
cp fun3d.nml fun3d_forward${i}.nml
cp sfe_forward.cfg sfe.cfg
cp sfe_forward.cfg sfe_forward${i}.cfg

mpiexec_mpt nodet_mpi |& tee om6_forward${i}.out
# extract the forward solution from csv and save as snap
mpiexec_mpt inf csv-to-snap --file om6ste${i}_volume.csv --only mach -o om6_forward${i}.snap

cp fun3d_adjoint.nml fun3d.nml
sed -i -e 's?project_rootname =.*?project_rootname = '"om6ste${i}"'?g' fun3d.nml
cp fun3d.nml fun3d_adjoint${i}.nml
cp sfe_adjoint.cfg sfe.cfg
cp sfe_adjoint.cfg sfe_adjoint${i}.cfg

mpiexec_mpt nodet_mpi |& tee om6_adjoint${i}.out
# extract the adjoint solution from csv and save as snap
mpiexec_mpt inf csv-to-snap --file om6ste${i}_volume.csv --only mach -o om6_adjoint${i}.snap

# import the snap file as a T-inf field, take the Hessian and output the
# upper-triagular part of the 3x3 metric tensor
mpiexec_mpt inf metric --mesh om6ste${i}.lb8.ugrid --snap om6_forward${i}.snap \
    -o om6_forward${i}_metric.snap --target-node-count 15000

mpiexec_mpt inf metric --mesh om6ste${i}.lb8.ugrid --snap om6_adjoint${i}.snap \
    -o om6_adjoint${i}_metric.snap --target-node-count 15000

# combine the metric fields
mpiexec_mpt inf metric --mesh om6ste${i}.lb8.ugrid --metrics om6_forward${i}_metric.snap \
    om6_adjoint${i}_metric.snap -o om6_combined${i}_metric.snap --intersect

# adapt mesh
j=$((i+1))
next=$(printf "%02d" ${j})
mpiexec_mpt inf adapt --mesh om6ste${i}.meshb --metric om6_combined${i}_metric.snap \
    -o om6ste${next}.meshb
ref translate om6ste${next}.meshb om6ste${next}.lb8.ugrid

# interpolate solution
mpiexec_mpt inf interpolate --source om6ste${i}.meshb --target om6ste${next}.meshb \
    --fields rho u v w p turb1 --snap om6ste${i}_solution.solb -o om6ste${next}_solution.solb

FILE=om6ste${next}_solution.solb
if [ ! -f "$FILE" ]; then
    echo "$FILE does not exist."
    break
fi

done

# ============

# cp om6ste01.mapbc om6ste02.mapbc
# cp fun3d_forward_warm_restart.nml fun3d.nml
# cp sfe_forward.cfg sfe.cfg
# mpiexec_mpt nodet_mpi |& tee om6_forward02.out

# inf plot --mesh om6ste02.meshb -o om6ste02_mesh.vtk