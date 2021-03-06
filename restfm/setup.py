# Copyright (C) 2012 by the Free Software Foundation, Inc.
#
# This file is part of Postorius.
#
# Postorius is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Postorius is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Postorius.  If not, see <http://www.gnu.org/licenses/>.

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name = "restfm",
    version = '1.0.0a1',
    description = "public facing apis for postorius",
    long_description=open('README.rst').read(),
    maintainer = "AREGEE",
    license = 'GPLv3',
    keywords = 'email mailman django',
    url = "https://github.com/aregee/rest-mailman.git",
    classifiers = [
        "Programming Language :: Python",
        ],
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data = True,
    install_requires = ['djangorestframework==2.2.6',
                        'mailmanclient', ]
)
