#!/usr/bin/env python
"""Watts Up? Pro/.Net meter logger (https://www.wattsupmeters.com).

This script reads meter values and saves the read data as CSV files.

Output format: CSV (comma separated values)
YYYY-MM-DD HH:MM:SS.ssssss, W, V, A, WH, Cost, WH/Mo, Cost/Mo, Wmax, Vmax, Amax, Wmin, Vmin, Amin, PF, DC, PC, HZ, VA

* Meters must be connected using USB and data can be collected and logged
  from multiple meters.
* Tested on Mac OS X and Linux using Python 2.7 using Watts Up? .Net meters.
* FTDI drivers may need to be installed. (http://www.ftdichip.com/Drivers/VCP.htm)
* Usage: "wattsup.py -h" for help.

Author: Yongpil Yoon
Copyright: Yongpil Yoon 2015
Version: 0.1.0
License: GPLv3

  This program is free software: you can redistribute it and/or
  modify it under the terms of the GNU General Public License as
  published by the Free Software Foundation, either version 3 of the
  License, or (at your option) any later version.  A copy of the GPL
  version 3 license can be found in the file COPYING or at
  <http://www.gnu.org/licenses/>.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
"""

import argparse
import time
import datetime
import fnmatch
import os
import sys
import serial
from platform import uname
import multiprocessing

class WattsUp(object):
  """WattsUp meter class"""

  def __init__(self, port, interval, duration):
    """__init__
    Keyword arguments:
    port -- the serial port (e.g. /dev/ttyUSB0)
    interval -- the sampling interval in seconds
    duration -- the sampling duration in minutes
    """
    self.serialPort = serial.Serial(port, 115200)
    self.interval = interval
    self.duration = int(float(duration) * 60) # duration in seconds
    self.logfile = None
    self.name = port[5:] # 

  
  def getRawLine(self):
    """Return the read values as a list"""
    line = self.serialPort.readline()
    fields = line.split(',')
    return fields

  def getFormattedLine(self):
    """Return the read values in appropriate formats as a list"""
    fields = self.getRawLine()
    if len(fields) != 21:
      fields = self.getRawLine()
    #format
    fields[3] = str(int(fields[3]) / 10.0)
    fields[4] = str(int(fields[4]) / 10.0)
    fields[5] = str(int(fields[5]) / 1000.0)
    fields[6] = str(int(fields[6]) / 10.0)
    fields[7] = str(int(fields[7]) / 1000.0)
    fields[8] = str(int(fields[8]) / 10.0)
    fields[9] = str(int(fields[9]) / 1000.0)
    fields[10] = str(int(fields[10]) / 10.0)
    fields[11] = str(int(fields[11]) / 10.0)
    fields[12] = str(int(fields[12]) / 1000.0)
    fields[13] = str(int(fields[13]) / 10.0)
    fields[14] = str(int(fields[14]) / 10.0)
    fields[15] = str(int(fields[15]) / 1000.0)
    # fields[16] = fields[16]
    # fields[17] = fields[17]
    # fields[18] = fields[18]
    fields[19] = str(int(fields[19]) / 10.0)
    fields[20] = str(int(fields[20].replace(';\r\n', '')))
    return fields

  def log(self, rawOutput, logfilePrefix):
    """Prints the read valuse on stdout and saves as CSV files
    Keyword arguments:
    rawOutput -- (bool) saves raw output if True
    logfilePrefix -- (str) prefix of logfile name
    """
    try:
      self.serialPort.write('#L,W,3,E,,%d;' % self.interval)
      elapsedTime = 0
      logfile = open(logfilePrefix + self.name + '.csv', 'w')
      logfile.write('Time, W, V, A, WH, Cost, WH/Mo, Cost/Mo, Wmax, Vmax, Amax, Wmin, Vmin, Amin, PF, DC, PC, HZ, VA\n')
      while True:
        if elapsedTime > self.duration:
          break

        if rawOutput:
          fields = self.getRawLine()
        else:
          fields = self.getFormattedLine()

        if len(fields) != 21:
          continue

        logfile.write('%s' % datetime.datetime.now())
        for i in range(3, len(fields)):
          logfile.write(', %s' % fields[i])
        logfile.write('\n')

        print ' duration: ' + str(self.duration) + ' elapsedTime: ' + str(elapsedTime)
        print self.name + ':', fields

        elapsedTime += self.interval

      try:
        logfile.close()
      except:
        pass
      self.serialPort.close()
    except KeyboardInterrupt:
      try:
        logfile.close()
      except:
        pass
      self.serialPort.close()
      print '\nKeyboardInterrupt in logger, saving log file for: ', logfile.name
      # close file

