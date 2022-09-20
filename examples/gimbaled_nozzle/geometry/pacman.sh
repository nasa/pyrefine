#! /bin/bash

set -o errexit
set -o pipefail
set -o nounset
set -o xtrace

PROJECT=${0%.sh}

set -o errexit

serveCSM -batch ${PROJECT}.csm \
	 > ${PROJECT}-csm-out.txt

../../../utils/egads2mapbc.sh ${PROJECT}.egads \
			    > ${PROJECT}01.mapbc

ref boostrap ${PROJECT}.egads \
	> ${PROJECT}-bootstrap-out.txt

ref adapt ${PROJECT}-vol.meshb -g ${PROJECT}.egads \
    --spalding 0.005 1000 \
    --fun3d-mapbc ${PROJECT}01.mapbc \
	-x ${PROJECT}01.meshb \
	> ${PROJECT}-curve-out.txt

#     --uniform cyl ceil 0.05 -0.5 0 0 0 4 0 0 0.6 1.2 \
