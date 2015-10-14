#!/usr/bin/env python2
import logging
import argparse

import sphero_opencv
import sphero_tactics



#Logging
# create logger
logger = logging.getLogger("sphero")
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

#ArgParse
parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("-v", "--verbosity", action="count", default=0)
group.add_argument("-q", "--quiet", action="store_true")

parser.add_argument("-s", "--stat", help="n")
parser.add_argument("-d", "--disable", action="store_true", help="")
parser.add_argument("-c", "--config", action="store_true", help="start Config Mode")
args = parser.parse_args()

#Arg Disable Logging
if args.quiet:
    ch.setLevel(logging.ERROR)

#Arg verbosity
if args.verbosity >= 2:
    ch.setLevel(logging.DEBUG)
if args.verbosity == 1:
    ch.setLevel(logging.INFO)
if args.verbosity == 0:
    ch.setLevel(logging.WARNING)


#Start Threads
#OpenCv Thread. Exit cvThread.threadExit = True
cvThread = sphero_opencv.Opencv(kwargs={'config': args.config})
cvThread.setDaemon(True)

#If config mode
if args.config:
    cvThread.openCVconfig()
else:
    cvThread.start()
    #Start Tactics
    tactic = sphero_tactics.Tactics(kwargs={'openCv': cvThread})
    tactic.run()

    #Exit cvThread
    cvThread.threadExit = True


#Exit - Send Exit to Threads
logger.info("Warte auf Threads to Exit")
#Wait for Threads to exit
if cvThread.isAlive():
    cvThread.join(10)
print("Exit")
