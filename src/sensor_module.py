'''SensorModule Class
'''
import numpy as np

import ROOT as rt
from ROOT import TH1D, TH2D, TGraph, TGraphErrors

class SensorModule:
    def __init__(self, fname) -> None:
        '''Module
        loads a root file with the stored RDF and integrations
        contains the methods used to analyze and perform QAQC on a module
        '''

        self.fname = fname
        self.tt = -0.025 # V
        self.ov = 2 # V
        self.n_spe = 100_000
        self.n_src = 200_000

        self.stats = self.load_json()
        if self.stats["ly_rms"] is None: # example
            self.ly_rms = self.ly_function()
            self.store_json()

    def __getitem__(self, key): # example
        return self.stats[key]
    
    # **** #
    def store(self): # example
        pass

    def load(self): # example
        json_fname = self.fname.replace('.root', '.json')
        pass

    # **** #
    def run_analysis(self): # example
        ''''''
        pass

    def rotate(self) -> None:
        '''rotate the channel mappings'''
        pass

    def calibrate(self, factors: dict):
        '''applies the calibration factors to the spe and source data'''
        pass

    def fit_spectra(self, source: str=None, channel: int=None): # spe, src
        '''fits the spectra'''
        pass

    def plot_spectra(self, source: str='spe'):
        pass
    
    def plot_charge_yield(self, source: str='spe'):
        pass

    def plot_light_yield(self) -> (rt.TH1):
        pass

    def plot_crosstalk_spectra(self, channel=0, neighbors=2):
        pass

    def plot_crosstalk_matrix(self):
        pass

    def run_tests(self):
        pass
