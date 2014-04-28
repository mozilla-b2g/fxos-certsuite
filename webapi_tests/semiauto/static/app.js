// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at http://mozilla.org/MPL/2.0/.

"use strict";

const SERVER_ADDR = window.location.host;

// Shorthand for document.querySelectorAll that returns one element
// for NodeLists of length == 1, or a NodeList.
function $(selector) {
  var els = document.querySelectorAll(String(selector));
  return els.length > 1 ? els : els[0];
};

// Extension of HTMLElement's prototype to allow adding a single CSS
// class to its @class attribute.
HTMLElement.prototype.addClass = function(newClass) {
  var oldClasses = this.className;
  this.className = String(this.className + " " + newClass).trim();
};

// Extension of HTMLElement's prototype to allow removing a single CSS
// class from its @class attribute.
HTMLElement.prototype.removeClass = function(toRemove) {
  var oldClasses = this.className.split(" ");
  var newClasses = "";
  oldClasses.map(function(klass) {
    if (klass == toRemove)
      return;
    newClasses += klass + " ";
  });
  this.className = newClasses.trim();
};

var Keys = (function() {
  function Keys() {
    var arr = [];
    arr.push.apply(arr, arguments);
    arr.__proto__ = Keys.prototype;
    return arr;
  }

  Keys.prototype = new Array;

  // Install keybinding for given key and callback.  When user
  // presses that key, the callback is called.
  Keys.prototype.bind = function(key, cb) {
    for (var entry of this) {
      if (entry.hasOwnProperty(key)) {
        return false;
      }
    }

    var ne = {};
    ne[key] = cb;
    this.push(ne);

    return true;
  };

  // Remove key binding associated with key.  Returns true if
  // the binding is found and removed, false otherwise in which
  // case this function didn't do anything.
  Keys.prototype.unbind = function(key) {
    for (var i = 0; i < this.length; ++i) {
      if (this[i].hasOwnProperty(key)) {
        this.splice(i, 1);
        return true;
      }
    }
    return false; 
  };

  // Run callback function associated with the event's key.
  // Returns true if key binding was found and called, or false
  // if no binding could be found for the key.

  Keys.prototype.triggerEvent = function(ev) {
    return this.trigger(ev.key);
  };

  // Run callback function associated with key.  Returns true if
  // key binding was found and called, or false if no binding
  // could be found for the key.

  Keys.prototype.trigger = function(key) {
    for (var e of this) {
      if (e.hasOwnProperty(key)) {
        e[key]();
        return true;
      }
    }
    return false;
  };

  var instance = new Keys();
  window.onkeypress = function(ev) { instance.triggerEvent(ev); }
  return instance;
})();

// Represents tests in a table in the document.
function TestListView(el, tests) {
  this.el = el;
  this.tests = tests;
}

TestListView.prototype = {
  // have a reusable function if we want a 'Re-run tests' option
  resetTable: function() {
    for (var index in this.tests) {
      var test = this.tests[index];
      var rowNode = this.el.insertRow(-1);
      rowNode.id = "test" + test.id;
      var descriptionNode = rowNode.insertCell(0);
      var resultNode = rowNode.insertCell(1);
      descriptionNode.innerHTML = test.description;
      resultNode.addClass("result");
      resultNode.innerHTML = "";
    }
  },

  setTestState: function(testId, outcome, result) {
    var el = $("#test" + testId);
    el.className = outcome;
    if (result) {
      var resultCell = el.getElementsByClassName("result")[0];
      resultCell.innerHTML = result;
    }
  },

  updateTest: function(data) {
    var testData = data.testData;
    switch (testData.event) {
      case "testStart":
        this.setTestState(testData.id, "running");
        break;
      case "success":
        this.setTestState(testData.id, "pass", "Pass");
        break;
      case "expectedFailure":
        this.setTestState(testData.id, "expected_failure", "Expected Failure");
        break;
      case "skip":
        this.setTestState(testData.id, "skip", testData.reason);
        break;
      case "error":
        this.setTestState(testData.id, "error", testData.error);
        break;
      case "failure":
        this.setTestState(testData.id, "fail", testData.error);
        break;
      case "expectedSuccess":
        this.setTestState(testData.id, "expected_success", "Unexpected Success");
        break;
    }
  }
};

// Represents a dialogue overlay.  Type can either be "prompt",
// "instruct", "confirm".  Message is the question or confirmation to
// pose to the user.
//
// A prompt will show a dialogue with a question, text input, and two
// buttons: "OK" and "Cancel".  An instruction will show a dialogue
// with an instruction, and two buttons: "OK" and "Cancel".  A
// confirmation will show a dialogue with a question, and two buttons:
// "Yes" and "No".
function Dialog(msg, type) {
  this.el = $("#dialog");
  this.textEl = $("#dialog .content");
  this.responseEl = $("#dialog .controls input[type=text]");
  this.okEl = $("#dialog .controls #ok");
  this.cancelEl = $("#dialog .controls #cancel");

  // Mouse event listeners
  this.okEl.onclick = function() { this.onok(); this.close(); }.bind(this);
  this.cancelEl.onclick = function() { this.oncancel(); this.close(); }.bind(this);

  this.message = msg || "";
  this.type = type || "prompt";

  // Assume prompt is default
  switch (this.type) {
  case "instruct":
    this.responseEl.addClass("hidden");
    break;
  case "confirm":
    this.responseEl.addClass("hidden");
    this.okEl.innerHTML = "Yes";
    this.cancelEl.innerHTML = "No";
    break;
  }
}

