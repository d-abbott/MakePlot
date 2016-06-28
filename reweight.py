# Tony Tong; baojia.tong@cern.ch
import os, argparse, sys, math, time
#for parallel processing!
import multiprocessing as mp
from array import array
import ROOT, rootlogon, helpers
import config as CONF
from ROOT import *
ROOT.gROOT.LoadMacro("AtlasStyle.C") 
ROOT.gROOT.LoadMacro("AtlasLabels.C")
ROOT.SetAtlasStyle()

#other setups
TH1.AddDirectory(False)
StatusLabel="Internal"
ROOT.gROOT.SetBatch(True)

#define functions
def options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plotter")
    parser.add_argument("--inputdir", default="b77_c10-cb")
    parser.add_argument("--inputroot", default="sum")
    parser.add_argument("--iter", default=0)
    return parser.parse_args()

# zero the x-errors
def zeroXerror(g):
    for i in range(0,g.GetN()):
        g.SetPointEXlow(i,  0.0)
        g.SetPointEXhigh(i, 0.0) 

# function to build total background in histograma and graph format
def makeTotBkg(bkgs=[], bkgsUp=[], bkgsDown=[]):
    # total bkg histogram
    hBkg = bkgs[0].Clone("bkg")
    if len(bkgs)>1:
        hBkg.Reset()
        for h in bkgs:
            hBkg.Add(h)
    # total bkg graph with errors
    gBkg = ROOT.TGraphAsymmErrors(bkgs[0].GetNbinsX())
    # add stat errors
    for i in range(0, gBkg.GetN()):
        gBkg.SetPoint(i,       hBkg.GetBinCenter(i+1), hBkg.GetBinContent(i+1))
        gBkg.SetPointEXlow(i,  hBkg.GetBinWidth(i+1) / 2.)
        gBkg.SetPointEXhigh(i, hBkg.GetBinWidth(i+1) / 2.)
        gBkg.SetPointEYlow(i,  hBkg.GetBinError(i+1))
        gBkg.SetPointEYhigh(i, hBkg.GetBinError(i+1))
    # add syst errors (if provided)
    if len(bkgsUp)>0:
        # loop over points
        for i in range(0, gBkg.GetN()):
            ### error up
            err = math.pow(gBkg.GetErrorYhigh(i),2)
            # loop over backgrounds
            for ih in range(0, len(bkgs)):
                err += math.pow(math.fabs( bkgs[ih].GetBinContent(i+1) - bkgsUp[ih].GetBinContent(i+1) ), 2)
            gBkg.SetPointEYhigh(i, math.sqrt(err))
            ### error down
            err = math.pow(gBkg.GetErrorYlow(i),2)
            # loop over backgrounds
            for ih in range(0, len(bkgs)):
                err += math.pow(math.fabs( bkgs[ih].GetBinContent(i+1) - bkgsDown[ih].GetBinContent(i+1) ), 2)
            gBkg.SetPointEYlow(i, math.sqrt(err))

    return [hBkg, gBkg]

# function to build data/bkgd ratios
def makeDataRatio(data, bkg):
    # ratio set to one with error band 
    gRatioBand = data.Clone(data.GetName() + "_gRatioBand")
    for i in range(0, data.GetN()):
        gRatioBand.SetPoint(i, data.GetX()[i], 1.0)
        if bkg.GetY()[i] > 0:
            gRatioBand.SetPointEYhigh(i, bkg.GetErrorYhigh(i) / bkg.GetY()[i]) 
            gRatioBand.SetPointEYlow(i, bkg.GetErrorYlow(i) / bkg.GetY()[i])             
            gRatioBand.SetPointEXhigh(i, bkg.GetErrorXhigh(i)) 
            gRatioBand.SetPointEXlow(i, bkg.GetErrorXlow(i))             
    # ratio set to data/bkg with data stat errors only
    gRatioDataBkg = data.Clone(data.GetName() + "_gRatioDataBkg")
    for i in range(0, data.GetN()):
        if data.GetY()[i]>0 and bkg.GetY()[i]>0:
            gRatioDataBkg.SetPoint(i, data.GetX()[i], data.GetY()[i] / bkg.GetY()[i])
            gRatioDataBkg.SetPointEYhigh(i, data.GetErrorYhigh(i) / bkg.GetY()[i])
            gRatioDataBkg.SetPointEYlow(i, data.GetErrorYlow(i) / bkg.GetY()[i])
            gRatioDataBkg.SetPointEXhigh(i, data.GetErrorXhigh(i)) 
            gRatioDataBkg.SetPointEXlow(i, data.GetErrorXlow(i))             
        #else:
            #gRatioDataBkg.SetPoint(i, 0.0, -1000)

    return [gRatioBand,gRatioDataBkg]

