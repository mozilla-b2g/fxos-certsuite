from pytz import reference
from datetime import datetime
import time

from webapi_tests.semiauto import TestCase


class TestTime(TestCase):
    """
    This is a test for the `MozTime API`_ which will:
    - Get the current date/time and ask the test user to verify
    - Set the current date/time to a user-specified value, and ask the test user verify
    .. _`MozTime API`: https://developer.mozilla.org/en-US/docs/Web/API/Time_and_Clock_API
    """

    def setUp(self):
        super(TestTime, self).setUp()
        self.wait_for_obj("window.navigator.mozTime")

    def test_time_set(self):
        get_current_time = """
            var curDate  = new Date();
            var time_msec = curDate.getTime();
            return time_msec;
        """
        set_time = """
            var sec = arguments[0];
            var datetime_to_set = new Date(1970,0,1);
            datetime_to_set.setSeconds(sec);
            console.log("printing the set time",sec);
            var time_interface = window.navigator.mozTime;
            //set the time using timer webAPI
            time_interface.set(datetime_to_set);
        """
        get_time = """
            //get the newly set time
            var get_new_time = new Date();
            return get_new_time.getTime() - get_new_time.getTimezoneOffset()*60*1000;
        """

        #get current time from system
        current_time_msec = self.marionette.execute_script(get_current_time)
        str_current_time = time.strftime('%Y-%m-%d %H:%M', \
                                   time.gmtime(current_time_msec / 1000.0))
        str_current_time_zone = reference.LocalTimezone().tzname(datetime.now())
        str_current_local_time = time.strftime('%Y-%m-%d %H:%M', \
                                   time.localtime(current_time_msec / 1000.0))
        self.confirm("Pull the notification bar and confirm if %s (UTC time)" \
                     " or %s (%s time) is current date and time on phone?" \
                     % (str_current_time, str_current_local_time, str_current_time_zone))

        #get the new date and time from user and pass to script to set
        d = time.mktime(time.strptime("November 11, 2011 11:12", '%B %d, %Y %H:%M'))

        self.marionette.execute_script(set_time, script_args=[d])
        time.sleep(5)
        mozset_time = self.marionette.execute_script(get_time)

        #compare the times (must be the same in minutes level)
        self.assertEqual(d/60, mozset_time/1000/60)
