#!/bin/sh
# Rebuild the v13 head: chin/head -> scale to 6.5 heads -> ears. Run from this folder.
set -e
python3 -I build_v13_chin.py
python3 -I scale_v13.py -- 0.907 feat_v13_65.blend
python3 -I build_v13_ears.py
