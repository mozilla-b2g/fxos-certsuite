 # -*- coding: utf-8 -*-
import sys
import os
import logging
import json
import socket
import signal
import threading
from multiprocessing import Process, Event
from collections import defaultdict
import urllib2
import uuid
import argparse

repo_root = os.path.abspath(os.path.split(__file__)[0])

sys.path.insert(1, os.path.join(repo_root, "tools", "wptserve"))
from wptserve import server as wptserve, handlers
from wptserve.router import any_method
sys.path.insert(1, os.path.join(repo_root, "tools", "pywebsocket", "src"))
from mod_pywebsocket import standalone as pywebsocket

routes = [("GET", "/tools/runner/*", handlers.file_handler),
          (any_method, "/tools/*", handlers.ErrorHandler(404)),
          (any_method, "/serve.py", handlers.ErrorHandler(404)),
          (any_method, "*.py", handlers.python_script_handler),
          ("GET", "*.asis", handlers.as_is_handler),
          ("GET", "*", handlers.file_handler),
          ]

rewrites = [("GET", "/resources/WebIDLParser.js", "/resources/webidl2/lib/webidl2.js")]

subdomains = [u"www",
              u"www1",
              u"www2",
              u"天気の良い日",
              u"élève"]

logger = None

def default_logger(level):
    logger = logging.getLogger("web-platform-tests")
    logging.basicConfig(level=getattr(logging, level.upper()))
    return logger

