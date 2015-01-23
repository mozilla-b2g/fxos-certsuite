import ConfigParser
import datetime
import os
import posixpath
import re
import shutil
import tempfile
import time
import traceback

from mozdevice import adb
from mozlog.structured import get_default_logger

here = os.path.split(__file__)[0]


class WaitTimeout(Exception):
    pass


class DeviceBackup(object):
    def __init__(self, backup_dirs=None, backup_files=None):
        self.device = ADBB2G()
        self.logger = self.device._logger

        if backup_dirs is None:
            backup_dirs = ["/data/local",
                            "/data/b2g/mozilla"]
        self.backup_dirs = backup_dirs

        if backup_files is None:
            backup_files = ["/system/etc/hosts"]
        self.backup_files = backup_files

    def local_dir(self, remote):
        return os.path.join(self.backup_path, remote.lstrip("/"))

    def __enter__(self):
        self.backup()
        return self

    def __exit__(self, *args, **kwargs):
        self.cleanup()

    def backup(self):
        self.logger.info("Backing up device")
        self.backup_path = tempfile.mkdtemp()

        for remote_path in self.backup_dirs:
            local_path = self.local_dir(remote_path)
            if not os.path.exists(local_path):
                os.makedirs(local_path)
            self.device.pull(remote_path, local_path)

        for remote_path in self.backup_files:
            remote_dir, filename = remote_path.rsplit("/", 1)
            local_dir = self.local_dir(remote_dir)
            local_path = os.path.join(local_dir, filename)
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            self.device.pull(remote_path, local_path)

        return self

    def restore(self):
        self.logger.info("Restoring device state")
        self.device.remount()

        for remote_path in self.backup_files:
            remote_dir, filename = remote_path.rsplit("/", 1)
            local_path = os.path.join(self.local_dir(remote_dir), filename)
            self.device.rm(remote_path)
            self.device.push(local_path, remote_path)

        for remote_path in self.backup_dirs:
            local_path = self.local_dir(remote_path)
            self.device.rm(remote_path, recursive=True)
            self.device.push(local_path, remote_path)

    def cleanup(self):
        shutil.rmtree(self.backup_path)

class PushFile(object):
    """Context manager that installs a file onto the device, and removes it again"""
    def __init__(self, device, local, remote):
        self.device = device
        self.local = local
        self.remote = remote

    def __enter__(self, *args, **kwargs):
        if self.remote.startswith("/system/"):
            self.device.remount()
        self.device.push(self.local, self.remote)

    def __exit__(self, *args, **kwargs):
        self.device.rm(self.remote)


def poll_wait(func, polling_interval=1.0, timeout=30, after_first=None):
    start_time = time.time()
    ran_first = False

    current_time = time.time()
    while current_time - start_time < timeout:
        value = func()
        if value:
            return value

        if not ran_first and after_first is not None:
            after_first()

        ran_first = True

        sleep = max(current_time + polling_interval - time.time(), 0)
        time.sleep(sleep)
        current_time = time.time()

    raise WaitTimeout()


