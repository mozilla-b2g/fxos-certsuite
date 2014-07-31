/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. */

"use strict";

var LockScreen = {
  unlock: function() {
    let xpc = window.wrappedJSObject;
    let lwm = ("lockScreenWindowManager" in xpc) ?
      xpc.lockScreenWindowManager : null;
    let lockscreen = xpc.lockScreen || xpc.LockScreen;
    let setlock = xpc.SettingsListener.getSettingsLock();
    let system = ("System" in xpc) ? xpc.System : null;
    let lockResp = lwm ? system : lockscreen;

    setlock.set({"screen.timeout": 0});
    xpc.ScreenManager.turnScreenOn();

    waitFor(function() {
      lockscreen.unlock(true);
      waitFor(function() {
        finish(lockResp.locked);
      }, function() {
        return !lockResp.locked;
      });
    }, function() {
      return !!lockscreen;
    });
  },

  lock: function() {
    let xpc = window.wrappedJSObject;
    let lwm = ("lockScreenWindowManager" in xpc) ?
      xpc.lockScreenWindowManager : null;
    let lockscreen = xpc.lockScreen || xpc.LockScreen;
    let setlock = xpc.SettingsListener.getSettingsLock();
    let system = ("System" in xpc) ? xpc.System : null;

    // gaia > 2.0 removed the locked property on lockscreen in
    // favour of System.locked.
    let lockResp = ("locked" in lockscreen) ? lockscreen : system;

    let waitLock = function() {
      waitFor(function() {
        lockscreen.lock(true);
        waitFor(function() {
          finish(!lockResp.locked);
        }, function() {
          return lockResp.locked;
        });
      }, function() {
        return !!lockscreen;
      });
    };

    setlock.set({"screen.timeout": 0});
    xpc.ScreenManager.turnScreenOn();

    // On gaia >= 2.0 we need to be explicit about opening the lock
    // screen window because we call lockscreen.lock directly.
    if (lwm) {
      lwm.openApp();
      waitFor(function() {
        waitLock();
      }, function() {
        return lwm.states.instance.isActive();
      });
    } else {
      waitLock();
    }
  }
};
