"""
MIT License

Copyright (c) 2017 Gr4ph0s

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import imp


class ImportTester(type):
    _HaveBeenCalled = False
    _CanImport = False

    @classmethod
    def _CheckImport(cls, clsName):
        # If we already test, we return the cached value
        if cls._HaveBeenCalled:
            return cls._CanImport

        # Check if module is already pressent
        try:
            imp.find_module(clsName)
            cls._CanImport = True
            return True

        # If module is not already loaded we try to laod it
        except ImportError:
            try:
                __import__(clsName)
                cls._CanImport = True
                return True

            except ImportError:
                print(__import__(clsName))
                cls._CanImport = False
                return False

    def __call__(cls, *args, **kwargs):
        if not cls._HaveBeenCalled:
            cls._CheckImport("redshift")
            cls._HaveBeenCalled = True

        if cls._CanImport:
            return super(ImportTester, cls).__call__(*args, **kwargs)
        else:
            return False
