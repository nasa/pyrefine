#! /bin/bash

PROJECT=${0%.sh}

serveCSM -batch ${PROJECT}.csm

ref bootstrap ${PROJECT}.egads

ln -sf ${PROJECT}-vol.meshb ${PROJECT}01.meshb


