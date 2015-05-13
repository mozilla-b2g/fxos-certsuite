# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import sys
import time
import traceback

DEFAULT_TIMEOUT = 120
DEFAULT_INTERVAL = 0.1

class Wait(object):
    """An explicit conditional utility class for waiting until a condition
    evalutes to true or not null.

    This will repeatedly evaluate a condition in anticipation for a
    truthy return value, or its timeout to expire, or its waiting
    predicate to become true.

    A ``Wait`` instance defines the maximum amount of time to wait for
    a condition, as well as the frequency with which to check the
    condition.  Furthermore, the user may configure the wait to ignore
    specific types of exceptions whilst waiting.

    """

    def __init__(self, timeout=DEFAULT_TIMEOUT,
                 interval=DEFAULT_INTERVAL, ignored_exceptions=None,
                 clock=None):
        """Configure the instance to have a custom timeout, interval, and a
        list of ignored exceptions.

        Optionally a different time implementation than the one
        provided by the standard library (time, through
        ``SystemClock``) can also be provided.

        Sample usage::

            # Wait 30 seconds for condition to return "foo", checking
            # it every 5 seconds.
            wait = Wait(timeout=30, interval=5)
            foo = wait.until(lambda: return get_foo())

        :param timeout: How long to wait for the evaluated condition
            to become true.  The default timeout is
            `wait.DEFAULT_TIMEOUT`.

        :param interval: How often the condition should be evaluated.
            In reality the interval may be greater as the cost of
            evaluating the condition function is not factored in.  The
            default polling interval is `wait.DEFAULT_INTERVAL`.

        :param ignored_exceptions: Ignore specific types of exceptions
            whilst waiting for the condition.  Any exceptions not
            whitelisted will be allowed to propagate, terminating the
            wait.

        :param clock: Allows overriding the use of the runtime's
            default time library.  See ``wait.SystemClock`` for
            implementation details.

        """

        self.timeout = timeout
        self.interval = interval
        self.clock = clock or SystemClock()
        self.end = self.clock.now + self.timeout

        exceptions = []
        if ignored_exceptions is not None:
            if isinstance(ignored_exceptions, collections.Iterable):
                exceptions.extend(iter(ignored_exceptions))
            else:
                exceptions.append(ignored_exceptions)
        self.exceptions = tuple(set(exceptions))

    def until(self, condition, is_true=None, message=""):
        """Repeatedly runs condition until its return value evalutes to true,
        or its timeout expires or the predicate evaluates to true.

        This will poll at the given interval until the given timeout
        is reached, or the predicate or conditions returns true.  A
        condition that returns null or does not evaluate to true will
        fully elapse its timeout before raising a
        ``TimeoutException``.

        If an exception is raised in the condition function and it's
        not ignored, this function will raise immediately.  If the
        exception is ignored, it will continue polling for the
        condition until it returns successfully or a
        ``TimeoutException`` is raised.

        The return value of the callable `condition` will be returned
        once it completes successfully.

        :param condition: A callable function whose return value will
            be returned by this function if it evalutes to true.

        :param is_true: An optional predicate that will terminate and
            return when it evalutes to False.  It should be a function
            that will be passed `clock` and an end time.  The default
            predicate will terminate a wait when the clock elapses the
            timeout.

        :param message: An optional message to include in the
            exception's message if this function times out.

        :returns: Return value of `condition`.

        """

        rv = None
        last_exc = None
        until = is_true or until_pred
        start = self.clock.now

        while not until(self.clock, self.end):
            try:
                rv = condition()
            except (KeyboardInterrupt, SystemExit) as e:
                raise e
            except self.exceptions as e:
                last_exc = sys.exc_info()

            if isinstance(rv, bool) and not rv:
                time.sleep(self.interval)
                continue

            if rv is not None:
                return rv

            self.clock.sleep(self.interval)

        if message:
            message = " with message: %s" % message

        raise TimeoutException(
            "Timed out after %s seconds%s" %
            ((self.clock.now - start), message), cause=last_exc)

def until_pred(clock, end):
    return clock.now >= end

class SystemClock(object):
    def __init__(self):
        self._time = time

    def sleep(self, duration):
        self._time.sleep(duration)

    @property
    def now(self):
        return self._time.time()

class TimeoutException(Exception):
    def __init__(self, message="", cause=None):
        self.msg = message
        self.cause = cause

    def __str__(self):
        msg = str(self.msg)
        tb = None

        if self.cause:
            msg += ", caused by %r" % self.cause[0]
            tb = self.cause[2]

        return "".join(traceback.format_exception(self.__class__, msg, tb))
