/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. */

'use strict';

var MCTSApps = {
  getMCTSManifestURL: function(appname) {
    let req = navigator.mozApps.mgmt.getAll();

    //onsuccess failed, use wait instead for now.
    setTimeout(function(){
      console.log("In loop");
      for(var i = 0; i < req.result.length; i++) {
        console.log(req.result[i].manifest.name);
        if(req.result[i].manifest.name == appname) {
          marionetteScriptFinished(req.result[i].manifestURL);
        }
      }
    }, 5000);
  }
};

