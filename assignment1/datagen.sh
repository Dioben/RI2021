#!/bin/bash
rm datatable.csv #reset file we're appending to
for file in *.tsv.gz
do
rm blockdump*
rm mergedindex*
rm masterindex*
time1=$(python3 indexer.py --source $file --stopsize 25)
tempfilecount=$(find . -maxdepth 1 -name "blockdump*" |wc -l)
time2=$(python3 merger.py)
indextime=$(echo "$time1 + $time2" | bc)
boottime=$(python3 loader.py --timer-only)
vocabsize=$(wc -l < masterindex.ssv)
indexsize=$(stat -c%s masterindex.ssv)
for f in mergedindex*
do
add=$(stat -c%s $f)
indexsize=$(expr $add + $indexsize)
done
echo "$file,$indextime,$indexsize,$vocabsize,$tempfilecount,$boottime" >>datatable.csv

done