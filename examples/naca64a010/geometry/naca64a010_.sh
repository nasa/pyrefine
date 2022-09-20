PROJECT=${0%.sh}

serveCSM -batch ${PROJECT}.csm 

../../../utils/egads2mapbc.sh ${PROJECT}.egads > ${PROJECT}01.mapbc

ref bootstrap ${PROJECT}.egads 

ln -sf ${PROJECT}-vol.meshb ${PROJECT}01.meshb

