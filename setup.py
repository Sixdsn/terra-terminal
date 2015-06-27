#!/usr/bin/env python2
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012 Ozcan ESEN <ozcanesen@gmail.com>
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import io
import os
import re
import subprocess
from setuptools import Extension, find_packages, setup


def read_file_contents(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ) as fp:
        return fp.read()


def get_package_info(name):
    file_contents = read_file_contents(os.path.join('terra', '__init__.py'))
    version_match = re.search(r'^%s\s*=\s*[\'"](.*?)[\'"]' % name, file_contents, re.M)

    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find %s string.' % name)


def parse_pkg_config(command, components, options_dict=None):
    if options_dict is None:
        options_dict = {
            'include_dirs': [],
            'library_dirs': [],
            'libraries': [],
            'extra_compile_args': []
        }

    commandLine = '%s --cflags --libs %s' % (command, components)
    output = get_command_output(commandLine).strip()
    for comp in output.split():
        prefix, rest = comp[:2], comp[2:]
        if prefix == '-I':
            options_dict['include_dirs'].append(rest)
        elif prefix == '-L':
            options_dict['library_dirs'].append(rest)
        elif prefix == '-l':
            options_dict['libraries'].append(rest)
        else:
            options_dict['extra_compile_args'].append(comp)

    commandLine = '%s --variable=libdir %s' % (command, components)
    output = get_command_output(commandLine).strip()

    return options_dict


def get_command_output(cmd, warn_on_stderr=True, warn_on_return_code=True):
    """Wait for a command and return its output.  Check for common
    errors and raise an exception if one of these occurs.
    """
    print('>>>' + cmd)
    p = subprocess.Popen(cmd, shell=True, close_fds=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if warn_on_stderr and stderr != '':
        raise RuntimeError('%s outputted the following error:\n%s' %
                           (cmd, stderr))
    if warn_on_return_code and p.returncode != 0:
        raise RuntimeError('%s had non-zero return code %d' %
                           (cmd, p.returncode))
    return stdout


ext_sources = [
    'ext/globalhotkeys/globalhotkeys.c',
    'ext/globalhotkeys/bind.c',
]
gtk_config = parse_pkg_config('pkg-config', 'gtk+-3.0')
globalhotkeys = Extension('terra.globalhotkeys', ext_sources, **gtk_config)


setup(
    name='terra',
    version=get_package_info('__version__'),
    description=get_package_info('__description__'),
    author=get_package_info('__author__'),
    author_email=get_package_info('__author_email__'),
    license=get_package_info('__license__'),
    url=get_package_info('__url__'),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'terra = terra.__main__:main'
        ],
    },
    data_files=[
        ('share/icons/hicolor/scalable/apps', ['terra/resources/terra.svg']),
        ('share/applications', ['terra/resources/terra.desktop'])
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Terminals',
    ],
    ext_modules=[globalhotkeys]
)
