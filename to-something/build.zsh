#!/bin/zsh

source env/bin/activate;
rm deployed.pkl;
rm -rf www;
python main.py;
rm -rf www/static;
python deploy.py;
deactivate;