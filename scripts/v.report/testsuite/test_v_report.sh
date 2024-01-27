#!/usr/bin/env bash

set -e
set -x

v.report zipcodes_wake option=area units=hectares > data/test_1_report.txt

cd data

for i in `ls *.txt` ; do
    diff $i "`basename $i .txt`.ref" >> out.diff
done

CHAR_NUM=`cat out.diff | wc -c`

# Return as exit status 0 in case no diffs are found
exit $CHAR_NUM
