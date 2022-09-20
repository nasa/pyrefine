
rm -f mda30p30n.egads
serveCSM -batch mda30p30n.csm

../../utils/egads2mapbc.sh mda30p30n.egads > mda30p30n01.mapbc

rm -f mda30p30n-vol.meshb
ref bootstrap mda30p30n.egads
mv mda30p30n-vol.meshb mda30p30n01.meshb

