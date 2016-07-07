import ROOT, rootlogon
import argparse
import copy
import glob
import helpers
import os
import sys
import time
import config as CONF
from array import array
import numpy as np
import sys
from plot_2dhists import DrawHists 

outputdir = CONF.outplotpath
basedir = "F_c10-cb-b77/"
signals = []
data = []

# mass_lst = [700, 800, 900, 1000, 1100, 1200, 1400, 1500, 1600, 1800, 2000, 2250, 2500, 2750, 3000]
#mass_lst = [1000, 1100, 1200, 1400, 1500, 1600, 1800, 2000]
mass_lst = [1000, 1100, 1200, 1400, 1500, 2000]

for mass in mass_lst:
    signals.append( basedir + ("signal_G_hh_c10_M%d/hist-MiniNTuple.root" % mass))

data.append( basedir + "data_test15/hist-MiniNTuple.root")
data.append( basedir + "data_test16/hist-MiniNTuple.root")

scuts = ["AllTag_Signal/h0_tj_pt_dR", "AllTag_Signal/h1_tj_pt_dR"]
dcuts = ["Alltag/h0_tj_pt_dR", "Alltag/h1_tj_pt_dR"]

deltas = np.linspace(0, .5, 21)
masses = np.linspace(225, 325, 21)

def main():

    ops = options()
    # create output file
    output = ROOT.TFile.Open(CONF.outplotpath + "sig_truth.root", "recreate")

    print output

    # # Draw the efficiency plot relative to the all normalization
    # name of the canvas
    cname = "roc_plot_scaled_lead.pdf"
    DrawRoc(output, [scuts[0]], [dcuts[0]], cname)
    output.Close()

def passcut(pt, dR, m, d):
    if pt > 1000.0:
	return True
    cval = m/pt
    return abs(cval - dR) < d

def cut_eff(m, d, *hists):
    retvals = []
    for h in hists:
	retvals.append(0)
        # only iterate over values for dR < 2.5
	ny = h.GetYaxis().FindBin(2.5)
        nx = h.GetNbinsX()

	for ix in range(nx):
	    for iy in range(ny):
		xval = h.GetXaxis().GetBinCenter(ix)
		yval = h.GetYaxis().GetBinCenter(iy)
		if passcut(xval, yval, m, d):
		    retvals[-1] += h.GetBinContent(ix, iy)	    

    return retvals

