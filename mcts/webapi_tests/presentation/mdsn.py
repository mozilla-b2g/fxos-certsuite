#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals
import socket
import sys

from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo


class ServiceListener(object):
    iplist = []
    namelist = []
    infolist = []

    # Check if desired ip showed up as a service host and return [ip,port]
    def check_ip(self, ip):
        for ipport in self.iplist:
            if ipport[0] == ip:
                return ipport
        for ipport in self.iplist:
            if ipport[0] == "tv":
                return [ip, ipport[1]]
        return False

    # Add services if any service host discovered
    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name, timeout=4000)
        self.namelist.append(name)
        self.infolist.append(info)
        si = ServiceInfo(type, name)
        if info:
            self.iplist.append([socket.inet_ntoa(info.address), info.port])
        else:
            si.request(zeroconf, 5000)
            self.iplist.append(["tv", si.port])
