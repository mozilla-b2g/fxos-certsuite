#!/bin/bash
use_adb() {
  ACTION=$1
  EXTRA_EXPLANATION=$2
  shift 2
  adb $@
  if [ $? != 0 ]; then
    echo "Could not $ACTION. Is it listed on 'adb devices'?"
    echo "If not, please follow README instructions to setup adb on the device."
    echo "If it is listed in 'adb devices', is the device rooted?"
    if [ ! -z "$EXTRA_EXPLANATION"]; then
      echo $EXTRA_EXPLANATION
    fi
    exit 1
  fi
}
use_adb "remount device" "" remount
use_adb "push special-powers to the device" "If it is rooted, does the special-powers@mozilla.org folder exist in your current working directory?" push special-powers\@mozilla.org /system/b2g/distribution/bundles/special-powers\@mozilla.org
use_adb "push marionette to the device" "If it is rooted, does the marionette@mozilla.org folder exist in your current working directory??" push marionette\@mozilla.org /system/b2g/distribution/bundles/marionette\@mozilla.org
use_adb "call adb shell to stop b2g" "" shell stop b2g
use_adb "call adb shell to start b2g" "" shell start b2g
echo "waiting for b2g to start"
TRIES=30
while [ $TRIES -gt 0 ]; do
  sleep 5
  echo "checking if b2g has started"
  use_adb "call adb shell to check b2g-ps" "" shell b2g-ps | grep b2g
  if [ $? == 0 ]; then
    break
  fi
  let TRIES=TRIES-1
done
if [ $TRIES == 0 ]; then
  echo "b2g did not start up!"
  exit 1
fi
use_adb "forward adb port" "If it is rooted, is port 2828 already in use? Try 'nc -z localhost 2828'" forward tcp:2828 tcp:2828