def graphFromHist(hist):
    hist.SetBinErrorOption(1)
    nBins = hist.GetNbinsX()
    dataGr = ROOT.TGraphAsymmErrors(nBins)
    dataGr.SetName("data_hh")
    for i in range(nBins):
        thisX        = hist.GetBinCenter(i+1)
        thisY        = hist.GetBinContent(i+1)
        if thisY:
            thisYErrLow  = hist.GetBinErrorLow(i+1)
            thisYErrUp   = hist.GetBinErrorUp(i+1)
            binWidthOver2  = thisX - hist.GetBinLowEdge(i+1)
        else:
            thisYErrLow = 0
            thisYErrUp  = 0
            binWidthOver2  = thisX - hist.GetBinLowEdge(i+1)
        #print i, thisX, thisY, thisYErrLow, thisYErrUp                                                                                                  
        dataGr.SetPoint(i,thisX, thisY)
        dataGr.SetPointError(i, binWidthOver2, binWidthOver2, thisYErrLow, thisYErrUp)
    return dataGr

def do_variable_rebinning(hist, bins, scale=1.0):
    a=hist.GetXaxis()
    newhist=ROOT.TH1F(hist.GetName()+"_rebinned",
                      hist.GetTitle()+";"+hist.GetXaxis().GetTitle()+";"+hist.GetYaxis().GetTitle(),
                      len(bins)-1,
                      array('d',bins))
    newhist.Sumw2()
    newa=newhist.GetXaxis()

    for b in range(1, hist.GetNbinsX()+1):
        newb             = newa.FindBin(a.GetBinCenter(b))
        # Get existing new content (if any)                                                                                                              
        val              = newhist.GetBinContent(newb)
        err              = newhist.GetBinError(newb)
        # Get content to add
        ratio_bin_widths = scale*newa.GetBinWidth(newb)/a.GetBinWidth(b)
        #print "ratio_bin_widths",ratio_bin_widths
        val              = val+hist.GetBinContent(b)/ratio_bin_widths
        err              = math.sqrt(err*err+hist.GetBinError(b)/ratio_bin_widths*hist.GetBinError(b)/ratio_bin_widths)
        newhist.SetBinContent(newb,val)
        newhist.SetBinError(newb,err)
    return newhist

####################################################################################
#plot

