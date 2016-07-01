<<<<<<< HEAD
### iteration of reweighting!!!, takes the first argument as the reweighting configuration file under script
homepath="/afs/cern.ch/user/g/gputnam/"
workpath="/afs/cern.ch/work/g/gputnam/public/Output/"
inch=F_c10-cb
re=$1

## iteration of reweighting!!!, takes the first argument as the reweighting configuration file under script
for i in {0..8}
do
	re=$1
	iter=$i
	ch=f_c10-cb-15-$"_"$re"_"$iter
	#ch=f_c10-cb
	echo $ch, "is the channel and iteration!"
	python PlotTinyTree.py --inputdir $inch --outputdir $ch --reweight $re --iter $iter #$re
	python get_count.py --inputdir $ch
	python plot.py --inputdir $ch
	python reweight.py --inputdir $ch

#publish online
echo "Publish!"
if [ ! -d $homepath"/www/share/hh4b/reweight/"$ch ]; then
  mkdir $homepath"/www/share/hh4b/reweight/"$ch
fi
if [ ! -d $homepath"/www/share/hh4b/plot/"$ch ]; then
  mkdir $homepath"/www/share/hh4b/plot/"$ch
fi
if [ ! -d $homepath"/www/share/hh4b/express/"$ch ]; then
  mkdir $homepath"/www/share/hh4b/express/"$ch
fi
find $workpath$ch$"/Plot_r0/Sideband/" -name '*.png' -exec cp {} $homepath"/www/share/hh4b/reweight/"$ch \;
find $workpath$ch$"/Plot/Sideband/" -name '*.png' -exec cp {} $homepath"/www/share/hh4b/plot/"$ch \;
find $workpath$ch$"/Plot/Control/" -name '*.png' -exec cp {} $homepath"/www/share/hh4b/plot/"$ch \;
find $workpath$ch$"/Plot/Sideband/" -name '*mHH_l.png' -exec cp {} $homepath"/www/share/hh4b/express/"$ch \;
find $workpath$ch$"/Plot/Control/" -name '*mHH_l.png' -exec cp {} $homepath"/www/share/hh4b/express/"$ch \;
##generate the text file 
echo " reweight: "$re$" iter: "$iter > $homepath"/www/share/hh4b/express/"$ch$"/"shortdescription.txt
echo " reweight: "$re$" iter: "$iter > $homepath"/www/share/hh4b/plot/"$ch$"/"shortdescription.txt
echo " reweight: "$re$" iter: "$iter > $homepath"/www/share/hh4b/reweight/"$ch$"/"shortdescription.txt
cd $homepath"/www/share/"
python createHtmlOverview.py
done
echo "Done!"


# ## iteration of reweighting!!!, takes the first argument as the reweighting configuration file under script
# for i in {0..10}
# do
# 	re=$1
# 	inch=F_c10-cb
# 	iter=$i
# 	ch=f_mcut-cb$"_"$re"_"$iter
# 	#ch=f_c10-cb
# 	echo $ch, "is the channel and iteration!"
# 	python PlotTinyTree.py --inputdir $inch --outputdir $ch --reweight $re --iter $iter #$re
# 	python get_count.py --inputdir $ch
# 	python plot.py --inputdir $ch
# 	python reweight.py --inputdir $ch

# 	##publish online
# 	echo "Publish!"
# 	if [ ! -d $homepath"/www/share/hh4b/reweight/"$ch ]; then
# 	  mkdir $homepath"/www/share/hh4b/reweight/"$ch
# 	fi
# 	if [ ! -d $homepath"/www/share/hh4b/plot/"$ch ]; then
# 	  mkdir $homepath"/www/share/hh4b/plot/"$ch
# 	fi
# 	if [ ! -d $homepath"/www/share/hh4b/express/"$ch ]; then
# 	  mkdir $homepath"/www/share/hh4b/express/"$ch
# 	fi
# 	find $workpath$ch$"/Plot_r0/Sideband/" -name '*.png' -exec cp {} $homepath"/www/share/hh4b/reweight/"$ch \;
# 	find $workpath$ch$"/Plot/Sideband/" -name '*.png' -exec cp {} $homepath"/www/share/hh4b/plot/"$ch \;
# 	find $workpath$ch$"/Plot/Control/" -name '*.png' -exec cp {} $homepath"/www/share/hh4b/plot/"$ch \;
# 	find $workpath$ch$"/Plot/Sideband/" -name '*mHH_l.png' -exec cp {} $homepath"/www/share/hh4b/express/"$ch \;
# 	find $workpath$ch$"/Plot/Control/" -name '*mHH_l.png' -exec cp {} $homepath"/www/share/hh4b/express/"$ch \;
# 	##generate the text file 
# 	echo " reweight: "$re$" iter: "$iter > $homepath"/www/share/hh4b/express/"$ch$"/"shortdescription.txt
# 	echo " reweight: "$re$" iter: "$iter > $homepath"/www/share/hh4b/plot/"$ch$"/"shortdescription.txt
# 	echo " reweight: "$re$" iter: "$iter > $homepath"/www/share/hh4b/reweight/"$ch$"/"shortdescription.txt
# 	cd $homepath"/www/share/"
# 	python createHtmlOverview.py
# 	cd -
# 	echo "Done!"
# done

