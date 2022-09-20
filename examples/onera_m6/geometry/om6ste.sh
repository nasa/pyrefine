#!/usr/bin/env bash

set -e
set -u
set -x

serveCSM -batch om6ste.csm | tee om6ste-csm.txt

ref bootstrap om6ste.egads | tee om6ste-boot.txt

ref_driver -i om6ste-vol.meshb \
	   -g om6ste.egads \
	   -x om6ste01.meshb \
    | tee om6ste-crv.txt
