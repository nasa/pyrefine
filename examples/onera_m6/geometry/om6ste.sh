#!/usr/bin/env bash

set -e
set -u
set -x

PROJECT=om6ste
INIT_COMPLEXITY=5000
YPLUS_ONE=1e-3

rm -f ${PROJECT}.egads
serveCSM -batch ${PROJECT}.csm | tee ${PROJECT}-csm.txt

rm -f ${PROJECT}-vol.meshb
ref bootstrap ${PROJECT}.egads | tee ${PROJECT}-boot.txt

rm -f ${PRJOECT}01.meshb
mpiexec_mpt refmpi adapt ${PROJECT}-vol.meshb \
                         -g ${PROJECT}.egads \
                         --spalding ${YPLUS_ONE} ${INIT_COMPLEXITY} \
                         --viscous-tags 5,6 \
                         -x ${PROJECT}01.meshb \
                         -x ${PROJECT}01.lb8.ugrid \
                       | tee ${PROJECT}01-bla-dpt.txt