def plotRegion(config, cut, xTitle, yTitle="N Events", Logy=0, labelPos=11, rebin=None, rebinarry=[], fitrange=[0, 0]):
    #load configurations from config file
    filepath = config["root"] 
    filename = config["inputdir"] 
    outputFolder= config["outputdir"]
    #print config, filepath, filename
    #debug
    #print filepath, filename, cut
    gStyle.SetErrorX(0)
    gStyle.SetHatchesSpacing(0.7)
    gStyle.SetHatchesLineWidth(1)

    # input file
    ifile = ROOT.TFile(filepath + filename + ".root")

    # read stuff
    data = ifile.Get("data_" + cut )
    data_est = ifile.Get("data_est_" + cut )
    qcd = ifile.Get("qcd_est_" + cut )
    #qcd_origin = ifile.Get("qcd_" + cut )
    #print "factor is ", qcd.Integral()/qcd_origin.Integral()
    ttbar = ifile.Get("ttbar_est_" + cut )
    zjet = ifile.Get("zjet_" + cut )
    RSG1_1000 = ifile.Get("RSG1_1000_" + cut )
    RSG1_1500 = ifile.Get("RSG1_1500_" + cut )
    RSG1_2500 = ifile.Get("RSG1_2500_" + cut )

    #modify data
    data.Add(ttbar, -1)
    data.Add(zjet, -1)
    data_est.Add(ttbar, -1)
    data_est.Add(zjet, -1)

    #clear factioned binns; only for reweighting purpose
    for b in range(1, data.GetNbinsX()+1): 
        if  data.GetBinContent(b) < 1:
            data.SetBinContent(b, 0)
            data.SetBinError(b, 0)

    #swap data if blinded
    if "Signal" in cut and blinded:
        data = data_est.Clone()
    #do rebin
    if not rebin == None:
        data.Rebin(rebin)
        data_est.Rebin(rebin)
        qcd.Rebin(rebin)
        ttbar.Rebin(rebin)
        zjet.Rebin(rebin)
        RSG1_1000.Rebin(rebin)
        RSG1_1500.Rebin(rebin)
        RSG1_2500.Rebin(rebin)

    if rebinarry != []:
        data      = do_variable_rebinning(data, rebinarry)
        data_est  = do_variable_rebinning(data_est, rebinarry)
        qcd       = do_variable_rebinning(qcd, rebinarry)
        ttbar     = do_variable_rebinning(ttbar, rebinarry)
        zjet      = do_variable_rebinning(zjet, rebinarry)
        RSG1_1000 = do_variable_rebinning(RSG1_1000, rebinarry)
        RSG1_1500 = do_variable_rebinning(RSG1_1500, rebinarry)
        RSG1_2500 = do_variable_rebinning(RSG1_2500, rebinarry)

    #get QS scores
    if "Signal" in cut and blinded:
        ks = 0
    else:
        ks   = data.KolmogorovTest(data_est, "QU")

    int_data = data.Integral(0, data.GetXaxis().GetNbins()+1)
    int_data_est = data_est.Integral(0, data_est.GetXaxis().GetNbins()+1)
    percentdiff   = (int_data_est - int_data)/int_data * 100.0
    #chi2 =        data.Chi2Test(data_est, "QU CHI2")
    #ndf  = chi2 / data.Chi2Test(data_est, "QU CHI2/NDF") if chi2 else 0.0

    xMin = data.GetXaxis().GetBinLowEdge(1)
    xMax = data.GetXaxis().GetBinUpEdge(data.GetXaxis().GetNbins())
    yMax = data.GetMaximum() * 1.6
    if Logy==1:
        yMax = yMax * 100
    #qcd_fit = ifile.Get("qcd_fit")
    #qcd_fitUp = ifile.Get("qcd_fitUp")
    #qcd_fitDown = ifile.Get("qcd_fitDown")

    data = makeTotBkg([data])[1]
    bkg = makeTotBkg([qcd])
    #bkg = makeTotBkg([ttbar,qcd,zjet]) #original
    # bkg/data ratios: [0] band for bkg errors, [1] bkg/data with stat errors only
    ratios = makeDataRatio(data, bkg[1])
    # canvas
    c0 = ROOT.TCanvas("c0"+filename+cut, "Insert hilarious TCanvas name here", 800, 800)
    c0.SetRightMargin(0.05)

    # top pad
    pad0 = ROOT.TPad("pad0", "pad0", 0.0, 0.31, 1., 1.)
    pad0.SetRightMargin(0.05)
    pad0.SetBottomMargin(0.0001)
    pad0.SetFrameFillColor(0)
    pad0.SetFrameBorderMode(0)
    pad0.SetFrameFillColor(0)
    pad0.SetBorderMode(0)
    pad0.SetBorderSize(0)

    pad1 = ROOT.TPad("pad1", "pad1", 0.0, 0.0, 1., 0.29)
    pad1.SetRightMargin(0.05)
    pad1.SetBottomMargin(0.38)
    pad1.SetTopMargin(0.0001)
    pad1.SetFrameFillColor(0)
    pad1.SetFillStyle(0) # transparent
    pad1.SetFrameBorderMode(0)
    pad1.SetFrameFillColor(0)
    pad1.SetBorderMode(0)
    pad1.SetBorderSize(0)

    c0.cd()
    pad0.SetLogy(Logy)
    pad0.Draw()
    pad0.cd()

    bkg[0].SetTitle("")
    bkg[0].SetStats(0)
    bkg[0].SetLineColor(ROOT.kBlack)
    bkg[0].SetLineWidth(2)
    bkg[0].GetYaxis().SetTitleFont(43)
    bkg[0].GetYaxis().SetTitleSize(28)
    bkg[0].GetYaxis().SetLabelFont(43)
    bkg[0].GetYaxis().SetLabelSize(28)
    bkg[0].GetYaxis().SetTitle(yTitle)
    bkg[0].GetYaxis().SetRangeUser(0.001, yMax)
    bkg[0].SetFillColor(ROOT.kYellow)
    bkg[0].Draw("HISTO")

    bkg[1].SetFillColor(ROOT.kBlue)
    bkg[1].SetLineColor(ROOT.kBlue)
    bkg[1].SetFillStyle(3345)
    bkg[1].SetMarkerSize(0)
    bkg[1].Draw("E2 SAME")

    #ttbar.SetLineWidth(2)
    #ttbar.SetLineColor(ROOT.kBlack)
    #ttbar.SetFillColor(ROOT.kAzure-9)
    #ttbar.Draw("HISTO SAME")

    #zjet.SetLineWidth(2)
    #zjet.SetLineColor(ROOT.kBlack)
    #zjet.SetFillColor(ROOT.kGreen+4)
    #zjet.Draw("HISTO SAME")

    # RSG1_1000.SetLineWidth(2)
    # RSG1_1000.SetLineStyle(2)
    # RSG1_1000.SetLineColor(ROOT.kViolet+7)
    # RSG1_1000.Draw("HISTO SAME")

    RSG1_1500.Scale(25)
    RSG1_1500.SetLineWidth(2)
    RSG1_1500.SetLineStyle(2)
    RSG1_1500.SetLineColor(ROOT.kPink+7)
    RSG1_1500.Draw("HISTO SAME")


    RSG1_2500.Scale(1000)
    RSG1_2500.SetLineWidth(2)
    RSG1_2500.SetLineStyle(2)
    RSG1_2500.SetLineColor(ROOT.kGreen+4)
    RSG1_2500.Draw("HISTO SAME")

    zeroXerror(data)
    data.SetMarkerStyle(20)
    data.SetMarkerSize(1)
    data.SetLineWidth(2)
    data.GetXaxis().SetLabelSize(0)
    data.GetXaxis().SetLabelOffset(999)
    if not ("Signal" in cut and blinded):
        data.Draw("EPZ SAME")

    # bottom pad
    c0.cd()
    pad1.Draw()
    pad1.cd()

    hratio = ROOT.TH1F("hratio","", 1, xMin, xMax)
    hratio.SetStats(0)
    
    hratio.GetYaxis().SetTitleFont(43)
    hratio.GetYaxis().SetTitleSize(28)
    hratio.GetYaxis().SetLabelFont(43)
    hratio.GetYaxis().SetLabelSize(28)
    hratio.GetYaxis().SetTitle("Data / Bkgd")
    hratio.GetYaxis().SetRangeUser(0.5, 1.5) #set range for ratio plot
    hratio.GetYaxis().SetNdivisions(405)

    hratio.GetXaxis().SetTitleFont(43)
    hratio.GetXaxis().SetTitleOffset(3.5)
    hratio.GetXaxis().SetTitleSize(28)
    hratio.GetXaxis().SetLabelFont(43)
    hratio.GetXaxis().SetLabelSize(28)
    hratio.GetXaxis().SetTitle(xTitle)

    hratio.Draw()

    #
    # Add stat uncertianty
    #
    ratios[0].SetFillColor(kBlue)
    ratios[0].SetFillStyle(3345)
    ratios[0].Draw("E2")

    #zeroXerror(ratios[1])
    ratios[1].SetMarkerStyle(20)
    ratios[1].SetMarkerSize(1)
    ratios[1].SetLineWidth(2)
    if not ("Signal" in cut and blinded):
        ratios[1].Draw("E0PZ SAME")
    # qcd_fit.SetLineColor(kRed)
    # qcd_fitUp.SetLineColor(kRed)
    # qcd_fitUp.SetLineStyle(2)
    # qcd_fitDown.SetLineColor(kRed)
    # qcd_fitDown.SetLineStyle(2)
    # qcd_fit.Draw("SAME")
    # qcd_fitUp.Draw("SAME")
    # qcd_fitDown.Draw("SAME")

    # Fit the ratio with a TF1
    if not ("Signal" in cut and blinded):
        if fitrange == [0, 0]:
            fitMin = xMin
            fitMax = xMax
        else:
            fitMin = fitrange[0]
            fitMax = fitrange[1]

        if ("trk0_Pt" in cut): #for the leading track jet fit
            testfit = ROOT.TF1("testfit", "pol3", xMin, xMax)
            testfit.SetParameters(0.51, 0.0076, -0.000027, -0.000000027)
            #testfit.FixParameter(3, 0) #do a 1D fit really
        elif ("trk1_Pt" in cut): #for the subleading track jet fit
            testfit = ROOT.TF1("testfit", "pol3", xMin, xMax)
            testfit.SetParameters(0.77, 0.059, -0.00002, -0.000000027)
            testfit.FixParameter(3, 0) #do a 1D fit really
        elif ("trk_pt_diff" in cut): #for the subleading track jet fit
            testfit = ROOT.TF1("testfit", "pol3", xMin, xMax)
            testfit.SetParameters(1, 0.001, -0.000001, -0.00000001)
            #testfit.FixParameter(3, 0) #do a 1D fit really
        elif ("Pt_m" in cut): #for the subleading track jet fit
            testfit = ROOT.TF1("testfit", "pol3", xMin, xMax)
            testfit.SetParameters(0.9, 0.0005, -1, 0)
            testfit.FixParameter(2, 0) #do a 1D fit really
            testfit.FixParameter(3, 0) #do a 1D fit really
        elif ("Rhh" in cut): #for the subleading track jet fit
            testfit = ROOT.TF1("testfit", "pol3", xMin, xMax)
            testfit.SetParameters(1, 0.7, -1, 0)
            testfit.FixParameter(2, 0) #do a 1D fit really
            testfit.FixParameter(3, 0) #do a 1D fit really
        else:
            testfit = ROOT.TF1("testfit", "pol3", xMin, xMax)
            testfit.SetParameters(0.9, 0.001, -0.000001, 0)
            testfit.FixParameter(2, 0) #do a 1D fit really
            testfit.FixParameter(3, 0) #do a 1D fit really
        #testfit.SetParLimits(0, -1, 2)
        #testfit.SetParLimits(1, -1, 1)
        #testfit.SetParLimits(1, -1, 1)
        ratios[1].Fit("testfit", "QWLR", "", fitMin, fitMax)
        testfit.SetLineColor(kRed)
        testfit.Draw("SAME")
        fitresult = testfit.GetParameters()
        fitprob = float(testfit.GetProb())
        myText(0.05, 0.17, 1, "y=%s + %s x + %sx^2 + %sx^3, prob:%s" % (str('%.2g' % fitresult[0]), \
            str('%.2g' % fitresult[1]), str('%.2g' % fitresult[2]), str('%.2g' % fitresult[3]), str('%.2g' % fitprob)), 22)

        #write out the reweighting parameteres; for things in the sideband only
        if ("Sideband" in cut and True):
            f_reweight = open(reweightfolder + "r" + str(iter_reweight) + "_" + cut +".txt", "w")
            f_reweight.write("reweighting function of: " + cut + "; prob is: " + str('%.2g' % fitprob) + "\n")
            f_reweight.write("par0: " + str('%.3g' % fitresult[0]) + " \n")
            f_reweight.write("par1: " + str('%.3g' % fitresult[1]) + " \n")
            f_reweight.write("par2: " + str('%.3g' % fitresult[2]) + " \n")
            f_reweight.write("par3: " + str('%.3g' % fitresult[3]) + " \n")
            f_reweight.write("low:  " + str('%.3g' % fitMin) + " \n")
            f_reweight.write("high: " + str('%.3g' % fitMax) + " \n")
            f_reweight.close()

    # draw the ratio 1 line
    line = ROOT.TLine(xMin, 1.0, xMax, 1.0)
    line.SetLineStyle(1)
    line.Draw()

    c0.cd()
    #
    # Add ks score
    #
    myText(0.2, 0.97, 1, "KS = %s" % str(('%.3g' % ks)), 22)
    myText(0.6, 0.97, 1, "(e-d)/d = %s" % str(('%.3g' % percentdiff)), 22)
    #myText(0.15, 0.92, 1, "#chi^{2} / ndf = %s / %s" % (str(chi2), str(ndf)), 22)

    # labels
    legHunit=0.05
    legH=legHunit*6 # retuned below based on number of entries to 0.05*num_entries
    legW=0.4
    leg = ROOT.TLegend(0.6, 0.75, 0.95, 0.95)
    # top right, a bit left
    ATLASLabel(0.19, 0.91, StatusLabel)
    if "15" in filepath:
        myText(0.19, 0.87, 1, "#sqrt{s}=13 TeV, 2015, 3.2 fb^{-1}", 22)
    elif "16" in filepath:
        myText(0.19, 0.87, 1, "#sqrt{s}=13 TeV, 2016, 2.6 fb^{-1}", 22)
    elif "cb" in filepath:
        myText(0.19, 0.87, 1, "#sqrt{s}=13 TeV, 15+16, 6.6 fb^{-1}", 22)
    else:
        myText(0.19, 0.87, 1, "#sqrt{s}=13 TeV, 2015, 3.2 fb^{-1}", 22)
    myText(0.19, 0.83, 1, ' ' + cut.replace("_", "; "), 22)
    ##### legend
    leg.SetNColumns(2)
    leg.SetTextFont(43)
    leg.SetTextSize(12)
    leg.SetFillColor(0)
    leg.SetFillStyle(0)
    leg.SetBorderSize(0)
    leg.AddEntry(data, "Data", "PE")
    leg.AddEntry(bkg[0], "Multijet", "F")
    leg.AddEntry(ttbar, "t#bar{t}","F")
    leg.AddEntry(zjet, "Z+jets","F")
    leg.AddEntry(bkg[1], "Stat Uncertainty", "F")
    #leg.AddEntry(RSG1_1000, "RSG1, 1TeV", "F")
    leg.AddEntry(RSG1_1500, "RSG1, 1.5TeV * 25", "F")
    leg.AddEntry(RSG1_2500, "RSG1, 2.5TeV * 1000", "F")
    #leg.AddEntry(qcd_fit, "Fit to Ratio", "L")
    #leg.AddEntry(qcd_fitUp, "#pm 1#sigma Uncertainty", "L")
    leg.SetY1(leg.GetY2()-leg.GetNRows()*legHunit)
    leg.Draw()



    # save
    postname = ("" if Logy == 0 else "_" + str(Logy)) + ("" if not ("Signal" in cut and blinded) else "_blind")
    #c0.SaveAs(outputFolder+"/"+filename.replace(".root", ".pdf"))
    c0.SaveAs(outputFolder+ "/" + filename + "_" + cut + postname + ".png")
    c0.SaveAs(outputFolder+ "/" + filename + "_" + cut + postname + ".pdf")
    #c0.SaveAs(outputFolder+ "/" + filename + "_" + cut + ".pdf")
    #c0.SaveAs(outputFolder+ "/" + filename + "_" + cut + ".eps")

    pad0.Close()
    pad1.Close()
    c0.Close()
    del(data)
    del(data_est)
    del(qcd)
    del(ttbar)
    del(zjet)
    del(RSG1_1000)
    del(RSG1_1500)
    del(RSG1_2500)

    ##should only be run non-parellel.
    #if ("Sideband" in cut and True):
        #outputroot.cd()
        #ratios[1].SetName(cut)
        #ratios[1].Write()