def open_socket(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if port != 0:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', port))
    sock.listen(5)
    return sock

def get_port():
    free_socket = open_socket(0)
    port = free_socket.getsockname()[1]
    logger.debug("Going to use port %s" % port)
    free_socket.close()
    return port


class ServerProc(object):
    def __init__(self):
        self.proc = None
        self.daemon = None
        self.stop = Event()

    def start(self, init_func, config, paths, port, bind_hostname):
        self.proc = Process(target=self.create_daemon, args=(init_func, config, paths, port, bind_hostname))
        self.proc.daemon = True
        self.proc.start()

    def create_daemon(self, init_func, config, paths, port, bind_hostname):
        try:
            self.daemon = init_func(config, paths, port, bind_hostname)
        except socket.error:
            logger.error("Socket error on port %s" % port)
            raise

        if self.daemon:
            self.daemon.start(block=False)
            try:
                self.stop.wait()
            except KeyboardInterrupt:
                pass

    def wait(self):
        self.stop.set()
        self.proc.join()

    def kill(self):
        self.stop.set()
        self.proc.terminate()
        self.proc.join()

def check_subdomains(config, paths, subdomains, bind_hostname):
    port = get_port()
    wrapper = ServerProc()
    wrapper.start(start_http_server, config, paths, port, bind_hostname)

    rv = {}

    for subdomain, (punycode, host) in subdomains.iteritems():
        domain = "%s.%s" % (punycode, host)
        try:
            urllib2.urlopen("http://%s:%d/" % (domain, port))
        except Exception as e:
            if config["external_domain"]:
                external = "%s.%s" % (punycode, config["external_domain"])
                logger.warning("Using external server %s for subdomain %s" % (external, subdomain))
                rv[subdomain] = external
            else:
                logger.critical("Failed probing domain %s and no external fallback configured. You may need to edit /etc/hosts or similar." % domain)
                sys.exit(1)
        else:
            rv[subdomain] = "%s.%s" % (punycode, host)

    wrapper.wait()

    return rv

def get_subdomains(config):
    #This assumes that the tld is ascii-only or already in punycode
    host = config["host"]
    return {subdomain: (subdomain.encode("idna"), host)
            for subdomain in subdomains}

def start_servers(config, paths, ports, bind_hostname):
    servers = defaultdict(list)

    host = config["host"]

    for scheme, ports in ports.iteritems():
        assert len(ports) == {"http":2}.get(scheme, 1)

        for port  in ports:
            init_func = {"http":start_http_server,
                         "https":start_https_server,
                         "ws":start_ws_server,
                         "wss":start_wss_server}[scheme]

            server_proc = ServerProc()
            server_proc.start(init_func, config, paths, port, bind_hostname)

            logger.info("Started server at %s://%s:%s" % (scheme, config["host"], port))
            servers[scheme].append((port, server_proc))

    return servers

def start_http_server(config, paths, port, bind_hostname):
    return wptserve.WebTestHttpd(host=config["host"],
                                 port=port,
                                 doc_root=paths["doc_root"],
                                 routes=routes,
                                 rewrites=rewrites,
                                 bind_hostname=bind_hostname,
                                 config=config,
                                 use_ssl=False,
                                 certificate=None)

def start_https_server(config, paths, port, bind_hostname):
    return

class WebSocketDaemon(object):
    def __init__(self, host, port, doc_root, handlers_root, log_level, bind_hostname):
        self.host = host
        cmd_args = ["-p", port,
                    "-d", doc_root,
                    "-w", handlers_root,
                    "--log-level", log_level]
        if (bind_hostname):
            cmd_args = ["-H", host] + cmd_args
        opts, args = pywebsocket._parse_args_and_config(cmd_args)
        opts.cgi_directories = []
        opts.is_executable_method = None
        self.server = pywebsocket.WebSocketServer(opts)
        ports = [item[0].getsockname()[1] for item in self.server._sockets]
        assert all(item == ports[0] for item in ports)
        self.port = ports[0]
        self.started = False
        self.server_thread = None

    def start(self, block=False):
        logger.info("Starting websockets server on %s:%s" % (self.host, self.port))
        self.started = True
        if block:
            self.server.serve_forever()
        else:
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.setDaemon(True)  # don't hang on exit
            self.server_thread.start()

    def stop(self):
        """
        Stops the server.

        If the server is not running, this method has no effect.
        """
        if self.started:
            try:
                self.server.shutdown()
                self.server.server_close()
                self.server_thread.join()
                self.server_thread = None
                logger.info("Stopped websockets server on %s:%s" % (self.host, self.port))
            except AttributeError:
                pass
            self.started = False
        self.server = None

def start_ws_server(config, paths, port, bind_hostname):
    return WebSocketDaemon(config["host"],
                           str(port),
                           repo_root,
                           paths["ws_doc_root"],
                           "debug",
                           bind_hostname)

def start_wss_server(config, paths, port, bind_hostname):
    return

def get_ports(config):
    rv = defaultdict(list)
    for scheme, ports in config["ports"].iteritems():
        for i, port in enumerate(ports):
            if port == "auto":
                port = get_port()
            else:
                port = port
            rv[scheme].append(port)
    return rv

def normalise_config(config, domains, ports):
    ports_ = {}
    for scheme, ports_used in ports.iteritems():
        ports_[scheme] = ports_used

    domains_ = domains.copy()
    domains_[""] = config["host"]

    return {"host":config["host"],
            "domains":domains_,
            "ports": ports_}

def start(config):
    ports = get_ports(config)
    domains = get_subdomains(config)
    bind_hostname = config["bind_hostname"]

    paths = {"doc_root": config["doc_root"],
             "ws_doc_root": config["ws_doc_root"]}

    if config["check_subdomains"]:
        domains = check_subdomains(config, paths, domains, bind_hostname)

    config_ = normalise_config(config, domains, ports)

    servers = start_servers(config_, paths, ports, bind_hostname)

    return config_, servers


def iter_procs(servers):
    for servers in servers.values():
        for port, server in servers:
            yield server.proc

def value_set(config, key):
    return key in config and config[key] is not None

def set_computed_defaults(config):
    if not value_set(config, "ws_doc_root"):
        if value_set(config, "doc_root"):
            root = config["doc_root"]
        else:
            root = repo_root
        config["ws_doc_root"] = os.path.join(repo_root, "websockets", "handlers")

    if not value_set(config, "doc_root"):
        config["doc_root"] = repo_root


def merge_json(base_obj, override_obj):
    rv = {}
    for key, value in base_obj.iteritems():
        if key not in override_obj:
            rv[key] = value
        else:
            if isinstance(value, dict):
                rv[key] = merge_json(value, override_obj[key])
            else:
                rv[key] = override_obj[key]
    return rv

def load_config(default_path, override_path=None):
    if os.path.exists(default_path):
        with open(default_path) as f:
            base_obj = json.load(f)
    else:
        raise ValueError("Config path %s does not exist" % default_path)

    if os.path.exists(override_path):
        with open(override_path) as f:
            override_obj = json.load(f)
    else:
        override_obj = {}
    rv = merge_json(base_obj, override_obj)

    set_computed_defaults(rv)
    return rv

def main():
    global logger

    config = load_config("config.default.json",
                         "config.json")

    logger = default_logger(config["log_level"])

    config_, servers = start(config)

    try:
        while any(item.is_alive() for item in iter_procs(servers)):
            for item in iter_procs(servers):
                item.join(1)
    except KeyboardInterrupt:
        logger.info("Shutting down")

if __name__ == "__main__":
    main()
