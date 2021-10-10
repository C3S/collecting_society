#!/usr/bin/env python
# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
from setuptools import setup
import re
import os
import configparser

MODULE = 'collecting_society'
PREFIX = 'c3s'
MODULE2PREFIX = {}


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


config = configparser.ConfigParser()
config.readfp(open('tryton.cfg'))
info = dict(config.items('tryton'))
for key in ('depends', 'extras_depend', 'xml'):
    if key in info:
        info[key] = info[key].strip().splitlines()
version_info = info.get('version', '0.2')
branch, _ = version_info.rsplit('.', 1)
dev_branch = float(branch) * 10
# Warning: Check, after version 3.9 must follow 4.0. This calculation only
# works if the Tryton project follows a strict sequence version number policy.
if not (dev_branch % 2):  # dev_branch is a release branch
    dev_branch -= 1
next_branch = dev_branch + 2
branch_range = str(dev_branch / 10), str(next_branch / 10)
requires = ['hurry.filesize']

for dep in info.get('depends', []):
    if not re.match(r'(ir|res|webdav)(\W|$)', dep):
        prefix = MODULE2PREFIX.get(dep, 'trytond')
        requires += ['%s_%s >= %s, < %s' % ((prefix, dep,) + branch_range)]
requires += ['trytond >= %s, < %s' % branch_range]
tests_require = ['proteus >= %s, < %s' % branch_range]

setup(
    name='%s_%s' % (PREFIX, MODULE),
    version=version_info,
    description='Tryton module %s from %s' % (MODULE, PREFIX),
    long_description=read('README.rst'),
    author='virtual things',
    author_email='info@virtual-things.biz',
    url='http://www.virtual-things.biz',
    package_dir={'trytond.modules.%s' % MODULE: '.'},
    packages=[
        'trytond.modules.%s' % MODULE,
        'trytond.modules.%s.tests' % MODULE,
    ],
    package_data={
        'trytond.modules.%s' % MODULE: (
            info.get('xml', []) + [
                '*.odt', '*.ods', 'icons/*.svg', 'tryton.cfg', 'view/*.xml',
                'locale/*.po', 'tests/*.rst']),
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Framework :: Tryton',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Legal Industry',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Natural Language :: English',
        'Natural Language :: German',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Office/Business',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Artistic Software',
    ],
    license='AGPL-3',
    install_requires=requires,
    zip_safe=False,
    entry_points="""
    [trytond.modules]
    %s = trytond.modules.%s
    """ % (MODULE, MODULE),
    test_suite='tests',
    test_loader='trytond.test_loader:Loader',
    tests_require=tests_require,
)
