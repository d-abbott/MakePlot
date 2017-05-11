#Tony: master configuration file, specifies all the necessary paths
import ROOT, helpers, os

#get current directory
currpath    = os.path.abspath(os.curdir)
#change this to your home directory of everything; should be where the code is checked out
toppath     =  os.path.dirname(currpath)
#input top directory for the root files
#inputpath   =  toppath + "/Output/"
inputpath = "/titan_rw/atlas/common/dabbott/"
helpers.checkpath(inputpath)
#output top directory for the output plots/root files
outputpath  =  toppath +"/Output/"
helpers.checkpath(outputpath)
#output top directory for only plots
outplotpath =  toppath +"/Plot/"
helpers.checkpath(outplotpath)
#put in the working directory name; default b77~
workdir     =  "Moriond" #"Moriond" #b77
#check if reference folder exists
refpath     =  toppath +"/Output/ref/"
#check if reference folder exists
fullstudy   =  True
#check if doing my thesis; if so, disable all the ATLAS labels
thesis      =  False
#check if the path exists
if not os.path.exists(refpath):
	print "please copy the directory: /afs/cern.ch/user/b/btong/work/public/RunIIHH4b/ref over to Output/ref!!!"
else:
	pass
#setup all the other constants
#MC mass points; <=400 has no entries!
mass_lst   = [500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1800, 2000, 2250, 2500, 2750, 3000]#, 3500, 4000, 4500, 5000, 6000]
#for data and MC, number of file splits, right now 14 = 2 * (8 - 1)
##this affects the cutflow plot error!!! because root reduces the error by sqrt(N). Need to scale it back up...
splits     = 14
#plot color variables
clr_lst    = [ROOT.kRed+1, ROOT.kBlue+1, ROOT.kOrange+7, ROOT.kGreen+3, ROOT.kPink-8, 
	ROOT.kMagenta+2, ROOT.kCyan+1, ROOT.kViolet-6, ROOT.kTeal+3, ROOT.kBlue+6, ROOT.kSpring-7, 
	ROOT.kRed-1, ROOT.kBlue-1, ROOT.kOrange-7, ROOT.kGreen-3, ROOT.kPink+8,
	ROOT.kRed-2, ROOT.kBlue-2, ROOT.kOrange-6, ROOT.kGreen-4, ROOT.kPink+7]
#plot marker style variables
mrk_lst  = range(20, 40)
#defuault root file name
hist_r = "hist-MiniNTuple.root"
#set the blinding status
blind  = True
 #False
#current total luminiosity, in fb 22.1; 13.0
totlumi = 36.1
#color dictionary for plotting style
col_dic = {"syst":ROOT.kGray+2}
#size for legend
legsize = 20
paperlegsize = 28
StatusLabel = "Internal" #"Preliminary"
