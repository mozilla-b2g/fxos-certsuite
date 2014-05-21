from semiauto import TestCase


class PowerManagement(TestCase):
    def test_brightness_basic(self):

        maximum_brightness = """
        var mm = window.navigator.mozPower;
        if(mm.screenEnabled)
               mm.screenBrightness = 1.0;
        """
        self.marionette.execute_script(maximum_brightness)
        self.confirm("Screen-brightness test:\
                      Ensure that the screen is enabled")

        self.instruct("The brightness will get reduced now ")
        decrease_brightness = """
        var mm = window.navigator.mozPower;
        if(mm.screenEnabled)
               mm.screenBrightness = 0.1;
        """
        self.marionette.execute_script(decrease_brightness)
        self.confirm("Did you notice decrease in brightness? ")

        self.instruct("The brightness will get increased now ")
        increase_brightness = """
        var mm = window.navigator.mozPower;
        if(mm.screenEnabled)
               mm.screenBrightness = 1.0;
        """
        self.marionette.execute_script(increase_brightness)
        self.confirm("Did you notice increase in brightness? ")

    def test_lock_background(self):
        self.instruct("Power management properties test:\
                       Run any app (ex: play music) and lock the screen.\
                       i.e lock-background state")
        script = """
        var mm = window.navigator.mozPower;
        var flag
        if((!mm.cpuSleepAllowed) && (!mm.screenEnabled) ){
           flag = true;
        }
        else{
           flag = false;
        }
        return flag;
        """
        result = self.marionette.execute_script(script)
        self.assertTrue(result)
        self.instruct("Successfully tested powermanagement properties\
                       in lock-background state")

    def test_lock_foreground(self):
        self.instruct("Power management properties test:\
                       Run any app (ex:play music) and keep it in foreground.\
                       i.e lock-foreground state")
        script = """
        var mm = window.navigator.mozPower;
        var flag
        if((!mm.cpuSleepAllowed) && (mm.screenEnabled) ){
           flag = true;
           }
        else{
           flag = false;
           }
        return flag;
        """
        result = self.marionette.execute_script(script)
        self.assertTrue(result)
        self.instruct("Successfully tested powermanagement properties\
                       in lock-foreground state")

    def test_unlock(self):
        self.instruct("Power management properties test:\
                       Ensure no app is running (except cert app) and lock  .\
                       the screen i.e Phone is in idle state")
        script = """
        var mm = window.navigator.mozPower;
        var flag
        if((mm.cpuSleepAllowed) && (!mm.screenEnabled) ){
           flag = true;
           }
        else{
           flag = false;
           }
        return flag;
        """
        result = self.marionette.execute_script(script)
        self.assertTrue(result)
        self.instruct("Successfully tested powermanagement properties\
                       in idle state")
