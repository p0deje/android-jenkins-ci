#!/usr/bin/python

"""
Jenkins continuous integration Python script for building and testing
Android applications.

Author: Alex "p0deje" Rodionov
Homepage: https://github.com/p0deje/android-jenkins-ci/
"""

"""This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""

from xml.dom.minidom import Document
from string import join
from shutil import rmtree
from subprocess import check_call, CalledProcessError
import os
import re

print '\n' + ' --------------------- BEGIN --------------------- '
print 'Preparing...'

""" VARIABLES """
APPLICATION = 'application'
TESTS = 'tests'
EMULATOR = 'emulator'
REAL = 'real'

# Android SDK
sdk_dir = '/opt/android-sdk-update-manager'
adb = sdk_dir + '/platform-tools/adb'

# directories
print '  Checking directories...'
root = os.environ['WORKSPACE'] # access to Jenkins workspace
app_dir = root + '/trunk'
tests_dir = root + '/tests'
reports_dir = tests_dir + '/reports'
if not os.path.exists(reports_dir):
    os.mkdir(reports_dir)

# device (emulator or real) and correct adb command line arg
device_type = EMULATOR
if device_type is REAL:
    device = ['-d']
elif device_type is EMULATOR:
    emulator = os.environ['ANDROID_AVD_DEVICE'] # access to emulator plugin device
    device = ['-s'] + [emulator]

# project
company_name = 'company'
app_name = 'app'
package_name = 'com.' + company_name + '.' + app_name
tests_name = app_name + 'tests'
target = 'android-8'

""" FUNCTIONS """
def execute(arg):
    """Prints fine command to execute and wrap it with try-except."""
    try:
        print '  Running command ' + join(arg, ' ')
        check_call(arg)
    except CalledProcessError:
        print '  Failed to execute command ' + join(arg, ' ') + '. Aborting.'
        quit()

def create_build_xml(arg):
    """Creates build.xml for Apache Ant."""
    # prepare document
    build_xml = Document()
    # prepare <project>
    build_project = build_xml.createElement('project')
    # different build.xml files
    if arg is TESTS:
        build_project.setAttribute('name', tests_name)
        build_project_dir = build_xml.createElement('property')
        build_project_dir.setAttribute('name', 'tested.project.dir')
        build_project_dir.setAttribute('value', app_dir)
        build_project.appendChild(build_project_dir)
    elif arg is APPLICATION:
        build_project.setAttribute('name', app_name)
        # write <project>
    build_project.setAttribute('default', 'help')
    build_xml.appendChild(build_project)
    # write <property name='target'>
    build_target = build_xml.createElement('property')
    build_target.setAttribute('name', 'target')
    build_target.setAttribute('value', target)
    build_project.appendChild(build_target)
    # write <property name='sdk.dir'>
    build_sdk_dir = build_xml.createElement('property')
    build_sdk_dir.setAttribute('name', 'sdk.dir')
    build_sdk_dir.setAttribute('value', sdk_dir)
    build_project.appendChild(build_sdk_dir)
    # write <path id=''>
    build_path = build_xml.createElement('path')
    build_path.setAttribute('id', 'android.antlibs')
    build_project.appendChild(build_path)
    # write <pathelement>
    jars = ['anttasks.jar', 'sdklib.jar', 'androidprefs.jar']
    for jar in jars:
        build_pathelement = build_xml.createElement('pathelement')
        build_pathelement.setAttribute('path', '${sdk.dir}/tools/lib/' + jar)
        build_path.appendChild(build_pathelement)
        # write <taskdef>
    build_taskdef = build_xml.createElement('taskdef')
    build_taskdef.setAttribute('classpathref', 'android.antlibs')
    build_taskdef.setAttribute('classname', 'com.android.ant.SetupTask')
    build_taskdef.setAttribute('name', 'setup')
    build_project.appendChild(build_taskdef)
    # write <setup />
    build_setup = build_xml.createElement('setup')
    build_project.appendChild(build_setup)
    # finish build.xml
    build_xml = build_xml.toprettyxml('  ', '\n', 'UTF-8')
    return build_xml

def build(arg):
    """Compiles source code into apk file."""
    # go to necessary directory
    if arg is APPLICATION:
        os.chdir(app_dir)
    elif arg is TESTS:
        os.chdir(tests_dir)
        # check for build.xml existence
    exist = os.path.exists('build.xml')
    if exist:
        print 'Apache Ant build.xml file exists...'
    else:
        # create temporary build.xml
        print 'Apache Ant build.xml file does not exist. Writing new one...'
        if arg is APPLICATION:
            build_xml = create_build_xml(APPLICATION)
        elif arg is TESTS:
            build_xml = create_build_xml(TESTS)
        temp_build_xml = open('build.xml', 'w')
        temp_build_xml.write(build_xml)
        temp_build_xml.close()
        # for tests, AndroidManifest.xml additionally needs non-default test-runner
    if arg is TESTS:
        # look if it's not already set
        manifest = open('AndroidManifest.xml', 'r')
        manifest = manifest.read()
        default = re.search('android:name="android.test.InstrumentationTestRunner"', manifest)
        # if default test-runner is set
        if default:
            new_manifest = re.sub('android:name="android.test.InstrumentationTestRunner"',
                                  'android:name="com.zutubi.android.junitreport.JUnitReportTestRunner"', manifest)
            manifest = open('AndroidManifest.xml', 'w')
            manifest.write(new_manifest)
            # close AndroidManifest.xml
            manifest.close()
        # build apk file
    print 'Compiling...'
    execute(['ant', '-quiet', 'debug'])
    print '  Done.'
    # if temporary build.xml, remove it
    if not exist:
        print 'Removing temporary build.xml...'
        os.unlink('build.xml')
        # go back to root
    os.chdir(root)

def install(arg):
    """Installs apk file to device."""
    print 'Installing ' + arg + '...'
    # prepare path to apk
    if arg is TESTS:
        apk = tests_dir + '/bin/' + tests_name + '-debug.apk'
    elif arg is APPLICATION:
        apk = app_dir + '/bin/' + app_name + '-debug.apk'
        # install
    command = [adb] + device + ['install', apk]
    execute(command)
    print '  Done.'

def run_tests():
    """Runs tests."""
    print 'Running tests...'
    command = [adb] + device + ['shell', 'am', 'instrument', '-w',
                                package_name + '.tests' + '/com.zutubi.android.junitreport.JUnitReportTestRunner']
    execute(command)
    print '  Done.'

def fetch_report():
    """Downloads generated JUnit test report."""
    print 'Fetching test report...'
    command = [adb] + device + ['pull', '/data/data/' + package_name + '/files/junit-report.xml', reports_dir]
    execute(command)
    print '  Done.'

def cleanup_dirs():
    """Performs necessary cleanup actions on directories."""
    print 'Removing directories with compiled files to avoid collisions...'
    # remove dirs with compiled files
    if os.path.exists(app_dir + '/bin'):
        rmtree(app_dir + '/bin')
    if os.path.exists(tests_dir + '/bin'):
        rmtree(tests_dir + '/bin')
    print '  Done.'

def uninstall():
    """Uninstall packages from real device."""
    if device_type is REAL:
        print 'Uninstalling packages from device...'
        command = [adb] + device + ['uninstall', package_name]
        execute(command)
        command = [adb] + device + ['uninstall', package_name + '.tests']
        execute(command)
        print '  Done.'

""" SCRIPT ITSELF """
if __name__ == '__main__':
    print 'All prepared. Running...'
    build(APPLICATION)
    build(TESTS)
    install(APPLICATION)
    install(TESTS)
    run_tests()
    fetch_report()
    cleanup_dirs()
    uninstall()
    print ' ---------------------- END ---------------------- ' + '\n'