def dumpRegion(config):
    rebin_dic = {}
    #different rebin for each catagory
    if "TwoTag" in config["cut"]:
        rebin_dic["mHH_l"]      = array('d', range(0, 2000, 200) + range(2000, 4000, 400))
        rebin_dic["mHH_pole"]   = array('d', range(0, 2000, 200) + range(2000, 4000, 400))
        rebin_dic["j0_Pt"]      = array('d', range(0, 800, 50) + [800, 1000, 1300, 2000])
        rebin_dic["j1_Pt"]      = array('d', range(0, 600, 50) + [600, 700, 800, 1000, 1300, 2000])
        rebin_dic["trk0_Pt"]    = array('d', range(0, 600, 40) + [600, 700, 800, 1000, 1300, 2000])
        rebin_dic["trk1_Pt"]    = array('d', range(0, 200, 20) + [200, 250, 400])
        rebin_dic["trk_dr"]     = array('d', [x * 0.1 for x in range(0, 10)] + [1, 1.5, 2])
        rebin_dic["trk_pT_diff"]= array('d', range(0, 500, 50) + [500, 600, 700, 800])
    if "ThreeTag" in config["cut"]:
        rebin_dic["mHH_l"]      = array('d', range(0, 2000, 200) + range(2000, 4000, 400))
        rebin_dic["mHH_pole"]   = array('d', range(0, 2000, 200) + range(2000, 4000, 400))
        rebin_dic["j0_Pt"]      = array('d', range(0, 800, 50) + [800, 1000, 1300, 2000])
        rebin_dic["j1_Pt"]      = array('d', range(0, 600, 50) + [600, 700, 800, 1000, 1300, 2000])
        rebin_dic["trk0_Pt"]    = array('d', range(0, 500, 50) + [500, 600, 1000, 2000])
        rebin_dic["trk1_Pt"]    = array('d', range(0, 180, 30) + [180, 400])
        rebin_dic["trk_dr"]     = array('d', [x * 0.1 for x in range(0, 10)] + [1, 1.5, 2])
        rebin_dic["trk_pT_diff"]= array('d', range(0, 500, 50) + [500, 600, 800])
    if "FourTag" in config["cut"]:
        rebin_dic["mHH_l"]      = array('d', range(0, 2000, 200) + range(2000, 4000, 400))
        rebin_dic["mHH_pole"]   = array('d', range(0, 2000, 200) + range(2000, 4000, 400))
        rebin_dic["j0_Pt"]      = array('d', range(0, 700, 100) + [700, 1000, 2000])
        rebin_dic["j1_Pt"]      = array('d', range(0, 500, 100) + [500, 1000, 2000])
        rebin_dic["trk0_Pt"]    = array('d', range(0, 100, 50) + range(100, 500, 100) + [500, 2000])
        rebin_dic["trk1_Pt"]    = array('d', range(0, 200, 40) + [200, 400])
        rebin_dic["trk_dr"]     = array('d', [x * 0.1 for x in range(0, 10, 2)] + [1, 1.5, 2])
        rebin_dic["trk_pT_diff"]= array('d', range(0, 400, 50) + [400, 800])
    #all the kinematic plots that needs to be plotted; set the axis and name, rebin information 1 by 1
    plotRegion(config, cut=config["cut"] + "mHH_l",              xTitle="m_{2J} [GeV]", rebinarry=rebin_dic["mHH_l"], fitrange=[800, 2000])
    plotRegion(config, cut=config["cut"] + "mHH_l",              xTitle="m_{2J} [GeV]", rebinarry=rebin_dic["mHH_l"], Logy=1, fitrange=[800, 2000])
    plotRegion(config, cut=config["cut"] + "mHH_pole",           xTitle="m_{2J} [GeV]", rebinarry=rebin_dic["mHH_pole"], fitrange=[800, 2000])
    plotRegion(config, cut=config["cut"] + "mHH_pole",           xTitle="m_{2J} [GeV]", rebinarry=rebin_dic["mHH_pole"], Logy=1, fitrange=[800, 2000])
    plotRegion(config, cut=config["cut"] + "leadHCand_trk0_Pt",  xTitle="J0 leadtrk p_{T} [GeV]", rebinarry=rebin_dic["trk0_Pt"], fitrange=[0, 700])
    plotRegion(config, cut=config["cut"] + "sublHCand_trk0_Pt",  xTitle="J1 leadtrk p_{T} [GeV]", rebinarry=rebin_dic["trk0_Pt"], fitrange=[0, 700])
    plotRegion(config, cut=config["cut"] + "leadHCand_trk1_Pt",  xTitle="J0 subltrk p_{T} [GeV]", rebinarry=rebin_dic["trk1_Pt"], fitrange=[0, 200])
    plotRegion(config, cut=config["cut"] + "sublHCand_trk1_Pt",  xTitle="J1 subltrk p_{T} [GeV]", rebinarry=rebin_dic["trk1_Pt"], fitrange=[0, 200])
    plotRegion(config, cut=config["cut"] + "leadHCand_Mass",     xTitle="J0 m [GeV]", rebin=2, fitrange=[60, 170])
    plotRegion(config, cut=config["cut"] + "sublHCand_Mass",     xTitle="J1 m [GeV]", rebin=2, fitrange=[60, 170])
    #plotRegion(config, cut=config["cut"] + "Rhh",                xTitle="Rhh", rebin=2)
    plotRegion(config, cut=config["cut"] + "hCandDr",            xTitle="#Delta R", rebin=2, fitrange=[2, 3.6])
    plotRegion(config, cut=config["cut"] + "hCandDeta",          xTitle="#Delta #eta", rebin=2, fitrange=[0, 1.7])
    plotRegion(config, cut=config["cut"] + "hCandDphi",          xTitle="#Delta #phi", rebin=2)
    plotRegion(config, cut=config["cut"] + "leadHCand_Pt_m",     xTitle="J0 p_{T} [GeV]", rebinarry=rebin_dic["j0_Pt"], fitrange=[450, 1000])
    plotRegion(config, cut=config["cut"] + "leadHCand_Pt_m",     xTitle="J0 p_{T} [GeV]", rebinarry=rebin_dic["j0_Pt"], Logy=1, fitrange=[450, 1000])
    plotRegion(config, cut=config["cut"] + "leadHCand_Eta",      xTitle="J0 #eta", rebin=2, fitrange=[-2, 2])
    plotRegion(config, cut=config["cut"] + "leadHCand_Phi",      xTitle="J0 #phi", rebin=4, fitrange=[-3, 3])
    plotRegion(config, cut=config["cut"] + "leadHCand_trk_dr",   xTitle="J0 dRtrk", rebin=2, rebinarry=rebin_dic["trk_dr"], fitrange=[0.2, 1.2])
    plotRegion(config, cut=config["cut"] + "sublHCand_Pt_m",     xTitle="J1 p_{T} [GeV]", rebinarry=rebin_dic["j1_Pt"], fitrange=[250, 1000])
    plotRegion(config, cut=config["cut"] + "sublHCand_Pt_m",     xTitle="J1 p_{T} [GeV]", rebinarry=rebin_dic["j1_Pt"], Logy=1, fitrange=[250, 1000])
    plotRegion(config, cut=config["cut"] + "sublHCand_Eta",      xTitle="J1 #eta", rebin=2, fitrange=[-2, 2])
    plotRegion(config, cut=config["cut"] + "sublHCand_Phi",      xTitle="J1 #phi", rebin=4, fitrange=[-3, 3])
    plotRegion(config, cut=config["cut"] + "sublHCand_trk_dr",   xTitle="J1 dRtrk", rebin=2, rebinarry=rebin_dic["trk_dr"], fitrange=[0.2, 1.2])
    plotRegion(config, cut=config["cut"] + "leadHCand_ntrk",     xTitle="J0 Ntrk", fitrange=([1, 6] if "TwoTag" in config["cut"] else [2, 4]))
    plotRegion(config, cut=config["cut"] + "sublHCand_ntrk",     xTitle="J1 Ntrk", fitrange=([1, 6] if "TwoTag" in config["cut"] else [2, 4]))
    plotRegion(config, cut=config["cut"] + "leadHCand_trk_pt_diff_frac", xTitle="J0 pt diff", rebinarry=rebin_dic["trk_pT_diff"])
    plotRegion(config, cut=config["cut"] + "sublHCand_trk_pt_diff_frac", xTitle="J1 pt diff", rebinarry=rebin_dic["trk_pT_diff"])
    #plotRegion(config, cut=config["cut"] + "hCand_Pt_assy",      xTitle="pT assy", fitrange=[0, 0.5])

    print config["outputdir"], "done!"


