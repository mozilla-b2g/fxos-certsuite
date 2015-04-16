#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import dbm
import sqlite3
import struct
import json
from pyasn1_modules import rfc2459
from pyasn1.codec.der import decoder as derdecoder
from elftools.elf import elffile
#from extrasuite.filesystem import runcmd


def db_is_bsddb( name ):
	return name == "cert8.db" or name == "key3.db"

def db_is_sqlite( name ):
	return name == "cert9.db" or name == "key4.db"

def bsddb_from_file( name ):
	import bsddb185
	if name.endswith( '.db' ):
		name = name[:-3]
	db = bsddb185.open( name, "rb" )
	return db

def sqlite_from_file( name ):
	import sqlite3
	db = sqlite3.connect( name )
	return db

class sqlcerts( object ):

	def __init__( self, filename ):
		self.db = sqlite3.connect( filename )

	def all_fields( self ):
		c = self.db.execute( u'SELECT * FROM nssPublic' )
		fields = list( map( lambda x: x[0], c.description ) )
		assert fields[0] == u'id'
		for field in fields[1:]:
			assert field.startswith( u'a' )
		return fields

	def dump( self ):
		ret = []
		fields = self.all_fields()
		c = self.db.execute( u'SELECT * FROM nssPublic' )
		for line in c.fetchall():
			as_dict = dict( zip( fields, line ) )
			ret.append( as_dict )
		return ret

	def iter_cns( self ):
		c = self.db.execute( u'SELECT a3 FROM nssPublic' )
		for cert in c.fetchall():
			yield str( cert[0] )

	def iter_certs( self ):
		c = self.db.execute( u'SELECT a11 FROM nssPublic' )
		for cert in c.fetchall():
			deccert = derdecoder.decode( str( cert[0] ), asn1Spec=rfc2459.Certificate() )[0]
			yield deccert


# high level: https://dxr.mozilla.org/mozilla-central/source/security/nss/lib/ckfw/builtins/constants.c
# hardcoded certs in http://mxr.mozilla.org/mozilla-central/source/security/nss/lib/ckfw/builtins/certdata.txt
# https://dxr.mozilla.org/mozilla-central/source/security/nss/lib/util/pkcs11t.h
# pull libnsscksi.so
# cert info located between "Mozilla Builtin Roots" and "\x00\x00NSS"

#define CKO_VENDOR_DEFINED    0x80000000 
#define NSSCK_VENDOR_NSS 0x4E534350 /* NSCP */
#define CKO_NSS (CKO_VENDOR_DEFINED|NSSCK_VENDOR_NSS)
#define CKO_NSS_CRL                (CKO_NSS + 1)
#define CKO_NSS_SMIME              (CKO_NSS + 2)
#define CKO_NSS_TRUST              (CKO_NSS + 3)
#define CKO_NSS_BUILTIN_ROOT_LIST  (CKO_NSS + 4)
#define CKO_NSS_NEWSLOT            (CKO_NSS + 5)
#define CKO_NSS_DELSLOT            (CKO_NSS + 6)


class ELFbin( object ):

	def __init__( self, filename ):
		self.f = open( filename, "r" )
		self.elf = elffile.ELFFile( self.f )
		self.sn = []
		self.sni = {}

	def add_section( self, name ):
		s = self.elf.get_section_by_name( name )
		self.sn.append( s )
		self.sni[name] = s

	def find_addr( self, addr ):
		for s in self.sn:
			startaddr = s.header['sh_addr']
			endaddr = startaddr + s.header['sh_size']
			if addr >= startaddr and addr < endaddr:
				#print "address", hex(addr), "is in", s.name, hex(s.header['sh_addr'])
				return s
		return None

	def read_addr( self, addr, size ):
		#print "reading", hex(addr), size
		section = self.find_addr( addr )
		if section is None:
			raise Exception( "invalid address", hex( addr ) )
		section_start = section.header['sh_addr']
		read_offset = addr - section.header['sh_addr']
		data = section.data()[read_offset:read_offset+size]
		if len(data) < size:
			raise Exception( "read beyond section end" )
		return data

	def read_uint32( self, addr ):
		return self.unpack( "I", addr )[0]

	def unpack( self, fmt, addr ):
		size = struct.calcsize( fmt )
		data = self.read_addr( addr, size )
		return struct.unpack( fmt, data )

	def close( self ):
		self.f.close()
		self.elf = None

