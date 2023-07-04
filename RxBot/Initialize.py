from Settings import *
from subprocess import call
import urllib, urllib.request
import json
import socket
import os
import datetime
try:
    import xlsxwriter
    import xlrd
    import validators
except ImportError as e:
    print(e)
    raise ImportError(">>> One or more required packages are not properly installed! Run INSTALL_REQUIREMENTS.bat to fix!")
global settings, commandsFromFile


def initSetup():
    global settings, commandsFromFile

    # Create Folders
    if not os.path.exists('../Config'):
        buildConfig()
    if not os.path.exists('Resources'):
        os.makedirs('Resources')
        print("Creating necessary folders...")

    # Create Settings.xlsx
    settings = settingsConfig.settingsSetup(settingsConfig())
    filterConfig.filterSetup(filterConfig())  # Just set it up
    return


class runMiscControls:

    def __init__(self):
        self.timerActive = False
        self.timers = {}

    def formatTime(self):
        return datetime.datetime.today().now().strftime("%I:%M")  # This just formats the time as normal time, isnt used for timers but is used for console.

    def setTimer(self, name, duration):
        self.timerActive = True  # Set this to true so other code can check if theres an active timer
        curTime = datetime.datetime.now()  # Store the CURRENT TIME (When the timer was set)
        targetTime = curTime + datetime.timedelta(seconds=duration)  # Calculate the TARGET TIME, which is the current time PLUS however many seconds. Once the current time >= target time, timer is done.
        self.timers[name] = targetTime  # Record the timer in the dictionary for tick() to watch

    def timerDone(self, timer):
        self.timers.pop(timer)  # Timers done, remove the timer from the dict
        print(timer + " timer complete.")
        if not self.timers:  # If there are no more timers, set it to false
            self.timerActive = False


misc = runMiscControls()