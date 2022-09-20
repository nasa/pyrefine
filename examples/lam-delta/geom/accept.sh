#!/usr/bin/env bash

set -x # echo commands
set -e # exit on first error
set -u # Treat unset variables as error

project=delta

serveCSM -batch ${project}.csm > accept-csm-out.txt
ref bootstrap ${project}.egads > accept-bootstrap-out.txt
../../acceptance/check.rb

