from marionette import MarionetteTestCase

class MinimalTestCase(MarionetteTestCase):
    def __init__(self, *args, **kwargs):
        super(MinimalTestCase, self).__init__(*args, **kwargs)

    def instruct(self, message):
        response = None
        try:
            response = raw_input("\n=== INSTRUCTION ===\n%s\nWere you successful? [y/n]\n" % message)
            while response not in ['y', 'n']:
                response = raw_input("Please enter 'y' or 'n': " % message)
        except KeyboardInterrupt:
            self.fail("Test interrupted by user")
        if response == 'n':
            self.fail("Failed on step: %s" % message)
