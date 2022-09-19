import os
import f90nml
from pyrefine.directory_utils import cd

machs = [0.70, 0.75, 0.8, 0.825, 0.83, 0.835, 0.84, 0.85, 0.86, 0.875, 0.885, 0.895, 0.9, 0.91, 0.925, 0.95, 1.0]

for mach in machs:
    dirname = f'mach{mach:0.3f}'
    os.system(f'cp -r lfd_template {dirname}')
    with cd(dirname):
        for nml in ['fun3d.nml', 'fun3d.nml.lfd']:
            inputs = f90nml.read(nml)
            inputs['reference_physical_properties']['mach_number'] = mach
            inputs.write(nml, force=True)
        os.system('time python -u adapt.py > adapt.out 2>&1 &')
