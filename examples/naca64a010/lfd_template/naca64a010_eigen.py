#!/usr/bin/env python
"""
Compute the natural frequencies and mode shapes of the Isogai NACA 64A010 problem
"""
import numpy as np
import scipy.linalg as linalg


def eigen_decomp(rho, b):

    # Isogai properties
    unbal = 1.8   # static unbalance
    ra2 = 3.48    # r_a^2 square of radius of gyration
    wh = 100.0    # plunge mode natural frequency
    wa = 100.0    # pitch mode natural frequency
    mu = 60.0     # mass ratio

    # Dimensional mass like terms (see kiviaho matrix pencil note 2019)
    m = mu * rho * np.pi * b**2.0
    Ia = ra2 * m * b**2.0
    Sa = unbal * m * b

    # Mass and Stiffness matrix
    M = np.zeros((2, 2))
    K = np.zeros((2, 2))

    M[0, 0] = m
    M[0, 1] = Sa
    M[1, 0] = Sa
    M[1, 1] = Ia

    K[0, 0] = m * wh**2.0
    K[1, 1] = Ia * wa**2.0

    lam, vec = linalg.eig(K, M)

    # scale the eigenvectors to get unit modal mass
    mass = np.zeros(2)
    stiff = np.zeros(2)
    for i in range(2):
        mass[i] = M.dot(vec[:, i]).dot(vec[:, i])
        vec[:, i] /= np.sqrt(mass[i])
    for i in range(2):
        mass[i] = M.dot(vec[:, i]).dot(vec[:, i])
        stiff[i] = K.dot(vec[:, i]).dot(vec[:, i])

    for i in range(2):
        print(
            'Eigen Decomposition: mode=', i, 'freq=', np.sqrt(lam[i]),
            'shape=', vec[:, i],
            'mass=', mass[i],
            'stiff=', stiff[i],
            'freq2=', np.sqrt(stiff[i]))

    return vec[:, 0], vec[:, 1]
