## No longer developed

## Description

Python script implementing continuous integration of Android applications
in Jenkins. It automatically builds, compiles and installs both application
and tests, run them and get results.

## Requirements
Android SDK with Platform-Tools (adb) (http://developer.android.com/sdk)
Android Emulator Plugin for Jenkins (if you are going to use emulator)
Python Plugin for Jenkins
Apache Ant (http://ant.apache.org)
android-junit-report (https://github.com/jsankey/android-junit-report)

## Installation
Change all necessary variables to fit your project and add to your android-junit-report.jar tests/lib/ directory.
Then just add build step of Python script and insert modified script.
More information on how to setup continuos integration of Android apps is available at
http://p0deje.blogspot.com/2011/03/continuos-integration-of-android-apps.html
