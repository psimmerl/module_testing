"""waveforms

functions for acquiring and processing waveforms.


Scan over-voltages and trigger thresholds for a module.
1. Use wavedump (or acquire-waveforms?) to collect over-voltage and trigger threshold data for a chosen source type
    -   Save each waveform's integrated charge, if it's saturated, t_{10%}, t_{90%}, and anything else?
2. Analysis of integrated wave

"""
import os
import sys
import argparse

import numpy as np

# import scipy as sp

import ROOT as rt


def acquire_waveforms(waveform_path, n_events, l: str = "sodium", ov: float = 2.2, thresholds: float = -0.05, **kwargs):
    """wavedump -t self -l sodium --channel-map 1 -n"""
    """acquire_waveforms
    Acquire waveforms from the QAQC jig and saves to an hdf5 file.
    """

    return


def process_waveforms(waveform_path: str, root_path: str, **kwargs):
    """process_waveforms
    Process a waveform file (hdf5) from the QAQC jig and save the reduced file as a ROOT nTuple. Can later be loaded into an RDataframe for more advanced analyses. Returns the nTuple

    params:
    waveform_path   str
        path of the hdf5 file where the waveforms are saved
    root_path    str
        path of the root file where the processed waveforms' data is saved
    branches    str, iterable
        choose what data is saved to your proc

    return [ ( trigger channel, trigger time, { channel ID, charge, t 10%, t 90%, saturation ; for the 8 channels in the trigger group } ) ; for N_EVENTS in each of the 4 trigger groups ]
    """

    return


if __name__ == "__main__":
    overvoltages = []

    pass
