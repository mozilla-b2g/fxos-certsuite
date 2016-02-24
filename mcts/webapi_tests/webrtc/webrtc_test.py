# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette_driver.wait import Wait


class WebrtcTestCommon(object):

    def webrtc_message_test(self):
        return self.marionette.execute_async_script("""
          var pc1;
          var pc2;
          var dc1;
          var dc2;
          var channel1;
          var channel2;
          var num_channels = 0;
          var datachannels = [];

          var pc1_offer;
          var pc2_answer;
          var iter = 0;
          var iter2 = 0;

          var log = function(msg) {
            marionetteScriptFinished(msg);
          };

          var sendit = function (which) {
            iter = iter + 1;
            if (which == 1) {
              dc1.send("test from pc2");
            } else if (which == 2) {
              dc2.send("test from pc1");
            }
          };

          function failed(code) {;};

          function step1(offer) {
            pc2 = new mozRTCPeerConnection();
            pc1.didSetRemote = false;
            pc2.didSetRemote = false;
            pc1.ice_queued = [];
            pc2.ice_queued = [];
            
            pc2.ondatachannel = function(event) {
              var mychannel = event.channel;
              datachannels[num_channels] = mychannel;
              num_channels++;
              mychannel.binaryType = "blob";
              dc2 = mychannel;

              mychannel.onmessage = function(evt) {
                iter2 = iter2 + 1;
                log("pc1 said: " + evt.data,"red");
              };

              mychannel.onopen = function() {;};
              mychannel.onclose = function() {;};
            };

            pc2.onclosedconnection = function() {;};
            pc2.onaddstream = function(obj) {;};

            pc2.onicecandidate = function(obj) {
              if (obj.candidate) {
                if (pc1.didSetRemote) {
                  pc1.addIceCandidate(obj.candidate);
                } else {
                  pc1.ice_queued.push(obj.candidate);
                }
              }
            };

            pc1_offer = offer;

            pc1.onicecandidate = function(obj) {
              if (obj.candidate) {
                if (pc2.didSetRemote) {
                  pc2.addIceCandidate(obj.candidate);
                } else {
                  pc2.ice_queued.push(obj.candidate);
                }
              }
            };

            pc1.setLocalDescription(offer, step1_5, failed);
          }

          function step1_5() {
            setTimeout(step2,0);
          }

          function step2() {
            pc2.setRemoteDescription(pc1_offer, step3, failed);
          }

          function step3() {
            pc2.didSetRemote = true;
            while (pc2.ice_queued.length > 0) {
              pc2.addIceCandidate(pc2.ice_queued.shift());
            }
            pc2.createAnswer(step4, failed);
          }

          function step4(answer) {
            pc2_answer = answer;
            pc2.setLocalDescription(answer, step5, failed);
          }

          function step5() {
            pc1.setRemoteDescription(pc2_answer, step6, failed);
          }

          function step6() {
            pc1.didSetRemote = true;
            while (pc1.ice_queued.length > 0) {
              pc1.addIceCandidate(pc1.ice_queued.shift());
            }
          }

          function start() {
            pc1 = new mozRTCPeerConnection();
            pc1.onaddstream = function(obj) {;};
            pc1.ondatachannel = function(event) {
              var mychannel = event.channel;
              datachannels[num_channels] = mychannel;
              num_channels++;

              mychannel.onmessage = function(evt) {
                log('pc2 said: ' + evt.data,"blue");
              }

              mychannel.onopen = function() {;};
              mychannel.onclose = function() {;};
            }
            pc1.onclosedconnection = function() {;};
            dc1 = pc1.createDataChannel("This is pc1", {});
            dc1.binaryType = "blob";
            dc1.onmessage = function(evt) {
              log('pc2 said: ' + evt.data,"blue");
            }
            dc1.onopen = function() {;};
            dc1.onclose = function() {;};
            pc1.createOffer(step1, failed);
          }

          start();
          setTimeout(function() { sendit(1); }, 500);
        """)