class libckbi( ELFbin ):

	def __init__( self, filename ):
		super( libckbi, self ).__init__( filename )
		for section in '.text', '.data', '.rodata', '.data.rel.ro.local':
			self.add_section( section )

	def is_ns_builtins_data_entry( self, addr, typecode=None ):
		# (num) (addr) (addr) (0x0 x 12)
		num, typeaddr, itemaddr = self.unpack( "III", addr )
		if num>30:
			return False
		if self.find_addr( typeaddr ) is None:
			return False
		if self.find_addr( itemaddr ) is None:
			return False
		zeros = self.unpack( "I"*12, addr+3*4 )
		for z in zeros:
			if z != 0:
				return False
		return True
		
	def guess_ns_builtins_data_addr( self ):
		sd = self.elf.get_section_by_name( '.data' )
		start_addr = sd.header['sh_addr']
		end_addr = start_addr + sd.header['sh_size'] - 15*4
		# looking for 0x5, addr, addr, 0x0 x 12, assume alignment
		for ptr in xrange( start_addr, end_addr, 4 ):
			if self.is_ns_builtins_data_entry( ptr ):
				if self.is_ns_builtins_data_entry( ptr + 15*4 ):
					return ptr
		return None

	def iter_builtins( self ):
		addr = self.guess_ns_builtins_data_addr()
		if addr is None:
			raise Exception( "incompatible lib format, no builtin found" )
		while self.is_ns_builtins_data_entry( addr ):
			num, types, items = self.unpack( "III", addr )
			yield num, types, items
			addr += 15*4

	def iter_types( self, addr, num ):
		zero = self.read_uint32( addr )
		for ptr in xrange(addr, addr+4*num, 4):
			yield self.read_uint32( ptr )
	
	def list_types( self, addr, num ):
		return [x for x in self.iter_types( addr, num ) ]

	def iter_items( self, addr, num ):
		endaddr = addr + num*8
		for ptr in xrange( addr, endaddr, 8 ):
			iaddr, size = self.unpack( "II", ptr )
			yield self.read_addr( iaddr, size )

	def list_items( self, addr, num ):
		return [x for x in self.iter_items( addr, num )]

	def iter_builtins_data( self ):
		for num, typesaddr, itemsaddr in self.iter_builtins():
			#print "num, types, items", num, hex(typesaddr), hex(itemsaddr)
			types = self.list_types( typesaddr, num )
			#print hex(typesaddr), [hex(x) for x in types]
			items = self.list_items( itemsaddr, num )
			ret = []
			for t, i in zip(types, items):	
				ret.append( (t, i) )
			#print ret
			yield ret

	def list_builtins_data( self ):
		return [x for x in self.iter_builtins_data()]

	decoders = {
		'bool': lambda x: "CK_FALSE" if x == '\x00' else "CK_TRUE",
		'utf8': lambda x: x[:-1].decode('utf8').encode('utf8'),
		'uint32': lambda x: struct.unpack('I', x)[0],
		'uhex32': lambda x: hex(struct.unpack('I', x)[0]),
		'repr': lambda x: repr(x)
	}

	typemap = {
		'0x0': ('CKA_CLASS', 'uhex32'),
		'0x1': ('CKA_TOKEN', 'bool'),
		'0x2': ('CKA_PRIVATE', 'bool'),
		'0x3': ('CKA_LABEL', 'utf8'),
		'0x10': 'CKA_APPLICATION',
		'0x11': 'CKA_VALUE',
		'0x12': 'CKA_OBJECT_ID',
		'0x80': ('CKA_CERTIFICATE_TYPE', 'uhex32'),
		'0x81': 'CKA_ISSUER',
		'0x82': ('CKA_SERIAL_NUMBER', 'repr'),
		'0x83': 'CKA_AC_ISSUER',
		'0x84': 'CKA_OWNER',
		'0x85': 'CKA_ATTR_TYPES',
		'0x86': ('CKA_TRUSTED', 'bool'),
		'0x100': 'CKA_KEY_TYPE',
		'0x101': 'CKA_SUBJECT',
		'0x102': ('CKA_ID', 'repr'),
		'0x170': ('CKA_MODIFIABLE', 'bool'),
		'0xce534351': 'CKO_NSS_CRL',
		'0xce534352': 'CKO_NSS_SMIME',
		'0xce534353': 'CKO_NSS_TRUST',
		'0xce534354': 'CKO_NSS_BUILTIN_ROOT_LIST',
		'0xce534355': 'CKO_NSS_NEWSLOT',
		'0xce534356': 'CKO_NSS_DELSLOT',
		'0xce536358': ('CKA_TRUST_SERVER_AUTH', 'uhex32'),
		'0xce536359': ('CKA_TRUST_CLIENT_AUTH', 'uhex32'),
		'0xce53635a': ('CKA_TRUST_CODE_SIGNING', 'uhex32'),
		'0xce53635b': ('CKA_TRUST_EMAIL_PROTECTION', 'uhex32'),
		'0xce53635c': ('CKA_TRUST_IPSEC_END_SYSTEM', 'uhex32'),
		'0xce53635d': ('CKA_TRUST_IPSEC_TUNNEL', 'uhex32'),
		'0xce53635e': ('CKA_TRUST_IPSEC_USER', 'uhex32'),
		'0xce53635f': ('CKA_TRUST_TIME_STAMPING', 'uhex32'),
		'0xce536360': ('CKA_TRUST_STEP_UP_APPROVED', 'bool'),
		'0xce5363b4': 'CKA_CERT_SHA1_HASH',
		'0xce5363b5': 'CKA_CERT_MD5_HASH'
	}

	def map_type( self, typecode, value ):
		try:
			mapped = self.typemap[hex(typecode)]
		except KeyError:
			print >> sys.stderr, "WARNING: unmapped type", hex(typecode)
			mapped = (hex(x), 'repr')
		if type( mapped ) is tuple:
			mappedtype, decoder = mapped
			return mappedtype, self.decoders[decoder](value)
		else:
			return mapped, repr(value)

