#!/usr/bin/env bash

set -e
set -x

v.report zipcodes_wake option=area units=hectares
v.report zipcodes_wake option=area units=hectares > data/test_1_report.txt
