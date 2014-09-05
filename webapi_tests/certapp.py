# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import fxos_appgen

from marionette import MarionetteException


__all__ = ["name", "canonical_name", "frame_name",
           "install", "is_installed", "launch", "activate", "kill"]


name = "CertTest App"
canonical_name = name.lower().replace(" ", "-")
frame_name = "certtest"
timeout = 5 * 1000  # ms


class LaunchError(Exception):
    pass


class SwitchError(Exception):
    pass


class CloseError(Exception):
    pass


def install(marionette=None, version='1.3'):
    """Installs the app on the attached device.  Raises if app is
    already installed, but a guard can be added using ``is_installed``.

    This function can optionally reuse an existing Marionette session.

    """

    # fxos_appgen will create a new Marionette instance if unspecified
    fxos_appgen.generate_app(name,
                             install=True,
                             version=version,
                             all_perm=True,
                             marionette=marionette)


def is_installed():
    return fxos_appgen.is_installed(name)


def switch_to_app_management(marionette):
    # App management is done in system app
    marionette.switch_to_frame()
    # TODO(mdas): Replace this with pkg_resources if we know that we'll be
    # installing this as a package
    marionette.import_script(
        os.path.join(os.path.split(__file__)[0], "app_management.js"))


def launch(marionette):
    """Launches and activates app.  A reference to the app will be
    returned.

    """

    marionette.set_context(marionette.CONTEXT_CONTENT)
    switch_to_app_management(marionette)

    # If the app is already launched this doesn't launch a new app, but
    # returns a reference to existing app.
    app = marionette.execute_async_script(
        "GaiaApps.launchWithName('%s')" % name, script_timeout=timeout)
    if app is None:
        raise LaunchError("Unable to launch app: %s" % name)
    activate(marionette, app=app)
    return app


def activate(marionette, app=None):
    """Switches to the app's frame, or raises ``ActivateError`` if
    unable to find app's frame.

    """

    exc = None

    if app is not None:
        try:
            marionette.switch_to_frame(app["frame"])
        except MarionetteException as e:
            exc = "Unable to activate app: %s: %s" % (name, e)
    else:
        iframes = marionette.execute_script(
            "return document.getElementsByTagName('iframe').length")
        for i in range(iframes):
            marionette.switch_to_frame(i)
            if frame_name in marionette.get_url():
                return
        exc = "App frame not found: %s" % frame_name

    if exc is not None:
        raise ActivateError("Unable to activate app: %s: %s" % (name, exc))


def kill(marionette, app=None):
    """Forcefully closes app by reference through `app` keyword
    argument, or by canonical name if unspecified.

    """

    origin = "app://%s" % canonical_name
    if app is not None:
        origin = app["origin"]

    try:
        switch_to_app_management(marionette)
        marionette.execute_async_script(
            "GaiaApps.kill('%s')" % origin, script_timeout=timeout)
    except MarionetteException as e:
        raise CloseError("Unable to close app: %s" % e)
    except Exception as e:
        raise CloseError("Unexpected exception: %s" % e)
