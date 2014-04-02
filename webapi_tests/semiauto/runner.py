# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import unittest


# TODO(ato): Come up with a better name for this
class PreInstantiatedTestRunner(unittest.runner.TextTestRunner):
    """Allows the `resultclass` argument to be an already instantiated
    ``unittest.results.TestResult`` implementation.

    The sole purpose of this class is to not make unittest terrible,
    and adds no extra value to our code.  Feel free to ignore it.

    """

    def __init__(self, *args, **kwargs):
        super(PreInstantiatedTestRunner, self).__init__(*args, **kwargs)

    def _makeResult(self):
        return self.resultclass


class TestEventDelegator(unittest.runner.TextTestResult):
    """Replacement class for ``unittest.runner.TextTestResult`` which
    allows attaching callback classes for state changes to tests.

    This class injects a callback delegator preserving the behaviour
    of ``unittest.results.TestResult``, meaning the shell output
    streamer is preserved.  Using ``add_callback(cb)`` on this class
    one can add additional hooks to test runner events by implementing
    the ``TestEvents`` callback interface.

    This class exists because unittest doesn't allow you to add
    arbitrary hooks.  This class makes the interface between semiauto
    and unittest slightly easier to use.

    """

    def __init__(self, *args, **kwargs):
        super(TestEventDelegator, self).__init__(*args, **kwargs)
        self.cbs = []

    def add_callback(self, cb):
        if not isinstance(cb, TestEvents):
            cb = cb()

        self.cbs.append(cb)

    def startTestRun(self):
        super(TestEventDelegator, self).startTestRun()
        for cb in self.cbs:
            cb.on_test_run_start()

    def startTest(self, test):
        super(TestEventDelegator, self).startTest(test)
        for cb in self.cbs:
            cb.on_test_start(test)

    def addSuccess(self, test):
        super(TestEventDelegator, self).addSuccess(test)
        for cb in self.cbs:
            cb.on_success(test)

    def addError(self, test, err):
        super(TestEventDelegator, self).addError(test, err)
        for cb in self.cbs:
            cb.on_error(test, err)

    def addFailure(self, test, err):
        super(TestEventDelegator, self).addFailure(test, err)
        for cb in self.cbs:
            cb.on_failure(test, err)

    def addSkip(self, test, reason):
        super(TestEventDelegator, self).addSkip(test, reason)
        for cb in self.cbs:
            cb.on_skip(test, reason)

    def addExpectedFailure(self, test, err):
        super(TestEventDelegator, self).addExpectedFailure(test, err)
        for cb in self.cbs:
            cb.on_expected_failure(test, err)

    def addUnexpectedSuccess(self, test):
        super(TestEventDelegator, self).addUnexpectedSuccess(test)
        for cb in self.cbs:
            cb.on_unexpected_success(test)

    def stopTest(self, test):
        super(TestEventDelegator, self).stopTest(test)
        for cb in self.cbs:
            cb.on_test_stop(test)

    def stopTestRun(self):
        super(TestEventDelegator, self).stopTestRun()
        for cb in self.cbs:
            cb.on_test_run_stop()


class TestEvents(object):
    """A set of hooks triggered as a test state gets updated.

    The hooks are called immediately after the relevant
    ``unittest.runner.TextTestResult`` actions have been performed.

    Since this is an abstract base class you can voluntarily implement
    all or just a subset of these methods in your implementation.
    This allows hooks to only listen for one or more specific events.

    """

    def on_test_run_start(self):
        pass

    def on_test_start(self, test):
        pass

    def on_success(self, test):
        pass

    def on_error(self, test):
        pass

    def on_failure(self, test, err):
        pass

    def on_skip(self, test, reason):
        pass

    def on_expected_failure(self, test, err):
        pass

    def on_unexpected_success(self, test):
        pass

    def on_test_stop(self, test):
        pass

    def on_test_run_stop(self):
        pass


class TestStateUpdater(TestEvents):
    """A test result event class that can update the host browser on the
    progress of running tests.

    Meant to be used as a callback for ``TestEventDelegator``.

    """

    def __init__(self, handler):
        """Construct a new test state updater.

        :param handler: Handler for current host browser connection,
            which should be an instance of ``server.TestHandler``.

        """

        self.client = handler

    # TODO(ato): This can be improved:
    def send_event(self, event, test=None, **kwargs):
        """Send event to the currently connected client.

        If a test specified a weak reference to it will be used
        (`hash(test)`).  Additional key-values can be given as keyword
        arguments.

        Because a canonical list of tests is already in the browser's
        cache it will use the test reference as a key to look up the
        test's which state to change.

        Some sample JSON objects emitted from this could be::

            {"testRunStart"}
            {"testStart": {"id": 12345678}}
            {"skip"}

        :param event: The event command to send to the client.

        :param test: Optional test to include as context.

        :param kwargs: Optional additional arguments to be included.
            These must be serializable by `json`.

        """

        if not self.client.connected:
            return

        payload = kwargs

        # TODO(ato): Serialization of socket.error, etc.
        if test:
            payload["id"] = hash(test)
            if "error" in payload:
                payload["error"] = str(payload["error"])
            payload["event"] = event
            self.client.emit("updateTest", {"testData": payload})
        else:
            self.client.emit(event, payload if payload else None)

    def on_test_run_start(self):
        self.send_event("testRunStart")

    def on_test_start(self, test):
        self.send_event("testStart", test)

    def on_success(self, test):
        self.send_event("success", test)

    def on_error(self, test, err):
        self.send_event("error", test, error=err)

    def on_failure(self, test, err):
        self.send_event("failure", test, error=err)

    def on_skip(self, test, reason):
        self.send_event("skip", test, reason=reason)

    def on_expected_failure(self, test, err):
        self.send_event("expectedFailure", test, error=err)

    def on_unexpected_success(self, test):
        self.send_event("unexpectedSuccess", test)

    def on_test_stop(self, test):
        self.send_event("testStop", test)

    def on_test_run_stop(self):
        self.send_event("testRunStop")


def serialize_suite(tests, ov=[]):
    """Serialize a ``unittest.TestSuite`` instance for transportation
    across the wire.

    Tests are represented by their hash as we have no desire to
    replicate the full Test instance object on the client side.

    :param tests: Instance of ``unittest.suite.TestSuite`` to be
        serialized.

    :returns: List of test dicts represented by `id` and
        `description`.

    """

    rv = ov
    if isinstance(tests, collections.Iterable):
        # [TestCase, ...] or [<TestSuite ...>, <TestSuite ...>]
        for test in tests:
            if isinstance(test, unittest.suite.TestSuite):
                rv = serialize_suite(test, rv)
            else:
                rv.append({"id": hash(test), "description": str(test)})
    elif hasattr(tests, "_tests"):
        # <unittest.suite.TestSuite _tests=[...]>
        rv = serialize_suite(tests._tests, rv)

    return rv
