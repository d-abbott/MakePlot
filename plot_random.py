import ROOT, rootlogon
import argparse
import array
import copy
import glob
import helpers
import os
import sys
import time

ROOT.gROOT.SetBatch(True)
from ROOT import gStyle    




def options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputdir", default="b77")
    return parser.parse_args()

def main():

    ops = options()

    ops = options()
    inputdir = ops.inputdir
    global inputpath
    inputpath = "/afs/cern.ch/work/b/btong/bbbb/NewAnalysis/Output/" + inputdir + "/"
    global outputpath
    outputpath = "/afs/cern.ch/work/b/btong/bbbb/NewAnalysis/Output/" + inputdir + "/" + "Plot/Other/"

    if not os.path.exists(outputpath):
        os.makedirs(outputpath)

    #side band shapes
    DrawSignalPlot("data_test/hist-MiniNTuple.root", "NoTag_Sideband", keyword="mH0H1", noteword="PhysMain", prename="Sideband", Xrange=[0, 320], Yrange=[0, 320])
    DrawSignalPlot("data_test/hist-MiniNTuple.root", "NoTag_Control", keyword="mH0H1", noteword="PhysMain", prename="Control", Xrange=[50, 200], Yrange=[50, 200])

    #signalregion shape comparison
    inputroot = "sum_" + inputdir + ".root"
    DrawSRcomparison(inputroot, inputdata="ttbar")
    DrawSRcomparison(inputroot, inputdata="ttbar", Logy=1)
    DrawSRcomparison(inputroot, inputdata="qcd_est")
    DrawSRcomparison(inputroot, inputdata="qcd_est", Logy=1)

    #draw the mhh before and after scale
    DrawScalecomparison(inputroot, norm=False)
    DrawScalecomparison(inputroot, norm=True, Logy=1)

def DrawSignalPlot(inputname, inputdir, keyword="_", noteword="PhysMain", prename="", Xrange=[0, 0], Yrange=[0, 0]):
    #print inputdir
    inputroot = ROOT.TFile.Open(inputpath + inputname)
    inputroot.cd(inputdir)
    for key in ROOT.gDirectory.GetListOfKeys():
        kname = key.GetName()
        if keyword in kname:

            ROOT.gStyle.SetPadRightMargin(0.15)

            temp_hist = ROOT.gDirectory.Get(kname).Clone()
            canv = ROOT.TCanvas(temp_hist.GetName(), temp_hist.GetTitle(), 800, 800)
            if Xrange != [0, 0]:
                temp_hist.GetXaxis().SetRangeUser(Xrange[0], Xrange[1])
            if Yrange != [0, 0]:
                temp_hist.GetYaxis().SetRangeUser(Yrange[0], Yrange[1])
                temp_hist.GetYaxis().SetTitleOffset(1.8)

            temp_hist.Draw("colz")

            xatlas, yatlas = 0.35, 0.87
            atlas = ROOT.TLatex(xatlas, yatlas, "ATLAS Internal")
            hh4b  = ROOT.TLatex(xatlas, yatlas-0.06, "RSG c=1.0")
            lumi  = ROOT.TLatex(xatlas, yatlas-0.12, "Data #sqrt{s} = 13 TeV")
            watermarks = [atlas, hh4b, lumi]
            for wm in watermarks:
                wm.SetTextAlign(22)
                wm.SetTextSize(0.04)
                wm.SetTextFont(42)
                wm.SetNDC()
                wm.Draw()

            canv.SaveAs(outputpath + prename + "_" +  canv.GetName() + ".pdf")
            canv.Close()
    inputroot.Close()

