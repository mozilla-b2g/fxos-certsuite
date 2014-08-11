# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import re

class UserAgentTestCommon(object):

    def get_user_agent(self):
        ret_user_agent = self.marionette.execute_script("return navigator.userAgent")
        return ret_user_agent

    def check_user_agent_is_valid(self, user_agent_string):
        valid = True

        ua_rexp = re.compile("Mozilla/(\d+\.\d+) \((Mobile|Tablet)(;.*)?; rv:(\d+\.\d+)\) Gecko/(\d+\.\d+) Firefox/(\d+\.\d+)")
        m = ua_rexp.match(user_agent_string)
        message = ""

        if m is None or len(m.groups()) != 6:
            # no match
            valid = False
            message = 'Did not match regular expression'
        elif m.groups()[2] != None:
            # Specified a device string, strip leading ';' and any leading/trailing whitespace
            device = m.groups()[2][1:].strip()
            # Do not use slash ("/"), semicolon (";"), round brackets or any whitespace.
            device_rexp = re.compile('[/;\(\)\s]')
            m = device_rexp.search(device)
            if m:
                valid = False
                message = 'Device identifier: "%s" contains forbidden characters' % device

        return valid, message
