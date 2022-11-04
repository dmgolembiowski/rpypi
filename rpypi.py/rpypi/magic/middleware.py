#!/usr/bin/env python3
# 
# File: /rpypi.py/rpypi/magic/backend.py
# 
# Adapted from a solution originally published by 
# David Beazly, the Euler of Python.
from typing import * # NoQA
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser
from contextlib import suppress, contextmanager, asynccontextmanager
from importlib.abc import SourceLoader
from immutables import Map as ImmutableMap
import importlib.abc
import threading

class InstalledMetaCache:
    
    def __init__(self, preset: Optional[Map] = None):
        """

        """
        if preset is not None:
            try:
                assert(isinstance(preset, Map
            self.inner = preset
        else:
            self.i
        self.locked = False

    @contextmanager
    def __enter__(self):
        # Call Rust library to either:
        # pre-1) Spin up the server as configured
        # pre-2) If already configured, check for reachability
        # pre-3) Raise any connection errors
        # pre-4) Tell rpypi-server to persist the socket 
        return self

    def __exit__(self):
        # Release the underlying rust unix socket connection
        return self

# ToDo:

def _get_links(url):
    class LinkParser(HTMLParser):

        def handle_starttag(self, tag, attrs):
            # ToDo:
            # =====
            # See if we can optimize this to build out 
            # pre-cached link attributes and save lookups
            if tag == 'a':
                attrs = dict(attrs)
                links.add(attrs.get('href').rstrip('/'))

    links = set()
    try:
        # ToDo:
        # =====
        # Forward debug logging to rpypi tracing socket
        log.debug('Getting links from %s' % url)
        # ToDo:
        # =====
        # Replace the urlopen with `acquire_socket`
        u = urlopen(url)
        # Move the extra allocations to a nonlocal stack to 
        # avoid unnnecessary re-allocations
        parser = LinkParser()
        # Maybe do `os.sendfile` somehow for a fast C-binding
        parser.feed(u.read().decode('utf-8'))
    except Exception as e:
        # Need to case out these exceptions, i.e. NotFound, Timeout, etc.
        log.debug('Could not get links. %s', e)
    log.debug('links: %r', links) # tracing!
    return links

class UrlMetaFinder(importlib.abc.MetaPathFinder):
    def __init__(self, baseurl):
        self._baseurl = baseurl
        self._links   = { }
        # Can these loaders be extended to include /dev/loop 
        # devices, for additional threads to share this?
        self._loaders = { baseurl : UrlModuleLoader(baseurl) }

    def find_module(self, fullname, path=None):
        log.debug('find_module: fullname=%r, path=%r', fullname, path) # tracing!
        if path is None:
            baseurl = self._baseurl
        else:
            # Returning None cannot work here,
            # if all else fails we need some way to 
            # tell the server to install it and wait on it,
            # then if that fails, try to locally import (or install+import) it 
            # otherwise raise a non-recoverable error.
            if not path[0].startswith(self._baseurl):
                return None
            baseurl = path[0]

        # Document why the `.split('.')` is used, maybe pref an iter().last()?
        # in Rust land?
        parts = fullname.split('.')
        basename = parts[-1]
        log.debug('find_module: baseurl=%r, basename=%r', baseurl, basename) # tracing!

        # Check link cache
        if basename not in self._links:
            self._links[baseurl] = _get_links(baseurl)

        # Check if it's a package
        if basename in self._links[baseurl]:
            log.debug('find_module: trying package %r', fullname) # tracing!
            fullurl = self._baseurl + '/' + basename
            # Attempt to load the package (which accesses __init__.py)
            loader = UrlPackageLoader(fullurl)
            try:
                loader.load_module(fullname)
                self._links[fullurl] = _get_links(fullurl)
                self._loaders[fullurl] = UrlModuleLoader(fullurl)
                log.debug('find_module: package %r loaded', fullname)
            except ImportError as e:
                # ToDo:
                # =====
                # Again, I want this to do more robust error handling
                # with three or more fallback conditions. For instance,
                # can we check if other nodes in some shared pool have 
                # the library, or maybe scan the filesystem to see if it 
                # was saved under a different PYTHON_PATH than it originally
                # loaded 
                log.debug('find_module: package failed. %s', e) # tracing!
                loader = None
            return loader

        # A normal module
        filename = basename + '.py'
        if filename in self._links[baseurl]:
            log.debug('find_module: module %r found', fullname) # tracing!
            return self._loaders[baseurl]
        else:
            log.debug('find_module: module %r not found', fullname) # tracing!
            return None

    def invalidate_caches(self):
        log.debug('invalidating link cache') # tracing!
        self._links.clear()

# Module Loader for a URL
class UrlModuleLoader(importlib.abc.SourceLoader):
    def __init__(self, baseurl):
        self._baseurl = baseurl
        self._source_cache = {}

    def module_repr(self, module):
        return '<urlmodule %r from %r>' % (module.__name__, module.__file__)

    # Required method
    def load_module(self, fullname):
        code = self.get_code(fullname)
        # This might potentially break the dynamically-linked 
        # Rust FFI binding, so to prevent this, it might be
        # essential to set an `exclusions` set wrapper around the 
        # `sys.modules.setdefault` function.
        mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
        mod.__file__ = self.get_filename(fullname)
        mod.__loader__ = self
        mod.__package__ = fullname.rpartition('.')[0]
        exec(code, mod.__dict__)
        return mod

    # Optional extensions
    def get_code(self, fullname):
        src = self.get_source(fullname)
        # It might be a terrible idea to call `compile` 
        # on a Rust-binding source file. Not sure yet though
        return compile(src, self.get_filename(fullname), 'exec')

    # ToDo:
    # =====
    # - Security checksum?
    # - Enforce TLS/HTTPS on non-LAN sources?
    def get_data(self, path):
        pass

    def get_filename(self, fullname):
        return self._baseurl + '/' + fullname.split('.')[-1] + '.py'

    def get_source(self, fullname):
        filename = self.get_filename(fullname)
        log.debug('loader: reading %r', filename) # tracing!
        if filename in self._source_cache:
            log.debug('loader: cached %r', filename)
            return self._source_cache[filename]
        try:
            u = urlopen(filename)
            source = u.read().decode('utf-8')
            log.debug('loader: %r loaded', filename) # tracing!
            self._source_cache[filename] = source
            return source
        except (HTTPError, URLError) as e:
            log.debug('loader: %r failed.  %s', filename, e) # tracing!
            raise ImportError("Can't load %s" % filename)

    def is_package(self, fullname):
        return False

# Package loader for a URL
class UrlPackageLoader(UrlModuleLoader):
    def load_module(self, fullname):
        mod = super().load_module(fullname)
        mod.__path__ = [ self._baseurl ]
        mod.__package__ = fullname

    def get_filename(self, fullname):
        return self._baseurl + '/' + '__init__.py'

    def is_package(self, fullname):
        return True

# Utility functions for installing/uninstalling the loader
_installed_meta_cache = { }
def install_meta(address):
    if address not in _installed_meta_cache:
        finder = UrlMetaFinder(address)
        _installed_meta_cache[address] = finder
        sys.meta_path.append(finder)
        log.debug('%r installed on sys.meta_path', finder)
    
def remove_meta(address):
    if address in _installed_meta_cache:
        finder = _installed_meta_cache.pop(address)
        sys.meta_path.remove(finder)
        log.debug('%r removed from sys.meta_path', finder)

# Path finder class for a URL
class UrlPathFinder(importlib.abc.PathEntryFinder):
    def __init__(self, baseurl):
        self._links = None
        self._loader = UrlModuleLoader(baseurl)
        self._baseurl = baseurl

    def find_loader(self, fullname):
        log.debug('find_loader: %r', fullname)
        parts = fullname.split('.')
        basename = parts[-1]
        # Check link cache
        if self._links is None:
            self._links = []     # See discussion
            self._links = _get_links(self._baseurl)

        # Check if it's a package
        if basename in self._links:
            log.debug('find_loader: trying package %r', fullname)
            fullurl = self._baseurl + '/' + basename
            # Attempt to load the package (which accesses __init__.py)
            loader = UrlPackageLoader(fullurl)
            try:
                loader.load_module(fullname)
                log.debug('find_loader: package %r loaded', fullname)
            except ImportError as e:
                log.debug('find_loader: %r is a namespace package', fullname)
                loader = None
            return (loader, [fullurl])

        # A normal module
        filename = basename + '.py'
        if filename in self._links:
            log.debug('find_loader: module %r found', fullname)
            return (self._loader, [])
        else:
            log.debug('find_loader: module %r not found', fullname)
            return (None, [])

    def invalidate_caches(self):
        log.debug('invalidating link cache')
        self._links = None

_url_path_cache = {}

def handle_url(path):
    # ToDo:
    # =====
    # Add additional handlers preempting these ones for
    # unix domain sockets, tcp sockets, and perhaps other sources
    # like ... `magnet` lol, this should be an April Fool's RFC to 
    # importlib on Python next year.
    # Might not be a terrible idea for macvlan networks 
    if path.startswith(('http://', 'https://')):
        log.debug('Handle path? %s. [Yes]', path)
        if path in _url_path_cache:
            finder = _url_path_cache[path]
        else:
            finder = UrlPathFinder(path)
            _url_path_cache[path] = finder
        return finder
    else:
        log.debug('Handle path? %s. [No]', path)

def install_path_hook():
    sys.path_hooks.append(handle_url)
    sys.path_importer_cache.clear()
    log.debug('Installing handle_url')
    
def remove_path_hook():
    sys.path_hooks.remove(handle_url)
    sys.path_importer_cache.clear()
    log.debug('Removing handle_url')
