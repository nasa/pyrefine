#!/usr/bin/env bash

set -x # echo commands
set -e # exit on first error
set -u # Treat unset variables as error

project=delta
INIT_COMPLEXITY=8000

serveCSM -batch ${project}.csm > accept-csm-out.txt
ref bootstrap ${project}.egads > accept-bootstrap-out.txt
ref adapt ${project}-vol.meshb -g ${project}.egads -x ${project}01.meshb \
    --implied-complexity \
    ${INIT_COMPLEXITY}