def DrawSRcomparison(inputname, inputdata="ttbar", inputtype=["TwoTag_split_Signal", "ThreeTag_Signal", "FourTag_Signal"], keyword="mHH_l", prename="", Xrange=[0, 0], Yrange=[0, 0], norm=True, Logy=0):
    #print inputdir
    inputroot = ROOT.TFile.Open(inputpath + inputname)
    tempname = inputdata + "_" + "compare" + "_" + keyword + ("" if Logy == 0 else "_" + str(Logy))
    canv = ROOT.TCanvas(tempname, tempname, 800, 800)
    canv.SetLogy(Logy)
    xleg, yleg = 0.5, 0.7
    legend = ROOT.TLegend(xleg, yleg, xleg+0.15, yleg+0.2)
    counter = 0
    maxbincontent = (0.2 if Logy ==0 else 10)

    for key in ROOT.gDirectory.GetListOfKeys():
        kname = key.GetName()
        for i, region in enumerate(inputtype):
            if inputdata + "_" + region  + "_" + keyword in kname:

                temp_hist = ROOT.gDirectory.Get(kname)
                #print temp_hist.GetName()
                temp_hist.SetLineColor(2 + i)
                temp_hist.SetMarkerStyle(20 + i)
                temp_hist.SetMarkerColor(2 + i)
                temp_hist.SetMarkerSize(1)
                if norm:
                    temp_hist.Scale(1/temp_hist.Integral(0, temp_hist.GetXaxis().GetNbins()+1))

                if Xrange != [0, 0]:
                    temp_hist.GetXaxis().SetRangeUser(Xrange[0], Xrange[1])
                if Yrange != [0, 0]:
                    temp_hist.GetYaxis().SetRangeUser(Yrange[0], Yrange[1])


                maxbincontent = max(maxbincontent, temp_hist.GetMaximum())
                temp_hist.SetMaximum(maxbincontent * 1.5)
                legend.AddEntry(temp_hist, region.replace("_", " "), "apl")

                if counter==0:
                    temp_hist.Draw("")
                else:
                    temp_hist.Draw("same")
                counter += 1

    legend.SetBorderSize(0)
    legend.SetMargin(0.3)
    legend.SetTextSize(0.04)
    legend.Draw()

    # draw watermarks
    xatlas, yatlas = 0.35, 0.87
    atlas = ROOT.TLatex(xatlas, yatlas, "ATLAS Internal")
    hh4b  = ROOT.TLatex(xatlas, yatlas-0.06, "RSG c=1.0")
    lumi  = ROOT.TLatex(xatlas, yatlas-0.12, "MC #sqrt{s} = 13 TeV")
    watermarks = [atlas]
    for wm in watermarks:
        wm.SetTextAlign(22)
        wm.SetTextSize(0.04)
        wm.SetTextFont(42)
        wm.SetNDC()
        wm.Draw()

    canv.SaveAs(outputpath + canv.GetName() + ".pdf")
    canv.Close()

    inputroot.Close()

def DrawScalecomparison(inputname, inputtype=["TwoTag_split_Signal", "ThreeTag_Signal", "FourTag_Signal"], prename="", Xrange=[0, 3000], Yrange=[0, 0], norm=True, Logy=0):
    #print inputdir
    inputroot = ROOT.TFile.Open(inputpath + inputname)
    inputdata= ["data_est", "RSG1_1500", "RSG1_2500"]
    for i, region in enumerate(inputtype):

        tempname = region + "_" + "compare_scale" + "_mHH" + ("" if Logy == 0 else "_" + str(Logy))
        canv = ROOT.TCanvas(tempname, tempname, 800, 800)
        canv.SetLogy(Logy)
        xleg, yleg = 0.52, 0.73
        legend = ROOT.TLegend(xleg, yleg, xleg+0.3, yleg+0.2)
        counter = 0
        maxbincontent = (0.3 if Logy ==0 else 10)

        for j, data in enumerate(inputdata):
            for key in ROOT.gDirectory.GetListOfKeys():
                kname = key.GetName()
                if (data + "_" + region  + "_" + "mHH_l"  in kname) or (data + "_" + region  + "_" + "mHH_pole" in kname):
                    #print kname
                    temp_hist = ROOT.gDirectory.Get(kname)
                    #print temp_hist.GetName()
                    temp_hist.SetLineColor(2 + j)
                    temp_hist.SetMarkerStyle(20 + j)
                    if "pole" in kname: temp_hist.SetMarkerStyle(20 + j + len(inputdata))
                    temp_hist.SetMarkerColor(2 + j)
                    temp_hist.SetMarkerSize(1)
                    if norm:
                        temp_hist.Scale(1/temp_hist.Integral(0, temp_hist.GetXaxis().GetNbins()+1))

                    if Xrange != [0, 0]:
                        temp_hist.GetXaxis().SetRangeUser(Xrange[0], Xrange[1])
                    if Yrange != [0, 0]:
                        temp_hist.GetYaxis().SetRangeUser(Yrange[0], Yrange[1])

                    maxbincontent = max(maxbincontent, temp_hist.GetMaximum())
                    
                    temp_hist.SetMaximum(maxbincontent * 1.5)
                    legend.AddEntry(temp_hist, data.replace("_", " ") + ("" if "pole" not in kname else " scaled"), "apl")

                    if counter==0:
                        temp_hist.Draw("")
                    else:
                        temp_hist.Draw("same")

                    counter += 1

        legend.SetBorderSize(0)
        legend.SetMargin(0.3)
        legend.SetTextSize(0.04)
        legend.Draw()

        # draw watermarks
        xatlas, yatlas = 0.35, 0.87
        atlas = ROOT.TLatex(xatlas, yatlas, "ATLAS Internal")
        hh4b  = ROOT.TLatex(xatlas, yatlas-0.06, "RSG c=1.0")
        lumi  = ROOT.TLatex(xatlas, yatlas-0.12, "MC #sqrt{s} = 13 TeV")
        watermarks = [atlas]
        for wm in watermarks:
            wm.SetTextAlign(22)
            wm.SetTextSize(0.04)
            wm.SetTextFont(42)
            wm.SetNDC()
            wm.Draw()

        canv.SaveAs(outputpath + canv.GetName() + ".pdf")
        canv.Close()

    inputroot.Close()

if __name__ == "__main__":
    main()
