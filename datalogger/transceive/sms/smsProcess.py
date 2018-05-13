#!/usr/bin/env python

import re
import subprocess
import os
import mmap

# Load environment variables
execfile("/KWH/datalogger/config/pyvars.py")
DEBUG = int(DEBUG)
smsPath = "/KWH/datalogger/transceive/sms"

# Setup regex and paths to command scripts
delPath =smsPath+"/smsDel.sh"
sendPath = smsPath+"/smsSend.sh"
commandList = []
################################################################################
admpwPath = smsPath+"/commands/ADMPW.sh"
admpw = re.compile(r"(.*?)#ADM:(.*?)()#")
commandList.append(admpw)
################################################################################
adxxPath = smsPath+"/commands/ADxx.sh" 
adxx = re.compile(\
r"(.*?)#ADN(0\d):([0-1])(,\d.\d{3},\d.\d{3},\d.\d{3},\d.\d{3},\d.\d{3},[0,1]{4},[0-3]{6})*?#")
commandList.append(adxx)
################################################################################
apnPath = smsPath+"/commands/APN.sh" 
apn = re.compile(r"(.*?)#GAN:(.*?)()\!#") 
commandList.append(apn)
################################################################################
debugPath = smsPath+"/commands/DEBUG.sh" 
debug = re.compile(r"(.*?)#DBG:([0-1])()#")
commandList.append(debug)
################################################################################
domainPath = smsPath+"/commands/DOMAIN.sh" 
domain = re.compile(r"(.*?)#GDN:([A-z\.]*)()\!#") 
commandList.append(domain)
################################################################################
inqE2Path = smsPath+"/commands/inqE2.sh" 
inqE2 = re.compile(r"(.*?)#E2#") 
commandList.append(inqE2)
################################################################################
inqEEPath = smsPath+"/commands/inqEE.sh" 
inqEE = re.compile(r"(.*?)#EE#") 
commandList.append(inqEE)
################################################################################
portPath = smsPath+"/commands/PORT.sh" 
port = re.compile(r"(.*?)#GIP:(\d{1,5})()#") 
commandList.append(port)
################################################################################
puxxPath = smsPath+"/commands/PUxx.sh" 
puxx = re.compile(r"(.*?)#DIN([1-8]):([0-4]),[0-1]{4},[0-3]{6}#") 
commandList.append(puxx)
################################################################################
puxxValPath = smsPath+"/commands/PUxxVal.sh" 
puxxVal = re.compile(r"(.*?)#DIP([1-8]):(\d*)#") 
commandList.append(puxxVal)
################################################################################
resetPath = smsPath+"/commands/RESET.sh" 
reset = re.compile(r"(.*?)#RESET#") 
commandList.append(reset)
################################################################################
staPath = smsPath+"/commands/STA.sh" 
sta = re.compile(r"(.*?)#BST:(.*?)()#") 
commandList.append(sta)
################################################################################
invalid = re.compile(r"(.*?)#")
commandList.append(invalid)
################################################################################
catchAll = re.compile(r".*")
commandList.append(catchAll)
################################################################################