def DrawRoc(outputroot, scuts, dcuts, canv_name):
    signalmc = ROOT.TH2F(scuts[0], "dR between lead, subleading track jet", 350, 0, 3500, 130, 0, 6.5)
    datamc = ROOT.TH2F(dcuts[0], "dR between lead, subleading track jet", 350, 0, 3500, 130, 0, 6.5)

    sig_mc_list = []
    # iterate over signal files
    for f in signals:
	input_mc = ROOT.TFile.Open(CONF.inputpath + f)
	sig_cut_list = []
        if not input_mc: 
            print CONF.inputpath + f
	for scut in scuts:
            try: 
                sig_cut_list.append( input_mc.Get(scut).Clone() ) 
            except: 
                print CONF.inputpath + f
                print scut 
                raise 

	scalefactor = sum([x.Integral() for x in sig_cut_list])
	# scale all mass points equally
	for i in range(len(sig_cut_list)):
	    sig_cut_list[i].Scale(1/scalefactor)
            signalmc.Add( sig_cut_list[i] ) 

	sig_mc_list += sig_cut_list

	input_mc.Close()


    # iterate over all the data
    data_mc_list = []
    for f in data:
	input_mc = ROOT.TFile.Open(CONF.inputpath + f)
	data_cut_list = []
        if not input_mc: 
            print CONF.inputpath + f
	for dcut in dcuts:
            try: 
                data_cut_list.append( input_mc.Get(scut).Clone() ) 
            except: 
                print CONF.inputpath + f
                print dcut 
                raise 
	
	# don't scale for data
	for i in range(len(data_cut_list)):
	    datamc.Add( data_cut_list[-1] )

	data_mc_list += data_cut_list

	input_mc.Close()

    # rebin for speed
    signalmc.Rebin2D(2,2)
    datamc.Rebin2D(2,2)
 
    sigsize = signalmc.Integral()
    datasize = datamc.Integral()

    coords = []
    testvals = []

    for m in masses: 
        for d in deltas:
	    # status feedback to user
	    print (m,d)
	    sys.stdout.write("\033[F")

	    cutsize = cut_eff(m, d, signalmc, datamc)
	    coords.append( (cutsize[0]/sigsize, 1 - cutsize[1]/datasize) )
	    testvals.append( (m, d) )

    # uncomment to be able to copy paste into Mathematica plot
    # print str(coords).replace("(","{").replace(")","}")
    # print"\n"
    # print testvals

    # make the ROC plot onto a canvas
    canv = ROOT.TCanvas("RP","Roc Plot",200,10,700,500);
    xs = [x for x,y in coords]
    ys = [y for x,y in coords]
    roc = ROOT.TGraph(len(xs), np.array(xs,dtype="float64"), np.array(ys,dtype="float64"))
    roc.Draw("ap")

    roc.GetXaxis().SetTitle("Signal Eff")
    roc.GetYaxis().SetTitle("1 - Background Eff")

    # Draw Watermarks
    wm = helpers.DrawWatermarks(0.35,0.35)

    # get the optimal parameter set
    sig = map(lambda x: x[0]/np.sqrt(1-x[1]), coords)

    sig9 = map(lambda x: x[0]/np.sqrt(1-x[1]), [c if c[0] > .9 else (0,0) for c in coords ])

    print "\n\nOptimal S/sqrt(B) for any signal efficiency:"
    print "Value: " + str(max(sig))
    print "Cutvals: " + str(testvals[sig.index(max(sig))])
    print "ROC coords: " + str(coords[sig.index(max(sig))])

    print "\nOptimal S/sqrt(B) for signal efficiency > .9:"
    print "Value: " + str( max(sig9))
    print "Cutvals: " + str(testvals[sig9.index(max(sig9))])
    print "ROC coords: " + str(coords[sig9.index(max(sig9))])

    # draw on canvas optimal cut info
    sBmax = max(sig)
    coordmax = coords[sig.index(max(sig))]
    vmax = testvals[sig.index(max(sig))]

    xdraw = 0.75
    ydraw = 0.85
    sBmax_info = ROOT.TLatex(xdraw, ydraw, "S/#sqrt{B}: %.2f" % sBmax)
    coord_info = ROOT.TLatex(xdraw, ydraw-0.06, "coords: %.2f, %.2f" % (coordmax[0], coordmax[1]))
    vmax_info = ROOT.TLatex(xdraw, ydraw-0.12, "m: %.1f, #delta: %.3f" % (vmax[0]/2, vmax[1]))
    # Draw
    words = helpers.DrawWords(sBmax_info, coord_info, vmax_info)
  
    # arrow!
    arr = ROOT.TArrow(0.85,0.75,coordmax[0], coordmax[1])
    arr.Draw()    

    canv.SaveAs(outputdir + canv_name)
    canv.Close()

    # decide on the histogram range
    if "h0" in scuts[0]:
	pTrange = (450, 2000)
    elif "h1" in scuts[0]:
	pTrange = (250, 2000)

    # now draw histograms in signal and data
    DrawHists(outputroot, scuts, "", signals, "mc_", cutvals=(vmax[0]/2, vmax[1]), Xrange=pTrange)
    DrawHists(outputroot, dcuts, "", data, "data_", cutvals=(vmax[0]/2, vmax[1]),  Xrange=pTrange) 

def ratioerror(a, b):
    if a > 0:
        return a / b * ROOT.TMath.Sqrt(1.0/a + 1.0/b)
    else:
        return 0

def options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plotter")
    parser.add_argument("--inputdir", default="TEST")
    return parser.parse_args()

def fatal(message):
    sys.exit("Error in %s: %s" % (__file__, message))

def warn(message):
    print
    print "Warning in %s: %s" % (__file__, message)
    print

if __name__ == "__main__":
    main()
