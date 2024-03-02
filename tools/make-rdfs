#!/bin/bash

for a in "$@"
do
    echo "$a"
    b=`basename "$a" .hdf5`
    python3 waveforms_2.py "$a" -o "${b}_RDF.root" --saturation_flag True -c True
done
