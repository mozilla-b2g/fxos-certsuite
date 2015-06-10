# -*- encoding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import mozdevice
import marionette

# getter for shared logger instance
from mozlog.structured import get_default_logger

from mcts.certsuite.cert import run_marionette_script
from mcts.utils.device.devicehelper import DeviceHelper

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


    def get_via_marionette(self):
        return run_marionette_script(certdump.js_certdump(),
                                     chrome=True)


    def nssversion_via_marionette(self):
        return run_marionette_script(certdump.js_nssversions(),
                                     chrome=True)


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
# ssl.nssversion

class nssversion(ExtraTest):
    """
    Test that logs nss component versions from device.
    """

    group = "ssl"
    module = sys.modules[__name__]

    # TODO: This list's tail must be maintained regularly.
    b2g_version_to_hginfo = {
        '1.2': {
            'hgtag': 'mozilla-b2g26_v1_2',
            'release_date:': '2013-12-09',
            'release_branch': 'RELEASE_BASE_20131202',
            'release_nss_version': 'NSS_3_15_3_RTM'
        },
        '1.3': {
            'hgtag': 'mozilla-b2g28_v1_3',
            'release_date:': '2014-04-17',
            'release_branch': 'B2G_1_3_20140317_MERGEDAY',
            'release_nss_version': 'NSS_3_15_5_RTM'
        },
        '1.3t': {
            'hgtag': 'mozilla-b2g28_v1_3t',
            'release_date:': '2014-04-17',
            'release_branch': 'B2G_1_3T_20140317_MERGEDAY',
            'release_nss_version': 'NSS_3_15_5_RTM'
        },
        '1.4': {
            'hgtag': 'mozilla-b2g30_v1_4',
            'release_date:': '2014-06-09',
            'release_branch': 'B2G_1_4_20140609_MERGEDAY',
            'release_nss_version': 'NSS_3_16_RTM'
        },
        '2.0': {
            'hgtag': 'mozilla-b2g32_v2_0',
            'release_date:': '2014-09-01',
            'release_branch': 'B2G_2_0_20140902_MERGEDAY',
            'release_nss_version': 'NSS_3_16_4_RTM'
        },
        '2.0m': {
            'hgtag': 'mozilla-b2g32_v2_0m',
            'release_date:': '2014-09-01',
            'release_branch': 'B2G_2_0_20140902_MERGEDAY',
            'release_nss_version': 'NSS_3_16_4_RTM'
        },
        '2.1': {
            'hgtag': 'mozilla-b2g34_v2_1',
            'release_date:': '2014-11-21',
            'release_branch': 'FIREFOX_RELEASE_34_BASE',
            'release_nss_version': 'NSS_3_17_2_RTM'
        },
        '2.1s': {
            'hgtag': 'mozilla-b2g34_v2_1s',
            'release_date:': '2014-11-21',
            'release_branch': 'FIREFOX_RELEASE_34_BASE',
            'release_nss_version': 'NSS_3_17_2_RTM'
        },
        '2.2': {
            'hgtag': 'mozilla-b2g37_v2_2',
            'release_date:': '2015-06-08',
            'release_branch': 'B2G_2_2_20150511_MERGEDAY',  # TODO: update on release
            'release_nss_version': 'NSS_3_17_4_RTM'         # TODO: update on release
        }
    }

    @staticmethod
    def to_ints(version):
        """
        Turn version string into a numeric representation for easy comparison.
        Undeclared point versions are assumed to be 0.
        :param version: a NSS version string
        :return: array of [major, minor, point, pointpoint, tag value]
        """

        # Example strings: "NSS_3_7_9_RTM", "NSS_3_6_BRANCH_20021026", "NSS_3_6_BETA2",
        #                  "3.18 Basic ECC Beta", "3.16.5 Basic ECC"

        # normalize version strings
        norm_version = version.replace('NSS_', '').replace('.', '_').replace(' ', '_').upper().split('_')

        # Asserting minimumum length of 3 as in [major,minor,tag]
        assert len(norm_version) >= 3

        # Asserting the first two fields are numeric major and minor
        assert norm_version[0].isdigit() and norm_version[1].isdigit()

        # Asserting last field is always a non-numeric tag or a date tag
        # CAVE: fails with obscure date dags like certdata.txt-NSS_3_4_20020403_2
        assert not norm_version[-1].isdigit() or len(norm_version[-1]) > 2

        # fill in missing point and pointpoint versions
        if not (norm_version[2].isdigit() and len(norm_version[2]) < 4):  # <4 to distinguish from numeric date tags
            norm_version.insert(2, "0")
        if not (norm_version[3].isdigit() and len(norm_version[3]) < 4):
            norm_version.insert(3, "0")

        # Strictly ordering by RTM > RC > BETA > *
        # CAVE: Order rule may result in bogus sorting of obscure tags (WITH_CBKI*, TPATCH*, BRANCHPOINT*, ...)
        # Recent versions are tagged non-obscurely and consistently

        tag_value = 0
        for v in norm_version[4:]:
            if v.startswith('BETA'):
                tag_value = 100
                if len(v[4:]) == 1 or len(v[4:]) == 2:
                    try:
                        tag_value += int(v[4:])
                    except ValueError:
                        pass
        for v in norm_version[4:]:
            if v.startswith('RC'):
                tag_value = 200
                if len(v[3:]) == 1 or len(v[3:]) == 2:
                    try:
                        tag_value += int(v[3:])
                    except ValueError:
                        pass
        for v in norm_version[4:]:
            if v == 'RTM':
                tag_value = 300

        # Special case: "x.y.z Basic ECC" is counted as RTM
        # TODO: research the set of potential version string formats reported by libnss.
        if norm_version[-2] == 'BASIC' and norm_version[-1] == 'ECC' and norm_version[-3].isdigit():
            tag_value = 300

        major, minor, point, pointpoint = (int(x) for x in norm_version[:4])

        return [major, minor, point, pointpoint, tag_value]

    @staticmethod
    def first_older_than_second(version_a, version_b):
        """
        Tests for the NSS version string in the first parameter being less
        recent than the second (a < b). Tag order is RTM > RC > BETA > *.
        Works with hg tags like "NSS_3_7_9_RTM" and version strings reported by
        nsINSSVersion, like "3.18 Basic ECC Beta" (mixed, too).
        :param version_a: a NSS version string
        :param version_b: another NSS version string
        :return: bool (a < b)
        """

        a = nssversion.to_ints(version_a)
        b = nssversion.to_ints(version_b)

        # must be of equal length
        assert len(a) == len(b)

        # Compare each version component, bail out on difference
        for i in xrange(len(a)):
            if b[i] < a[i]:
                return False
            if b[i] > a[i]:
                return True
        return False

    @staticmethod
    def most_recent_among(versions):
        """
        Compare a list of NSS versions and return the latest one.
        Uses first_older_than_second() for comparison.
        :param versions: an array of NSS version strings
        :return: verbatim copy of the most recent version string
        """
        latest = versions[0]
        for v in versions[1:]:
            if nssversion.first_older_than_second(latest, v):
                latest = v
        return latest

    @classmethod
    def run(cls, version=None):
        """
        Test runner method; is called by parent class defined in suite.py.
        :param version: B2G version string to test against
        :return: bool PASS/FAIL status
        """

        try:
            dumper = certdump()
            versions = dumper.nssversion_via_marionette()
        except:  # TODO: too broad exception. Log reason for failure.
            cls.log_status('FAIL', 'Failed to gather information from the device via Marionette.')
            return False

        if version is None:
            cls.log_status('FAIL', 'NSS version check requires a B2G version.\nReported component versions:\n%s' % (
                '\n'.join(["%s: %s" % (k, versions[k]) for k in versions])))
            return False

        reported_version = versions['NSS_Version']

        if version not in nssversion.b2g_version_to_hginfo:
            cls.log_status('FAIL', 'No version comparison data for B2G %s.\nReported NSS component versions:\n%s' % (
                version, '\n'.join(["%s: %s" % (k, versions[k]) for k in versions])))
            return False

        expected_version = nssversion.b2g_version_to_hginfo[version]['release_nss_version']

        # Fail if reported version is a downgrade
        if nssversion.first_older_than_second(reported_version, expected_version):
            cls.log_status('FAIL', 'NSS downgrade detected. Expecting at least version %s.\n'
                           'Reported versions:\n%s' % (
                           expected_version, '\n'.join(["%s: %s" % (k, versions[k]) for k in versions])))
            return False

        # Pass if NSS version was upgraded.
        if nssversion.first_older_than_second(expected_version, reported_version):
            cls.log_status('PASS', 'NSS more recent than release version %s. Reported component versions:\n%s' % (
                expected_version, '\n'.join(["%s: %s" % (k, versions[k]) for k in versions])))
            return True

        # Else device has reported the expected version.
        cls.log_status('PASS', 'NSS version reported as expected. Reported component versions:\n%s' % (
            '\n'.join(["%s: %s" % (k, versions[k]) for k in versions])))

        return True