##################################################################################################
# Main

def main():

    start_time = time.time()
    ops = options()
    global blinded
    blinded = True
    global iter_reweight
    iter_reweight = int(ops.iter)
    #setup basics
    inputdir = ops.inputdir
    inputroot = ops.inputroot
    inputpath = CONF.inputpath + inputdir + "/"
    rootinputpath = inputpath + inputroot + ("r" + str(iter_reweight - 1) if iter_reweight > 0 else "") + "_"
    print "input root file is: ", rootinputpath

    global StatusLabel
    StatusLabel = "Internal" ##StatusLabel = "Preliminary"

    global reweightfolder
    reweightfolder = inputpath + "Reweight/"
    helpers.checkpath(reweightfolder)

    global outputroot
    outputroot = ROOT.TFile(reweightfolder + "reweights.root", "recreate")
    # plot in the control region #
    # outputFolder = inputpath + inputroot + "Plot/" + "Sideband"
    # plotRegion(rootinputpath, inputdir, cut="FourTag" + "_" + "Sideband" + "_" + "mHH_l", xTitle="m_{2J} [GeV]")
    # plotRegion(rootinputpath, inputdir, cut="FourTag" + "_" + "Sideband" + "_" + "mHH_l", xTitle="m_{2J} [GeV]", Logy=1)

    region_lst = ["Sideband", "Control", "Signal", "ZZ"]
    cut_lst    = ["TwoTag_split", "ThreeTag", "FourTag"]

    #create master list
    inputtasks = []
    #fill the task list
    for i, region in enumerate(region_lst):
        if inputroot == "sum":
            inputroot = ""
        outputFolder = inputpath + inputroot + "Plot_r" + str(iter_reweight) + "/" + region
        helpers.checkpath(outputFolder)

        for j, cut in enumerate(cut_lst):
            config = {}
            config["root"] = rootinputpath
            config["inputdir"] = inputdir
            config["outputdir"] = outputFolder
            config["cut"] = cut + "_" + region + "_"
            inputtasks.append(config)
    #parallel compute!
    print " Running %s jobs on %s cores" % (len(inputtasks), mp.cpu_count()-1)
    npool = min(len(inputtasks), mp.cpu_count()-1)
    pool = mp.Pool(npool)
    pool.map(dumpRegion, inputtasks)
    ##for debug
    #dumpRegion(inputtasks[0])
    # dumpRegion(inputtasks[1])
    # dumpRegion(inputtasks[2])
    outputroot.Close()
    print("--- %s seconds ---" % (time.time() - start_time))

    
#####################################
if __name__ == '__main__':
    main()