Dialog.prototype = {
  show: function() {
    this.textEl.innerHTML = this.message;
    this.el.removeClass("hidden");

    switch (this.type) {
    case "instruct":
    case "confirm":
      this.okEl.focus();
      break;
    case "confirm":
    default:
      this.responseEl.focus();
    }

    function skipEl(el, fn) {
      return function() {
        if (document.activeElement === el) {
          return;
        }
        fn();
      }
    }

    Keys.bind("y", skipEl(this.responseEl, this.okEl.onclick));
    Keys.bind("n", skipEl(this.responseEl, this.cancelEl.onclick));
  },

  close: function() {
    Keys.unbind("y");
    Keys.unbind("n");
    this.el.addClass("hidden");
    this.reset();
  },

  value: function() {
    return this.responseEl.value;
  },

  // TODO(ato): Because we're reusing the same Dialog construct, we
  // have to reset it.
  reset: function() {
    this.responseEl.removeClass("hidden");
    this.responseEl.value = "";
    this.okEl.innerHTML = "OK";
    this.cancelEl.innerHTML = "Cancel";
  },

  onok: function() {},
  oncancel: function() {}
};

function Client(addr) {
  this.addr = addr;
  this.ws, this.testList = null;
  this.notificationEl = $("#notification");
}

Client.prototype = {
  // Prompt the user for a response.  Return input to server.
  //
  // This will present the user with an overlay and the ability to
  // enter a text string which will be returned to the server.
  promptUser: function(text) {
    var dialog = new Dialog(text);
    dialog.onok = function() { this.emit("prompt", dialog.value()); }.bind(this);
    dialog.oncancel = function() { this.emit("promptCancel"); }.bind(this);
    dialog.show();
  },

  // Instruct the user perform an action, such as rotating the phone.
  //
  // This will present the user with an ok/cancel dialogue to indicate
  // whether she was successful in carrying out the instruction.
  instructUser: function(text) {
    var dialog = new Dialog(text, "instruct");
    dialog.onok = function() { this.emit("instructPromptOk"); }.bind(this);
    dialog.oncancel = function() { this.emit("instructPromptCancel"); }.bind(this);
    dialog.show();
  },

  // Ask user to confirm a physical aspect about the device or the
  // testing environment that cannot be checked by the test.
  //
  // This will present the user with an ok/cancel dialogue to indicate
  // whether the question posed was true or false.
  confirmPrompt: function(question) {
    var dialog = new Dialog(question, "confirm");
    dialog.onok = function() { this.emit("confirmPromptOk"); }.bind(this);
    dialog.oncancel = function() { this.emit("confirmPromptCancel"); }.bind(this);
    dialog.show();
  },

  connect: function() {
    this.ws = new WebSocket("ws://" + this.addr + "/tests");

    this.ws.onopen = function(e) { console.log("open", e); }.bind(this);
    this.ws.onclose = function(e) { console.log("close", e); }.bind(this);

    this.ws.onmessage = function(e) {
      var data = JSON.parse(e.data);
      var command = Object.keys(data)[0];
      console.log("recv", data);

      switch (command) {
      case "testList":
        // set up the test_list table
        this.testList = new TestListView($("#test_list"), data.testList);
        this.testList.resetTable();
        break;

      case "testRunStart":
        this.notificationEl.innerHTML = "Running tests…";
        break;

      case "testRunStop":
        this.notificationEl.innerHTML = "Done!";
        break;

      case "prompt":
        this.promptUser(data.prompt);
        break;

      case "instructPrompt":
        this.instructUser(data.instructPrompt);
        break;

      case "confirmPrompt":
        this.confirmPrompt(data.confirmPrompt);
        break;

      case "updateTest":
        // TODO: this assumes any other request will be to update the table
        this.testList.updateTest(data.updateTest);
        break;

      default:
        console.log("unkwn", data);
        this.ws.close();
        this.notificationEl.innerHTML = "Received unknown command from server )-:";
        break;
      }
    }.bind(this);
  },

  emit: function(event, data) {
    var command = {};
    command[event] = data || null;
    var payload = JSON.stringify(command);
    console.log("send", command);
    this.ws.send(payload);
  }
};

function App(server) {
  this.addr = server;
  this.client = new Client(this.addr);
}

App.prototype = {
  start: function() {
    this.client.connect();
  }
};

function init() {
  var app = new App(SERVER_ADDR);
  app.start();
}

document.addEventListener("DOMContentLoaded", init, false);
