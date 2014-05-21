from semiauto import TestCase
from datetime import datetime
import time

class TestTime(TestCase):

    def test_time_set(self):
           get_current_time = """
              var curDate  = new Date();
              var time_msec = curDate.getTime();
              return time_msec;
           """
           set_time = """
              var date_n_time_string = arguments[0];
              var datetime_to_set = new Date(date_n_time_string);
              var time_interface = window.navigator.mozTime;

              //set the time using timer webAPI
              time_interface.set(datetime_to_set);
              //get the newly set time
              var get_new_time = new Date();
              return get_new_time.getTime();
           """
           #get current time from system
	   self.instruct("Ensure the phone is unlocked.")
	   current_time_msec = self.marionette.execute_script(get_current_time)
           str_current_time = time.strftime('%Y-%m-%d %H:%M',time.localtime(current_time_msec/1000.0))
	   self.confirm("open clock/calender app and confirm if %s is current date and time on phone?" %str_current_time)

           #get the new date and time from user and pass to script to set
           str_date = self.prompt("Please enter a date to be changed in format dd/mm/yyyy")
           if str_date is None:
               self.fail("Must enter a date")

           str_time = self.prompt("Please enter a time to be changed in format HH:MM:SS")
           date_struct = datetime.strptime(str_date,'%d/%m/%Y')
           date_format = date_struct.strftime('%B %d, %Y')
           date_n_time = date_format +' '+ str_time

	   mytime = self.marionette.execute_script(set_time, script_args=[date_n_time])
           self.confirm("re-open clock/calender app and confirm the set date and time")
