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

class CamConfig():
  def __init__(self, filename):
    self.name           = ''
    self.use_mpi         = False
    self.use_threading   = True
    self.debug          = False
    self.dycore          = ''
    self.hgrid           = ''
    self.physics_package = ''
    self.chem_package    = ''
    self.namelist_items = list()

    with open(filename) as f:
      self.name = os.path.basename(filename)
      for line in f:
        for entry in self.parse_options(line):
          if entry[0] == '-spmd':
            self.use_mpi = True
          elif entry[0] == '-nospmd':
            self.use_mpi = False
          elif entry[0] == '-smp':
            self.use_threading = True
          elif entry[0] == '-nosmp':
            self.use_threading = False
          elif entry[0] == '-dyn':
            self.dycore = self.entry_value(entry)
          elif entry[0] == '-res':
            self.hgrid = self.entry_value(entry)
          elif entry[0] == '-hgrid':
            self.hgrid = self.entry_value(entry)
          elif entry[0] == '-phys':
            self.physics_package = self.entry_value(entry)
          elif entry[0] == '-chem':
            self.chem_package = self.entry_value(entry)
          elif entry[0] == '-debug':
            self.debug = True
          elif entry[0] == '-s':
            # This is not relevant
            pass
          else:
            self.namelist_items.append(' '.join(entry))
          # End if
        # End for
      # End for
    # End with open

  # End def __init__

  def write_csv(self, f):
    csvlist = list()
    csvlist.append(self.quote_item(self.name))
    csvlist.append(self.quote_item(str(self.use_mpi).upper()))
    csvlist.append(self.quote_item(str(self.use_threading).upper()))
    csvlist.append(self.quote_item(str(self.debug).upper()))
    csvlist.append(self.quote_item(self.dycore))
    csvlist.append(self.quote_item(self.hgrid))
    csvlist.append(self.quote_item(self.physics_package))
    csvlist.append(self.quote_item(self.chem_package))
    csvlist.append(self.quote_item(' ' + ' '.join(self.namelist_items)))
    f.write(','.join(csvlist) + '\n')
  # End def write_csv

  def quote_item(self, item):
    return ''.join([ '"', item, '"' ])
  # End def quote_item

  def entry_value(self, entry):
    if len(entry) > 1:
      return ' '.join(entry[1:])
    else:
      raise NameError("config entry, %s, requires a value in %s"%
                      (entries[0], self.name))
    # End if
  # End def entry_value

  def parse_options(self, line):
    """ Turn different entries on a line into separate items
        Keep options with arguments together
        Return a list of options where each entry is a list
    """
    options = list()
    entries = [ s.strip() for s in line.split(' ') if len(s.strip()) > 0 ]
    while len(entries) > 0:
      if entries[0][0] == '-':
        opt = entries.pop(0)
        # We have an option, see if it takes a value
        if (len(entries) > 0) and (entries[0][0] != '-'):
          val = entries.pop(0)
          options.append([ opt, val ])
        else:
          options.append([ opt ])
        # End if
      else:
        # This shouldn't happen
        raise NameError("Bad config entry, %s, in %s"%(entries[0],self.name))
      # End if
    # End while
    return options
  # End def parse_options

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

def parse_configs (currpath):
  configs = list()
  for root, dirs, files in os.walk(currpath):
    for filename in files:
      if filename == 'testmech':
        continue
      else:
        configs.append(CamConfig(os.path.join(root,filename)))
      # End if
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
  test_dir = sys.argv[1]
# End if
currdir=os.getcwd()
if os.path.exists(test_dir):
  ## Parse system information
  configDir = os.path.join(test_dir, "config_files")
  configs = parse_configs(configDir)
  csvfilename = 'CamConfigs.csv'
  if os.path.exists(csvfilename):
    if os.path.exists(csvfilename + '~'):
      os.remove(csvfilename + '~')
    # End if
    os.rename(csvfilename, csvfilename + '~')
  # End if
  csvheaders = list()
  csvheaders.append("Name")
  csvheaders.append("Use MPI")
  csvheaders.append("Threading")
  csvheaders.append("Debug")
  csvheaders.append("dycore")
  csvheaders.append("hgrid")
  csvheaders.append("physics_package")
  csvheaders.append("chem_package")
  csvheaders.append("namelist_items")
  f = open(csvfilename, "w")
  f.write(','.join(csvheaders) + '\n')
  for config in configs:
    config.write_csv(f)
  # End for
  f.close()
else:
  print 'ERROR: CAM test directory not found'
  sys.exit(3)
# End if