# NOTE: msg[0] = message number, msg[1] = phone number, msg[2] = the message
def process(options, commandFile, msg):
    if DEBUG: print("Set "+options[0])

    # Check password
    if match.group(1) == ADMPW:
        if DEBUG: print("Password match")

        # Commands with more than two values as part of the update request processed here
	if match.group(3) <> '':
                # Special case for Pulse enable response formatting
                if options[0] == "PU0":
                    if DEBUG: print("Setting "+options[0]+match.group(2)+" to: "+match.group(3))
                    p = subprocess.Popen([commandFile, str(match.group(2)), str(match.group(3))])
                else:
                    if DEBUG: print("Setting "+options[0]+" "+match.group(2)+" to: "+match.group(3))
                    p = subprocess.Popen([commandFile, str(match.group(2)), str(match.group(3))])
        # Commands with a single value processed here
	else:
                if DEBUG: print("Setting "+options[0]+" to: "+match.group(2))
        	p = subprocess.Popen([commandFile, str(match.group(2))])

        # Wait until complete to start delete process
        p.communicate()
        if p.returncode == 0:
            if DEBUG: print(options[0]+" set success")
            if DEBUG: print("Deleting sms #"+msg[0])
            p = subprocess.Popen([delPath, msg[0]])
            p.communicate()
            if p.returncode == 0:
                if DEBUG: print("Delete success")
            else:
                if DEBUG: print("Delete failed")
            if DEBUG: print("Executing: "+sendPath+" "+msg[1]+" "+options[0]+" set to: "+match.group(2))

            # Commands with more than two values as part of the update request processed here
	    if match.group(3) <> '':
                # Special case for Pulse enable response formatting
                if options[0] == "PU0":
                    p = subprocess.Popen([sendPath, msg[1], str(options[0])+str(match.group(2))+" set to: "+str(match.group(3))])
                else:
                    p = subprocess.Popen([sendPath, msg[1], str(options[0])+" "+str(match.group(2))+" set to: "+str(match.group(3))])

            # Commands with a single value processed here
	    else:
                p = subprocess.Popen([sendPath, msg[1], str(options[0])+" set to: "+str(match.group(2))])

            p.communicate()
    else:
        if DEBUG: print("Wrong password")
        if DEBUG: print("Deleting sms #"+msg[0])
        p = subprocess.Popen([delPath, msg[0]])
        p.communicate()
        if p.returncode == 0:
            if DEBUG: print("Delete success")
        else:
            if DEBUG: print("Delete failed")



##### MAIN #####
# smsParse.py reads all sms into individual files in smsPath/msg director
# This puts them all into an array in message numerical order
messages = os.listdir(smsPath+"/msg")
messages.sort()
# Regex to get message #, phone #, and msg data from each message
messageData = re.compile(r"\+CMGL: (\d*),.*?,(.*?),.*?,.*?\n(.*)")
# This array will be populated with the msg(s) that each have the 3 regex groups
msgList = []

if DEBUG: print messages
for msg in messages:
    # Exclude the .gitMarker file that is only there so GitHub will retain the directory
    if str(msg) <> ".gitMarker":
        if DEBUG: print smsPath+"/msg/"+str(msg)
        f = open(smsPath+"/msg/"+str(msg), 'r+')
        msgData = mmap.mmap(f.fileno(), 0)
        parts = messageData.search(msgData)
        msgList.append([parts.group(1), parts.group(2).replace('"', ''), parts.group(3)])
        if DEBUG: print msgList
        f.close()


for msg in msgList:
    found = False
    for command in commandList:
        match = command.search(msg[2]) 
        if match and not found:
	    found = True
            # Execute the appropriate processing file
            if command == reset:
                process(["Reset"], resetPath, msg)
            elif command == admpw:
                process(["Admin Password"], admpwPath, msg)
            elif command == sta:
		process(["Station ID"], staPath, msg)
            elif command == debug:
		process(["Debug"], debugPath, msg)
            elif command == domain:
		process(["Server Domain"], domainPath, msg)
            elif command == port:
		process(["Server Port"], portPath, msg)
            elif command == apn:
		process(["APN"], apnPath, msg)
            elif command == puxx:
		process(["PU0"], puxxPath, msg)
            elif command == puxxVal:
                process(["Pulse Channel"], puxxValPath, msg)
            elif command == adxx:
		process(["Analog Channel"], adxxPath, msg)
            elif command == inqE2:
		process([""], inqE2Path, msg)
            elif command == inqEE:
		process([""], inqEEPath, msg)
            elif command == invalid:
	        if match.group(1) == ADMPW:
                    p = subprocess.Popen([sendPath, msg[1], "Command not valid"])
		    p.communicate()
                    p = subprocess.Popen([delPath, msg[0]])
		    p.communicate()
                    if DEBUG: print("Deleting invalid message with correct password")
	    elif command == catchAll:
                p = subprocess.Popen([delPath, msg[0]])
                p.communicate()
                if DEBUG: print("Deleting invalid message without correct password")
