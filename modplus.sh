#!/usr/bin/env bash
source "./modvenv/bin/activate"
git pull
pip3 install --upgrade certifi setuptools wheel pip
pip3 install -r requirements.txt
python3 -u modplus.py