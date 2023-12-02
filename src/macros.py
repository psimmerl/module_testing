import numpy as np
from array import array
from math import floor, ceil


def root_init():  # does this work?
    import ROOT as rt
    from ROOT import gROOT, gStyle
    from ROOT import TFile, TTree, TNtuple, RDataframe
    from ROOT import TCanvas, TPad, TAxis, TLegend, TLatex, TLine, TBox
    from ROOT import TH1D, TH2D, TGraph, TGraphErrors
    from ROOT import TMath, TF1, TF2


def abcd_predict(sig_XY, bkg_XY, X_bound, Y_bound, blinded=True, **kwargs):
    bounds = np.array([X_bound, Y_bound])
    sig_XY, bkg_XY = bounds < sig_XY, bounds < bkg_XY
    sig_abcd = np.array(
        [
            (sig_XY[:, 0] & sig_XY[:, 1]).sum(),
            (sig_XY[:, 0] & ~sig_XY[:, 1]).sum(),
            (~sig_XY[:, 0] & ~sig_XY[:, 1]).sum(),
            (~sig_XY[:, 0] & sig_XY[:, 1]).sum(),
        ]
    )
    bkg_abcd = np.array(
        [
            (bkg_XY[:, 0] & bkg_XY[:, 1]).sum(),
            (bkg_XY[:, 0] & ~bkg_XY[:, 1]).sum(),
            (~bkg_XY[:, 0] & ~bkg_XY[:, 1]).sum(),
            (~bkg_XY[:, 0] & bkg_XY[:, 1]).sum(),
        ]
    )
    S2SqrtB_score = np.divide(sig_abcd, np.sqrt(bkg_abcd), where=bkg_abcd != 0, out=np.zeros_like(sig_abcd))
    return sig_abcd, bkg_abcd, S2SqrtB_score


def abcd_confidence(sig_, abcd_bkg, **kwargs):
    for k, v in kwargs.item():
        sig_br_ratio = v if "sig_br_ratio" in v else 1.0
        levels = v if "levels" in v else [0.25, 0.16, 0.50, 0.840, 0.975]

    # simulataneous fit the two histos and get TConfidence
