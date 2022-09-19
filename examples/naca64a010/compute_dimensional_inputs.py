#!/usr/bin/python
"""
Isogai NACA 64A010 airfoil
Compute the moving body inputs from a speed index

Note: the temperature in fun3d.nml is only for sutherland's law it does not set the speed of sound here
"""
import numpy as np

#mach = 0.75
#vf = [1.0, 1.1, 1.20, 1.25, 1.5]

#mach = 0.80
#vf = [0.8, 0.9]

mach = 0.70
vf = [0.5, 1.5, 2.5]

rho = 1.225


# gas properties
T     = 298.15 # sea level temperature
gamma = 1.4    # ratio of specific heats
R     = 287.05 # gas constant

# Isogai airfoil properties
b  = 0.5      # semichord [m]
mu = 60.0
wa = 100.0

for i in range(len(vf)):
    #a = np.sqrt(gamma * R * T)
    uinf = vf[i] * b * wa * np.sqrt(mu)

    qinf = 0.5 * rho *  uinf ** 2.0
    print('vf', vf[i])
    print('uinf', uinf)
    print('qinf', qinf)