def scanPorts():
  """Return (list of str) paths to serial port device files"""
  system = uname()[0]
  fileName = 'tty.usbserial-*' if system == 'Darwin' else ('ttyUSB*' if system == 'Linux' else '')

  if fileName == '':
    print '\nThis operating system is not supported!'
    exit(1)

  ports = []

  for file in os.listdir('/dev'):
    if fnmatch.fnmatch(file, fileName):
      ports.append('/dev/' + file)

  if len(ports) == 0:
    print '\nWatts Up? meter not found!'
    print '* Please connect your meters.'
    print '* FTDI drivers have to be installed. (http://www.ftdichip.com/Drivers/VCP.htm)'
    print '* Run', str(__file__).split('/')[-1], '--help (-h) for help\n'
    exit(1)

  return ports

def checkPorts(ports):
  """Return (bool) True if the given ports exist
  Keyword arguments:
  ports - (list of str) paths to serial port device files
  """
  result = True
  for port in ports:
    if not os.path.exists(port):
      print 'Error: Port does not exist: ' + port
      result = False
  return result


def main(args, parser):
  """main function
  Starts logging according to the given options (command line arguments).
  Keyword arguments:
  parser -- argparse parser
  """
  # check ports
  if type(args.ports) is not list:
    args.ports = scanPorts()
  elif not checkPorts(args.ports):
    sys.exit(1)

  if not args.auto:
    # Confirm if the options are right
    print 'Metres:', args.ports
    print 'Logging duration:', args.duration, 'minute(s)'
    print 'Reading interval:', args.interval, 'second(s)'
    print 'Logfilename prefix:', args.prefix
    print 'Log raw data:', args.raw
    sys.stdout.write('Are the above options correct (Y/n)? ')
    selection = raw_input()
    if selection.lower() == 'n':
      print ''
      parser.print_help()
      sys.exit(0)

  # Create WattsUp objects and processes (logger)
  loggers = []
  for port in args.ports:
    metre = WattsUp(port, args.interval, args.duration)
    logger = multiprocessing.Process(target=metre.log, args=(args.raw, args.prefix,))
    loggers.append(logger)
    # logger.start()

  # Start logger processes
  for logger in loggers:
    logger.start()

  # KeyboardInterrupt
  try:
    for logger in loggers:
      logger.join()
  except KeyboardInterrupt:
      print 'Quitting...'


if __name__ == '__main__':
  # Parse command line arguments
  parser = argparse.ArgumentParser(description='Get readings from Watts Up? meters in real time (through USB) and save them to files.')
  parser.add_argument('-p', '--ports', dest='ports', nargs='+', type=str, help='USB port(s) e.g. /dev/ttyUSB0 /dev/ttyUSB1 ..')
  parser.add_argument('-t', '--time', dest='duration', default=0.5, help='Duration of logging in minutes (default 0.5 minute)')
  parser.add_argument('-i', '--interval', dest='interval', default=1, type=int, help='Reading interval in seconds (default 1 second)')
  parser.add_argument('-o', '--outfile-prefix', dest='prefix', default='WU-' + datetime.date.today().isoformat(), help='Prefix of output files')
  parser.add_argument('-r', '--raw', dest='raw', action='store_true', default=False, help='Save raw data')
  parser.add_argument('-a', '--auto', dest='auto', action='store_true', default=False, help='Start logging without confirmation')
  args = parser.parse_args()
  try:
    main(args, parser)
  except KeyboardInterrupt:
    print '\nQuitting...'



