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

#https://gist.github.com/mozkeeler/3531c27239d92bc1535c
#https://developer.mozilla.org/en-US/docs/Mozilla/QA/Marionette/Marionette_JavaScript_Tests
#https://developer.mozilla.org/en-US/Firefox_OS/Automated_testing/XPCShell
#https://developer.mozilla.org/en-US/Firefox_OS/Automated_testing


#######################################################################################################################
# shared module functions
#########################


class certdump( object ):

	@staticmethod
	def js_certdump():
		return '''
			const { 'classes': Cc, 'interfaces': Ci } = Components;
	 
			let certdb = Cc[ "@mozilla.org/security/x509certdb;1" ].getService( Ci.nsIX509CertDB ); // for FxOS >= 2.1
			if ( typeof( certdb.getCerts ) === "undefined" ) {
				certdb = Cc[ "@mozilla.org/security/x509certdb;1" ].getService( Ci.nsIX509CertDB2 ); // for FxOS < 2.1
			}
			let certs = certdb.getCerts();
			let enumerator = certs.getEnumerator();
			let certlist = [];
			while (enumerator.hasMoreElements()) {
				let cert = enumerator.getNext().QueryInterface( Ci.nsIX509Cert );
				let sslTrust, emailTrust, objsignTrust;
				if( typeof( cert.isCertTrusted ) !== "undefined" ) {
					sslTrust = certdb.isCertTrusted( cert, Ci.nsIX509Cert.CA_CERT, Ci.nsIX509CertDB.TRUSTED_SSL );
					emailTrust = certdb.isCertTrusted( cert, Ci.nsIX509Cert.CA_CERT, Ci.nsIX509CertDB.TRUSTED_EMAIL );
					objsignTrust = certdb.isCertTrusted( cert, Ci.nsIX509Cert.CA_CERT, Ci.nsIX509CertDB.TRUSTED_OBJSIGN );
				}
				let certinfo = {
					'cert': cert,
					'sslTrust': sslTrust,
					'emailTrust': emailTrust,
					'objsignTrust': objsignTrust
				};
				certlist.push( certinfo );
			}
			return certlist;
		'''

	@staticmethod
	def js_test():
		return '''
			return Components;
		'''

	def __init__( self ):
		self.logger = get_default_logger()
		try:
			self.dm = mozdevice.DeviceManagerADB( runAdbAsRoot=True )
		except mozdevice.DMError as e:
			self.logger.error( "Error connecting to device via adb (error: %s). Please be " \
			                   "sure device is connected and 'remote debugging' is enabled." % \
			                   e.msg )
			raise
		self.logger.debug( "Attempting to set up port forwarding for marionette" )


	def get_via_marionette( self ):
		self.dm.forward( "tcp:2828", "tcp:2828" )
		return run_marionette_script( certdump.js_certdump(), chrome=True )



#######################################################################################################################
# Test implementations
################################

# derived from shared test class
from suite import ExtraTest


#######################################################################################################################
# nss.certmods

class certmods( ExtraTest ):
	"""
	Test that checks hardcoded certificates in libckbi.so.
	"""

	group = "ssl"
	module = sys.modules[__name__]

	@classmethod
	def run( cls ):
		logger = get_default_logger()

		dumper = certdump()
		certs = dumper.get_via_marionette()
		issues = [ x['cert'][u'subjectName'] for x in certs ]

		if len(issues) > 0:
			cls.log_status( 'FAIL', 'critical SSL certificate issues detected::\n%s' % '\n'.join(issues) )
		else:
			cls.log_status( 'PASS', 'no critical libnss modifications detected' )