#############################################################################################

cmd = sys.argv[1]
filename = sys.argv[2]

#if db_is_bsddb( filename ):
#	db = bsddb_from_file( filename )
#
#if db_is_sqlite( filename ):
#	db = sqlite_from_file( filename )

dbc = sqlcerts( filename )

if cmd == 'dump':
	for l in dbc.dump():
		for k in l:
			try:
				print "%s:	%s" % (k,str(l[k]))
			except UnicodeDecodeError:
				s = str(l[k])
				print "%s:	%s" % (k,repr(l[k]))

elif cmd == 'certs':
	for cert in dbc.iter_certs():
		print cert.prettyPrint()

elif cmd == 'cn':
	for cn in dbc.iter_cns():
		print cn

elif cmd == 'lib':
	filename = sys.argv[2]
	lib = libckbi( filename )
	builtins = lib.list_builtins_data()
	allb = []
	for builtin in builtins:
		oneb = {}
		for itemtype, item in builtin:
			verbtype, verbitem = lib.map_type( itemtype, item )
			oneb[verbtype] = verbitem
			allb.append( oneb )
	print json.dumps( allb, sort_keys=True, indent=4, separators=(',', ': ') )

elif cmd == 'ipython':
	from IPython import embed
	embed()

else:
	print "unknown command:", cmd
	print "usage: dump|certs|cn|ipython <cert db file>"
