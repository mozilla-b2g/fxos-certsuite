#!/bin/bash
echo "Setting up virtualenv"

function notify_sudo {
  if [ "$SUDO_NOTIFY" = "1" ]; then
    return
  fi
  echo "This script requires sudo access to install pip and/or virtualenv "
  echo "on your system.  Please enter your sudo password if prompted. "
  echo "If you don't have sudo access, you will need a system administrator "
  echo "to install pip and virtualenv for you."
  SUDO_NOTIFY=1
}

which pip
if [ $? != 0 ]; then
  which easy_install
  if [ $? != 0 ]; then
    echo "Neither pip nor easy_install is found in your path"
    echo "Please install pip directly using: http://pip.readthedocs.org/en/latest/installing.html#install-or-upgrade-pip"
    exit 1
  fi
  notify_sudo
  sudo easy_install pip || { echo 'error installing pip' ; exit 1; }
fi

which virtualenv
if [ $? != 0 ]; then
  notify_sudo
  sudo pip install virtualenv || { echo 'error installing virtualenv' ; exit 1; }
fi

if [ ! -d "certsuite_venv" ]; then
  virtualenv --no-site-packages certsuite_venv || { echo 'error creating virtualenv' ; exit 1; }
fi

source certsuite_venv/bin/activate
python setup.py install
echo "Done, running the suite"
cert $@
deactivate