class ADBB2G(adb.ADBDevice):
    def __init__(self, *args, **kwargs):

        if "wait_polling_interval" in kwargs:
            self._wait_polling_interval = kwargs.pop("wait_polling_interval")
        else:
            self._wait_polling_interval = 1.0

        adb.ADBDevice.__init__(self, *args, **kwargs)

    def wait_for_device_ready(self, timeout=None, wait_polling_interval=None, after_first=None):
        """Wait for the device to become ready for reliable interaction via adb.
        NOTE: if the device is *already* ready this method will timeout.

        :param timeout: Maximum time to wait for the device to become ready
        :param wait_polling_interval: Interval at which to poll for device readiness.
        :param after_first: A function to run after first polling for device
                            readiness. This allows use cases such as stopping b2g
                            setting the unready state, and then restarting b2g.
        """

        if timeout is None:
            timeout = self._timeout
        if wait_polling_interval is None:
            wait_polling_interval = self._wait_polling_interval

        self._logger.info("Waiting for device to become ready")
        profiles = self.get_profiles()
        assert len(profiles) == 1

        profile_dir = profiles.itervalues().next()
        prefs_file = posixpath.normpath(profile_dir + "/prefs.js")

        current_date = int(self.shell_output('date +\"%s\"'))
        set_date = current_date - (365 * 24 * 3600 + 24 * 3600 + 3600 + 60 + 1)

        try:
            self.shell_output("touch -t %i %s" % (set_date, prefs_file))
        except adb.ADBError:
            # See Bug 1092383, the format for the touch command
            # has changed for flame-kk builds.
            set_date = datetime.datetime.fromtimestamp(set_date)
            self.shell_output("touch -t %s %s" %
                              (set_date.strftime('%Y%m%d.%H%M%S'),
                              prefs_file))

        def prefs_modified():
            times = [None, None]

            def inner():
                try:
                    listing = self.shell_output("ls -l %s" % (prefs_file))
                    mode, user, group, size, date, time, name = listing.split(None, 6)
                    mtime = "%s %s" % (date, time)
                except:
                    return False
                if times[0] is None:
                    times[0] = mtime
                else:
                    times[1] = mtime
                    if times[1] != times[0]:
                        return True

                return False

            return inner

        poll_wait(prefs_modified(), timeout=timeout,
                  polling_interval=wait_polling_interval, after_first=after_first)

    def wait_for_net(self, timeout=None, wait_polling_interval=None):
        """Wait for the device to be assigned an IP address.

        :param timeout: Maximum time to wait for an IP address to be defined
        :param wait_polling_interval: Interval at which to poll for ip address.
        """
        if timeout is None:
            timeout = self._timeout
        if wait_polling_interval is None:
            wait_polling_interval = self._wait_polling_interval

        self._logger.info("Waiting for network connection")
        poll_wait(self.get_ip_address, timeout=timeout)

    def stop(self, timeout=None):
        self._logger.info("Stopping b2g process")
        if timeout is None:
            timeout = self._timeout
        self.shell_bool("stop b2g")
        def b2g_stopped():
            processes = set(item[1].split("/")[-1] for item in self.get_process_list())
            return "b2g" not in processes
        poll_wait(b2g_stopped, timeout=timeout)

    def start(self, wait=True, timeout=None, wait_polling_interval=None):
        """Start b2g, waiting for the adb connection to become stable.

        :param wait:
        :param timeout: Maximum time to wait for restart.
        :param wait_polling_interval: Interval at which to poll for device readiness.
        """
        self._logger.info("Starting b2g process")

        if timeout is None:
            timeout = self._timeout

        if wait_polling_interval is None:
            wait_polling_interval = self._wait_polling_interval

        if wait:
            self.wait_for_device_ready(timeout,
                                       after_first=lambda:self.shell_bool("start b2g",
                                                                          timeout=timeout))
        else:
            self.shell_bool("start b2g", timeout=timeout)

    def restart(self, wait=True, timeout=None, wait_polling_interval=None):
        """Restart b2g, waiting for the adb connection to become stable.

        :param timeout: Maximum time to wait for restart.
        :param wait_polling_interval: Interval at which to poll for device readiness.
        """
        self.stop(timeout=timeout)
        self.start(wait, timeout=timeout, wait_polling_interval=wait_polling_interval)

    def reboot(self, timeout=None, wait_polling_interval=None):
        """Reboot the device, waiting for the adb connection to become stable.

        :param timeout: Maximum time to wait for reboot.
        :param wait_polling_interval: Interval at which to poll for device readiness.
        """
        if timeout is None:
            timeout = self._timeout
        if wait_polling_interval is None:
            wait_polling_interval = self._wait_polling_interval

        self._logger.info("Rebooting device")
        self.wait_for_device_ready(timeout,
                                   after_first=lambda:self.command_output(["reboot"]))

    def get_profiles(self, profile_base="/data/b2g/mozilla", timeout=None):
        """Return a list of paths to gecko profiles on the device,

        :param timeout: Timeout of each adb command run
        :param profile_base: Base directory containing the profiles.ini file
        """

        rv = {}

        if timeout is None:
            timeout = self._timeout

        profile_path = posixpath.join(profile_base, "profiles.ini")
        try:
            proc = self.shell("cat %s" % profile_path, timeout=timeout)
            config = ConfigParser.ConfigParser()
            config.readfp(proc.stdout_file)
            for section in config.sections():
                items = dict(config.items(section))
                if "name" in items and "path" in items:
                    path = items["path"]
                    if "isrelative" in items and int(items["isrelative"]):
                        path = posixpath.normpath("%s/%s" % (profile_base, path))
                    rv[items["name"]] = path
        finally:
            proc.stdout_file.close()
            proc.stderr_file.close()

        return rv
