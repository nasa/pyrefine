#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pbs4py import PBS
from pbs4py import FakePBS
from pyrefine.refine.aflr3 import AFLR3
from pyrefine.refine.bootstrap import RefineBootstrap
import subprocess
import sys
import time

# This example uses all ranks to perform refinement and a subset to perform CFD more efficiently.
# This script is called within a single queue scheduling script.
# This script can also be easily changed to run both CFD and refinement on CPUs by setting gpus_per_node to ranks_per_node, ranks_per_gpu to 1, and commenting out the &gpu_support namelist in fun3d.nml
# Example usage with PBS:
# # load AFLR3, UG_IO/UGC, and FUN3D
# mpirun -npernode 1 nvidia-cuda-mps-control -d # starts MPS one time instead of every FUN3D launch, can alternatively use cuda_start_mps
# nodes=$(cat $PBS_NODEFILE | sort | uniq | wc -l)
# ranks=$(cat $PBS_NODEFILE | wc -l)
# ranks_per_node=$(expr $ranks / $nodes)
# gpus_per_node=4
# ranks_per_gpu=4
# python -u adapt.py $ranks_per_node $nodes $gpus_per_node $ranks_per_gpu > output.txt

# Alternatively, it is possible to use split queues as in the onera_m6/steady_sa_gpu example to run refinement on CPU nodes and CFD on GPU nodes

phase_bootstrap = True
phase_c2s       = True
phase_aflr3     = True
phase_hybrid    = True

# Hardware Inputs
pbs                  = FakePBS() # calling script inside a single PBS job
pbs.ncpus_per_node   = int(sys.argv[1]) # ranks per node
pbs.queue_node_limit = int(sys.argv[2]) # number of nodes
gpus_per_node        = int(sys.argv[3]) # gpus per node
ranks_per_gpu        = int(sys.argv[4]) # ranks per gpu
gpu_ranks_per_node   = ranks_per_gpu*gpus_per_node

# General Inputs
project_name = 'cev'
interpolant  = 'file' # default interpolant_label = 'sampling_geom1'

# Bootstrap Phase Inputs
bootstrap_complexity           = 100_000
bootstrap_initial_wall_spacing = 1E-5

# C2S Phase Inputs
initial_complexity   = 200_000
final_complexity     = 3_200_000
steps_per_complexity = 5

# AFLR3 Phase Inputs
# bl_type = 'yplus'   # requires FUN3D v14.2+, defaults: initial wall spacing = 1, bl height = 1000
# bl_type = 're_cell' # requires FUN3D v14.2+, defaults: initial wall spacing = 1, bl height = 5000
bl_type     = 'manual'
# for manual, can alternatively call aflr.compute_spacing_from_reynolds_number(re, bl_initial=None, bl_full=None) below
# which will compute y+=1 from flat plate theory and generate BL from y+=1 to y+=1000 (adjustable with optional args bl_initial and bl_full)
# default growth rate is 1.2 which is also adjustable
first_layer = 2.5e-7 # max re_cell ~ 1
nlayers     = 35     # bl height ~ 3000 wall units based on re_cell

# Hybrid Phase Inputs:
hybrid_complexity = 2_000_000 # fixed complexity
hybrid_steps      = 10

if (phase_bootstrap):
    print("Bootstrap Begin")
    tic = time.perf_counter()
    bootstrap = RefineBootstrap(project_name, bootstrap_complexity, bootstrap_initial_wall_spacing)
    bootstrap.run()
    toc = time.perf_counter()
    elapsed = int(toc-tic)
    print("Bootstrap End. Elapsed Time = ",'{:02}h:{:02}m:{:02}s'.format(elapsed//3600, elapsed%3600//60, elapsed%60))

if (phase_c2s):
    print("C2S Begin")
    tic = time.perf_counter()
    adapt_driver = AdaptationDriver('%s' % (project_name), pbs)
    adapt_driver.refine.vertices_per_cpu_core = 500 # use all ranks always
    adapt_driver.controller.initial_complexity = initial_complexity
    adapt_driver.controller.final_complexity = final_complexity
    adapt_driver.simulation.extra_input_files = ["tdata"]
    adapt_driver.simulation.ranks_per_node = gpu_ranks_per_node
    adapt_driver.controller.steps_per_complexity = steps_per_complexity
    iterations = adapt_driver.controller.compute_iterations()
    adapt_driver.refine.lp_norm = 4
    adapt_driver.refine.gradation = 10
    adapt_driver.refine.number_of_sweeps = 10
    adapt_driver.refine.interpolant = interpolant
    adapt_driver.simulation.fun3d_nml = 'fun3d.nml.1'
    adapt_driver.set_iterations(1, 3)
    adapt_driver.run()
    adapt_driver.simulation.fun3d_nml = 'fun3d.nml.2'
    adapt_driver.set_iterations(4, iterations)
    adapt_driver.run()
    toc = time.perf_counter()
    elapsed = int(toc-tic)
    print("C2S End. Elapsed Time = ",'{:02}h:{:02}m:{:02}s'.format(elapsed//3600, elapsed%3600//60, elapsed%60))

if (phase_aflr3):
    print("AFLR3 Begin")
    tic = time.perf_counter()
    aflr = AFLR3(project_name, bl_type)
    aflr.nbl = nlayers
    aflr.initial_wall_spacing = first_layer
    aflr.run()
    toc = time.perf_counter()
    elapsed = int(toc-tic)
    print("AFLR3 End, Elapsed Time = ",'{:02}h:{:02}m:{:02}s'.format(elapsed//3600, elapsed%3600//60, elapsed%60))

if (phase_hybrid):
    print("Hybrid Begin")
    tic = time.perf_counter()
    adapt_hybrid_driver = AdaptationDriver('%s' % (project_name), pbs)
    adapt_hybrid_driver.refine.vertices_per_cpu_core = 500 # use all ranks always
    adapt_hybrid_driver.controller.initial_complexity = hybrid_complexity
    adapt_hybrid_driver.simulation.extra_input_files = ["tdata"]
    adapt_hybrid_driver.simulation.ranks_per_node = gpu_ranks_per_node
    adapt_hybrid_driver.controller.steps_per_complexity = hybrid_steps
    adapt_hybrid_driver.refine.lp_norm = 2
    adapt_hybrid_driver.refine.number_of_sweeps = 10
    adapt_hybrid_driver.refine.interpolant = interpolant
    adapt_hybrid_driver.simulation.fun3d_nml = 'fun3d.nml.1'
    adapt_hybrid_driver.set_iterations(1, 3)
    adapt_hybrid_driver.run() 
    adapt_hybrid_driver.simulation.fun3d_nml = 'fun3d.nml.2'
    adapt_hybrid_driver.set_iterations(4, hybrid_steps)
    adapt_hybrid_driver.run(skip_final_refine_call=True) 
    toc = time.perf_counter()
    elapsed = int(toc-tic)
    print("Hybrid End. Elapsed Time = ",'{:02}h:{:02}m:{:02}s'.format(elapsed//3600, elapsed%3600//60, elapsed%60))
