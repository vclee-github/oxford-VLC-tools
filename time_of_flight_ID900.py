#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description: Run a Time of Flight histogram acquisition, saves the timestamps, and plot the histograms for channels 1-4 on ID900 Time Controller.

author = Vincent Lee
email = vincent.lee@eng.ox.ac.uk
status = revision 1

"""

# Check that packages below (zmq, subprocess, psutil) are installed.
# Install the missing packages with the following command in an instance of cmd.exe, opened as admin user.
#   python.exe -m pip install "name of missing package"

# Python modules needed
import os
import sys
import time
import socket
import fileinput
import zmq
import subprocess
import psutil
import matplotlib.pyplot as plt
import numpy as np

#################################################################
#################   TO BE FILLED BY USER   ######################
#################################################################

# executables_path is the folder location of the "DataLinkTarget.Service.exe"
# executable on your computer. Once the GUI installed, you should find it there:
executables_path = r"C:\Program Files\IDQ\Time Controller\packages\ScpiClient"

# IP address of the ID900 
ID900_IP = "169.254.101.129"

# data_folder is the folder location where you want to store your timestamps files
data_folder = r"C:\Users\wolf4891\Documents\ID900-1908029T010\Timestamps"

# Acquisition time in seconds
acquisition_time = 1
#32.8 us is max time limit for HR acquisition in GUI.

# Channels on which timestamps are acquired (possible range: 1-4)
channels = [1,2,3,4]

#################################################################
####################   UTILS FUNCTIONS   ########################
#################################################################

def check_host(address, port):
    s = socket.socket()
    s.settimeout(5)
    try:
        s.connect((address, port))
        s.settimeout(None)
        return True
    except socket.error as e:
        return False

def error(message):
    print('Error: ' + message)
    exit(1)

def zmq_exec(zmq, cmd):
    print(cmd)
    zmq.send_string(cmd)
    ans = zmq.recv().decode('utf-8')
    if ans: print('>', ans)
    return ans


def plot_hist(input_ch):
    # Get histogram data
    histogram = eval(zmq_exec(tc, "TSST{}:DATA:HISTO?".format(input_ch)))
    bin_min   = eval(zmq_exec(tc, "TSST{}:HISTO:MIN?".format(input_ch))[:-2])
    bin_width = eval(zmq_exec(tc, "TSST{}:HISTO:BWID?".format(input_ch))[:-2])

    # Compute bins time and filter empty bins to speedup plot rendering
    #You are making .keys() here called 'bin' for the dictionary 'bins'.
    bins = { bin_min + i * bin_width: bin     for i, bin in enumerate(histogram) if bin != 0 }

    # Plot bins
    fig, ax = plt.subplots(1)
    fig.suptitle('Histogram {}'.format(input_ch), fontsize=16) 
    plt.xlabel('ps')
    plt.xlim(0, bin_min + len(histogram) * bin_width)
    plt.ylabel('Number of Photons')
    plt.ylim(0, max(bins.values()))
    plt.stem(list(bins.keys()), list(bins.values()), markerfmt=" ", basefmt=" ")  
    #Must omit linefmt, but keep markerfmt=' ' and basefmt=' ' to makes bar graphs. 
    #These make the top and bottom flat and without the usual line and dot for stem plots.
    #plt.stem(list(bins.keys()), list(bins.values()))   #Usual line and dot for stem plots. But unreadable for histograms.


def query_hist(input_ch):
    #Get histogram data (y values only)
    global hist_query, num_bins_query
    hist_query = eval(zmq_exec(tc, "TSST{}:DATA:HISTO?".format(input_ch)))
    #eval(zmq_exec(tc, "HIST{}:DATA?".format(input_ch))) #This performs the same thing
    num_bins_query = len(hist_query)
    print('Histogram {} number of bins = '.format(input_ch),num_bins_query)
    return hist_query, num_bins_query


def out_ch1(state):
    zmq_exec(tc, "TSGE1:MODE SPUL;:TSGE1:ENAB ON;TRIG:MODE INTERNAL;DELAY 0;INTER:PER 24000;:TSGE1:SPUL:PWID 6000")  #24ns period and 6ns pulse
    zmq_exec(tc, "OUTP1:DELA 0;ENAB {};INPO:LINK TSCO9;:OUTP1:MODE NIM".format(state))  

def out_ch2(state):
    zmq_exec(tc, "TSGE2:MODE SPUL;:TSGE2:ENAB ON;TRIG:MODE INTERNAL;DELAY 0;INTER:PER 24000;:TSGE2:SPUL:PWID 6000")  #24ns period and 6ns pulse
    zmq_exec(tc, "OUTP2:DELA 0;ENAB {};INPO:LINK TSCO10;:OUTP2:MODE NIM".format(state))

def out_ch3(state):
    zmq_exec(tc, "TSGE3:MODE SPUL;:TSGE3:ENAB ON;TRIG:MODE INTERNAL;DELAY 0;INTER:PER 24000;:TSGE3:SPUL:PWID 6000")  #24ns period and 6ns pulse
    zmq_exec(tc, "OUTP3:DELA 0;ENAB {};INPO:LINK TSCO11;:OUTP3:MODE NIM".format(state))

def out_ch4(state):
    zmq_exec(tc, "TSGE4:MODE SPUL;:TSGE4:ENAB ON;TRIG:MODE INTERNAL;DELAY 0;INTER:PER 24000;:TSGE4:SPUL:PWID 6000")  #24ns period and 6ns pulse
    zmq_exec(tc, "OUTP4:DELA 0;ENAB {};INPO:LINK TSCO12;:OUTP4:MODE NIM".format(state))


#################################################################
###################   WORK HAPPENS HERE   #######################
#################################################################

ID900_PORT = 5555
ID900_ADDR = 'tcp://' + ID900_IP + ':' + str(ID900_PORT)

# Check that the target folder exists
if not os.path.isdir(data_folder):
    error('Data folder "' + data_folder + '" does not exist.')

# Check that the executables folder exists
if not os.path.isdir(executables_path): 
    error('Path to the executables folder "' + executables_path + '" does not exist.')

# Check if ID900 is listening
if not check_host(ID900_IP, ID900_PORT):
    error('Unable to connect to ID900 "' + ID900_IP + '" on port ' + str(ID900_PORT) + '.')

# Check that the DataLink service is not already running
running_processes = set([psutil.Process(proc.pid).name() for proc in psutil.process_iter()])
if "DataLinkTarget.Service.exe" in running_processes:
    error("DataLinkTarget.Service.exe is already running!\nPlease close the GUI if it's running or, otherwise, end this process manually in the Task Manager.")

# Build Datalink log configuration file
script_path = os.path.dirname(os.path.realpath(__file__))
log_path = script_path if (script_path[-1] == "/") or (script_path[-1] == "\\") else script_path + "/"
with open("DataLinkTargetService.log.conf", "w") as logConfFile:
    for line in open(os.path.join(executables_path, r"config\DataLinkTargetService.log.conf"), "r"):
        logConfFile.write(line.replace("log4cplus.appender.AppenderFile.File=", "log4cplus.appender.AppenderFile.File=" + log_path))

# Launch partner executables
datalink_service = subprocess.Popen([executables_path + r"\DataLinkTargetService.exe", "-f", data_folder, "--logconf", os.path.join(script_path, "DataLinkTargetService.log.conf")])

# Create zmq socket and connect to the ScpiClient
context = zmq.Context()
tc = context.socket(zmq.REQ)
tc.connect(ID900_ADDR)

# Create zmq socket and connect to the DataLink
datalink = context.socket(zmq.REQ)
datalink.connect("tcp://localhost:6060")

# Configure the acquisition timer
zmq_exec(tc, "TSGE8:ENAB OFF")
zmq_exec(tc, "TSGE8:ONES:PWID %d" % (acquisition_time * 1e12))  #Makes format in picoseconds. Can also use TB which is 1 ps. 3000 GTB = 3000 Giga Time Base = 3 seconds.

for channel in channels:
    # Reset error counter
    zmq_exec(tc, "TSST{}:DATA:RAW:ERRORS:CLEAR".format(channel))
   #TSSTatistic1-4 (TSST1-4) is for Channels 1-4 to acquire histogram and timestamp data.

    # Tell the DataLink to start listening and store the timestamps in text format.
    # Command: activate <channel> <id900 ip> <port> <filename> <format>
    #    channel:  Choose on between 1 to 4
    #    port:     5556 for channel 1
    #              5557 for channel 2
    #              5558 for channel 3
    #              5559 for channel 4
    #    filename: Any name without spaces
    #    format:   Choose between "acsii" and "bin"
    port = 5555 + channel
    zmq_exec(datalink, "activate {0} {1} {2} timestamps_C{0}.txt ascii".format(channel, ID900_IP, port))  #String place holders format: 0=channel, 1=IP, 2=port

    # Start transfer of timestamps (All within one acquisition time?)
    zmq_exec(tc, "TSST{}:DATA:RAW:SEND ON".format(channel))
    #zmq_exec(tc, "RAW{}:SEND ON".format(channel)) #This performs the same thing

#------------Now all timestamps will be saved to their new files------------#

#zmq_exec(tc, "".format(channel))

# Configure histogram parameters
for channel in channels:

    #TSSTatistic1-4 (TSST1-4) is for Channels 1-4 to acquire histogram and timestamp data.
    #zmq_exec(tc, "".format(channel))

    #Clear histograms
    zmq_exec(tc, "TSST{}:DATA:HISTO:FLUSh".format(channel))
    
    #Set Bin width to 2ns (2000ps), Max bin count = 16384 (3.2768e7 ps or 32.768 us)
    #zmq_exec(tc, "HIST{0}:BCOU 16384;BWID 2000;INPO:ENAB:LINK TSGE8;:HIST{1}:MIN 0".format(channel,channel))
    zmq_exec(tc, "HIST{0}:BCOU 500;BWID 2000;INPO:ENAB:LINK TSGE8;:HIST{1}:MIN 0".format(channel,channel))


# Histogram start/stop channels
    #Ref Channel (Trigger) = TSCO5-8 . This channel will trigger the Stop Channel to start timestamping
    #Stop Channel = TSCO5-8 . This is the channel you want to send timestamps for histogram   
    #Channel 1 = TSCO 5
    #Channel 2 = TSCO 6
    #Channel 3 = TSCO 7
    #Channel 4 = TSCO 8

hist1_start = 7
hist1_stop = 5
zmq_exec(tc, "HIST1:INPO:REF:LINK TSCO{0};:HIST1:INPO:STOP:LINK TSCO{1}".format(hist1_start,hist1_stop))

hist2_start = 6
hist2_stop = 5
zmq_exec(tc, "HIST2:INPO:REF:LINK TSCO{0};:HIST2:INPO:STOP:LINK TSCO{1}".format(hist2_start,hist2_stop))

hist3_start = 5
hist3_stop = 6
zmq_exec(tc, "HIST3:INPO:REF:LINK TSCO{0};:HIST3:INPO:STOP:LINK TSCO{1}".format(hist3_start,hist3_stop))    

hist4_start = 7
hist4_stop = 6
zmq_exec(tc, "HIST4:INPO:REF:LINK TSCO{0};:HIST4:INPO:STOP:LINK TSCO{1}".format(hist4_start,hist4_stop))    

# Configure inputs
for channel in channels:
    #Set up idles
    zmq_exec(tc, "DELA{0}:INPO:LINK INPU{1};:DELA{2}:VALU 0".format(channel, channel, channel))
    
    #Set up inputs (Detection 1 port on SPAD, LVTTL, Rising Edge, 1V)
    zmq_exec(tc, "INPU{0}:COUN:INTE 1000;MODE CYCL;:INPU{1}:COUP DC;EDGE RISI;ENAB ON;MODE HIRES;RESY AUTO;SELE UNSH;THRE 1V".format(channel, channel))


# Turn off output channels 1-4
out_ch1('off')
out_ch2('off')
out_ch3('off')
out_ch4('off')

# Start the acquisition timer 
zmq_exec(tc, "TSGE8:ENAB ON")  #HIST and RAW can be used with ENABLE ON with TSGE8 only. TSGE8 specifies start/stop duration of acquisition. 
#Once this step is done (i.e., enable TSGE8) you can query histogram and raw data. ID900 automatically takes histogram within TSGE8 pulsewidth duration.

# Turn on output channels 1-4 for modulation
out_ch1('off')
out_ch2('off')
out_ch3('off')
out_ch4('on')


# Wait for the desired time plus some margin
time.sleep(acquisition_time + 0.1)

# Finish transfer of timestamps
for channel in channels:
    zmq_exec(tc, "TSST{}:DATA:RAW:SEND OFF".format(channel))
    #zmq_exec(tc, "RAW{}:SEND OFF".format(channel)) #This performs the same thing

# Wait a while to let the DataLink receive the remaining timestamps
time.sleep(1)

# Tell the DataLink to stop listening
for channel in channels:
    zmq_exec(datalink, "disactivate {}".format(channel))

# Check if data was lost while transmitting the timestamps
for channel in channels:
    errors = int(zmq_exec(tc, "TSST{}:DATA:RAW:ERRORS?".format(channel)))
    if errors > 0:
        print("Warning: A data loss occured. Saved timestamp values may be wrong on channel", channel)

# Stop partner executables
datalink_service.terminate()

# Plot Histograms
#plot_hist(1)
plot_hist(2)
plot_hist(3)
#plot_hist(4)

# Query histogram data points
#query_hist(1)
query_hist(2)
#query_hist(3)
#query_hist(4)