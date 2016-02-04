import os

class MCTSApps():

    def __init__(self, marionette):
        self.marionette = marionette
        js = os.path.abspath(os.path.join(__file__, os.path.pardir, "mcts_apps.js"))
        self.marionette.import_script(js)

    def getManifestURL(self, name, switch_to_frame=True, url=None, launch_timeout=None):
        self.marionette.switch_to_frame()
        result = self.marionette.execute_async_script("MCTSApps.getMCTSManifestURL('" + name + "')", script_timeout=launch_timeout)
        return result
