# -*- encoding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import mozdevice
import marionette

# getter for shared logger instance
from mozlog.structured import get_default_logger

from certsuite.harness import check_adb
from certsuite.harness import MarionetteSession
from certsuite.cert import run_marionette_script

# https://gist.github.com/mozkeeler/3531c27239d92bc1535c
# https://developer.mozilla.org/en-US/docs/Mozilla/QA/Marionette/Marionette_JavaScript_Tests
#https://developer.mozilla.org/en-US/Firefox_OS/Automated_testing/XPCShell
#https://developer.mozilla.org/en-US/Firefox_OS/Automated_testing


#######################################################################################################################
# shared module functions
#########################


class certdump(object):
    @staticmethod
    def js_test():
        return '''
            return Components;
        '''

    @staticmethod
    def js_nssversions():
        return '''
            const { 'classes': Cc, 'interfaces': Ci } = Components;

            let nssversion = Cc[ "@mozilla.org/security/nssversion;1" ].getService(Ci.nsINSSVersion);
            return {
                'NSS_Version': nssversion.NSS_Version,
                'NSSUTIL_Version': nssversion.NSSUTIL_Version,
                'NSSSSL_Version': nssversion.NSSSSL_Version,
                'NSPR_Version': nssversion.NSPR_Version,
                'NSSSMIME_Version': nssversion.NSSSMIME_Version
            };
        '''

    @staticmethod
    def js_certdump():
        return '''
            const { 'classes': Cc, 'interfaces': Ci } = Components;

            let certdb = Cc[ "@mozilla.org/security/x509certdb;1" ].getService(Ci.nsIX509CertDB);
            if ("nsIX509CertDB2" in Ci) certdb.QueryInterface(Ci.nsIX509CertDB2); // for FxOS < 2.1
            let certs = certdb.getCerts();
            let enumerator = certs.getEnumerator();
            let certlist = [];
            while (enumerator.hasMoreElements()) {
                let cert = enumerator.getNext().QueryInterface(Ci.nsIX509Cert);
                let sslTrust = certdb.isCertTrusted(cert, Ci.nsIX509Cert.CA_CERT, Ci.nsIX509CertDB.TRUSTED_SSL);
                let emailTrust = certdb.isCertTrusted(cert, Ci.nsIX509Cert.CA_CERT, Ci.nsIX509CertDB.TRUSTED_EMAIL);
                let objsignTrust = certdb.isCertTrusted(cert, Ci.nsIX509Cert.CA_CERT, Ci.nsIX509CertDB.TRUSTED_OBJSIGN);
                let certinfo = {
                    'cert': cert,
                    'sslTrust': sslTrust,
                    'emailTrust': emailTrust,
                    'objsignTrust': objsignTrust
                };
                certlist.push(certinfo);
            }
            return certlist;
        '''


    def __init__(self):
        self.logger = get_default_logger()
        try:
            self.dm = mozdevice.DeviceManagerADB(runAdbAsRoot=True)
        except mozdevice.DMError as e:
            self.logger.error("Error connecting to device via adb (error: %s). Please be " \
                              "sure device is connected and 'remote debugging' is enabled." % \
                              e.msg)
            raise
        self.logger.debug("Attempting to set up port forwarding for marionette")


    def get_via_marionette(self):
        self.dm.forward("tcp:2828", "tcp:2828")
        return run_marionette_script(certdump.js_certdump(), chrome=True)


    def nssversion_via_marionette(self):
        self.dm.forward("tcp:2828", "tcp:2828")
        return run_marionette_script(certdump.js_nssversions(), chrome=True)


#######################################################################################################################
# Test implementations
################################

# derived from shared test class
from suite import ExtraTest


#######################################################################################################################
# ssl.certdb_info

class certdb_info(ExtraTest):
    """
    Test that dumps CertDB from device and logs certificates for info.
    """

    group = "ssl"
    module = sys.modules[__name__]

    @classmethod
    def run(cls, version=None):
        logger = get_default_logger()

        try:
            dumper = certdump()
            certs = dumper.get_via_marionette()
        except:
            cls.log_status('FAIL', 'Failed to gather information from the device via Marionette.')
            return False

        # TODO: just listing all of the certs, no filtering
        certlist = [x['cert'][u'subjectName'] for x in certs]
        cls.log_status('PASS', 'SSL certificates on device:\n%s' % '\n'.join(certlist))
        return True


#######################################################################################################################
# ssl.nssversion_info

class nssversion_info(ExtraTest):
    """
    Test that logs nss component versions from device.
    """

    group = "ssl"
    module = sys.modules[__name__]

    @classmethod
    def run(cls, version=None):
        logger = get_default_logger()

        try:
            dumper = certdump()
            versions = dumper.nssversion_via_marionette()
        except:
            cls.log_status('FAIL', 'Failed to gather information from the device via Marionette.')
            return False

        cls.log_status('PASS', 'NSS component versions detected:\n%s' % '\n'.join(
            ["%s: %s" % (k, versions[k]) for k in versions]))
        return True
