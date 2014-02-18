# run with `source run.sh`
echo "Setting up virtualenv"
which pip
if [ $? != 0 ]; then
  which easy_install
  if [ $? != 0 ]; then
    echo "Neither pip nor easy_install is found in your path"
    echo "Please install pip directly using: http://pip.readthedocs.org/en/latest/installing.html#install-or-upgrade-pip"
    exit 1
  fi
  easy_install pip
fi
if [ ! -d "certsuite_venv" ]; then
  pip install virtualenv
  virtualenv --no-site-packages certsuite_venv 
fi
source certsuite_venv/bin/activate
python setup.py install
echo "Done, running the suite"
if [ -z $1 ] ; then
  cert
else
  cert --version $1
fi
deactivate
