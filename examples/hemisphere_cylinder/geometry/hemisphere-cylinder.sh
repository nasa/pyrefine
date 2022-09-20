#!/usr/bin/env bash

set -x # echo commands
set -e # exit on first error
set -u # Treat unset variables as error

project=hemisphere-cylinder

INIT_COMPLEXITY=2000

serveCSM -batch ${project}.csm | tee csm-out.txt
ref bootstrap ${project}.egads | tee bootstrap-out.txt
ref adapt ${project}-vol.meshb \
    -g ${project}.egads \
    -x ${project}01.meshb \
    --implied-complexity \
    ${INIT_COMPLEXITY} | tee initial-mesh-out.txt

