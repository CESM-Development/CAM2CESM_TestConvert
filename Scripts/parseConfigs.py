#!/usr/bin/python

import sys
import os
import inspect
import re
import fnmatch

## Important paths
thisFile = os.path.realpath(inspect.getfile(inspect.currentframe()))
currDir = os.path.dirname(thisFile)
testDir = ''

## Regular expression for source files
fsrc = re.compile(r"\.F90(\.in)*$")

##############################
###
### Classes
###
##############################

class camConfig():
  def __init__(self):
    self.useMPI         = False
    self.useThreading   = True
    self.debug          = False
    self.physicsPackage = ''
    self.chemPackage    = ''
  # End def __init__
# End class camTest

##############################
###
### Helper Functions
###
##############################

def Usage ():
  print """
Usage: %s <CAM test dir>

  Parses the CAM master test list and produces input info for CESM equivalents

  """%(os.path.basename(thisFile))
# End Usage

def ParseConfigs (currpath):
  configs = list()
  for root, dirs, files in os.walk(currpath):
    for file in files:
      print file
    # End for
  # End for
  return configs
# End FindCAM


##############################
###
### Beginning of main program
###
##############################
if len(sys.argv) > 2:
  Usage()
  sys.exit(1)
else:
  testDir = sys.argv[1]
# End if
currdir=os.getcwd()
if os.path.exists(testDir):
  ## Parse system information
  configDir = os.path.join(testDir, "config_files")
  ParseConfigs(configDir)
else:
  print 'ERROR: CAM test directory not found'
  sys.exit(3)
# End if
