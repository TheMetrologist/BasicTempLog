#!/bin/Python3
#   Tested with Python3.4 on Raspbian Stretch (RPi3 platform)
#
#///////////////////////////////////////////////////////////////////////////////
## BasicTempLog.py Notes
#   Authored by: Michael Braine, Physical Science Technician, NIST, Gaithersburg, MD
#       PHONE: 301 975 8746
#       EMAIL: michael.braine@nist.gov (use this instead of phone)
#
#   Purpose
#       continuously read temperature from voltage sensing circuit on a portable platform (RPi3)
#
#///////////////////////////////////////////////////////////////////////////////
## References
#   - RPi3 GPIO mapping
#
#///////////////////////////////////////////////////////////////////////////////
## Change log from v1.000 to v1.000
#   November 9, 2017
#
#   ver 1.000 - modified from StrangEnvironment/environment_monitor.py v1.053
#
#///////////////////////////////////////////////////////////////////////////////

## Used libraries
import serial, os, time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

## Variables
print('\nBasic Temperature Logging System, v1.000\n\nMichael Braine, November 2017\nmichael.braine@nist.gov\n')
pts_per_hr = 120                                                                #number of points per hour, default is 2 pt/min
graph_time = 12                                                                 #length of time to graph into past, hours, default is 12 hours
tick_spacing = 20                                                               #number of points between each x-axis tickmark
graph_pts = round(graph_time*pts_per_hr)                                        #maximum number of recent points to plot
sleeptimer = (pts_per_hr / 60 / 60)**-1                                         #amount of time for system to wait until next temperature, seconds
#define probes
probe_T_matl = np.array([5,9,10])
probe_T_air = np.array([])
scan_CH = np.append(probe_T_matl, probe_T_air)
dpi_set = 186                                                                   #display pixels per inch for 27", 1920x1080 display
colorvec = ['r','b','g','c','m','y']

## Set up file directories and file dependencies
# correctionsfile = '/home/pi/BasicTempLog/corrections.csv'                       #location of corrections and gradients
envdatadir = '/home/pi/Desktop/EnvironmentData/'                                #where data will be stored

## Navigate to and load Hart160 corrections and gradients
# Tcorr_file = np.genfromtxt(correctionsfile, skip_header=1, delimiter=',', dtype=(int,float,float), autostrip=True) #load corrections, corrections[channel][1] is slope, corrections[channel][2] is intercept
# Tcorr_slope = np.zeros((len(Tcorr_file)), dtype=float)                          #initialize corrections with zeros
# Tcorr_intercept = np.zeros((len(Tcorr_file)), dtype=float)                      #initialize corrections with zeros
# for n in range(len(Tcorr_file)):                                                #parse slope and intercepts
    # Tcorr_slope[n] = Tcorr_file[n][1]                                           #slope
    # Tcorr_intercept[n] = Tcorr_file[n][2]                                       #intercept

## Connect to Hart 1560 temperature system
hart1560_obj = serial.Serial(timeout=2)                                         #create serial port connection object with 2 second timeout
hart1560_obj.baudrate = 9600                                                    #set baudrate, default = 9600
hart1560_obj.linefeed = 'on'                                                    #set linefeed, default = on
hart1560_obj.duplex = 'half'                                                    #set duplex, default = half
hart1560_obj.port = '/dev/ttyUSB0'
hart1560_obj.open()
hart1560_obj.read(100)                                                          #clear buffer

# temperature measurement
def ReadTemperature():                                                          #read temperature from active channel
    fetch_str = 'MEAS? (@'+str(scan_CH[n])+')'                                  #build string for Hart1560 command
    fetch_str = fetch_str.encode('UTF-8')+b'\n'                                 #add newline character to string and convert to binary
    hart1560_obj.write(fetch_str)                                               #pass command to Hart1560
    time.sleep(0.5)                                                             #pause before reading
    try:
        temptemp = float(hart1560_obj.read(100))
    except Exception:
        time.sleep(0.5)
        hart1560_obj.read(100)
        time.sleep(0.5)
        hart1560_obj.write(fetch_str)                                           #pass command to Hart1560
        temptemp = float(hart1560_obj.read(100))
    return temptemp                                                             #read Hart1560 buffer

alltemps = []
print('\nTesting connection')
for n in range(len(scan_CH)):
    alltemps.append(ReadTemperature())                                          #test read of Hart1560
print('\n\t\t Hart 1560 status:\tCONNECTED')

overwrite = False
again = True
while again:
    print('\n')
    filename = input('Filename for data? The name will be automatically appended with the .env.csv extension: ')
    if os.path.isfile(envdatadir+filename+'.env.csv'):
        aot = print('Filename '+filename+' exists in '+envdatadir+'.')
        understand = False
        while not(understand):
            aot = input('Do you want to [a]ppend, [o]verwrite, or [t]ry another filename? (a/o/t): ')
            if (aot.lower() == 'a') or (aot.lower() == 'append'):
                print('\n\nData will be appended to: '+envdatadir+filename+'\n')
                understand = True
                overwrite = False
                again = False
            elif (aot.lower() == 'o') or (aot.lower() == 'overwrite'):
                print('\n\nData in this file will be overwritten: '+envdatadir+filename+'\n')
                understand = True
                overwrite = True
                again = False
            elif (aot.lower() == 't'):
                print('\nVery well.\n')
                understand = True
                overwrite = False
                again = True
            else:
                print('\nNot a valid responnse. Try again.\n')
                understand = False
                overwrite = False
                again = True
    else:
        print('\n\nA new file will be written to: '+envdatadir+filename+'\n')
        again = False

print('\nLog and graph commencing...\nGathering initial data...\n\nPlease wait, graph takes a moment to display.')
CH = {}
alltemps = []
ti = time.time()                                                                #begin timer------------------------------------------
## First measurement to populate variable
for n in range(len(scan_CH)):
    if n == 0:
        currenttime = time.strftime("%Y-%m-%d %H:%M:%S")                        #get current system time (yyyy mm dd hh mm ss)
        CH.update({'time':[currenttime]})
    temperature = ReadTemperature()                                             #measure temperature
    # temperature = (temperature - Tcorr_intercept[scan_CH[n]-1]) / Tcorr_slope[scan_CH[n]-1] #calculate corrected temperature
    CH.update({scan_CH[n]:[temperature]})
    alltemps.append(temperature)

tf = time.time()                                                                #stop timer------------------------------------------
if sleeptimer-(tf-ti) > 0:
    time.sleep(sleeptimer-(tf-ti))                                              #sleep for sleeptimer less time taken for above lines
truncate = False

print('Do not close terminal window or iPython plot.\n')

## Figure setup
plt.ion()
fig = plt.figure(num=1, figsize=(4.2,2.2), dpi=dpi_set)                         #get matplotlib figure ID, set figure size
# fig = plt.figure(num=1, figsize=(21.5,11.25), dpi=dpi_set)
gs = gridspec.GridSpec(1,1)
gs.update(hspace=0.05)
ax1 = plt.subplot(gs[0,:])
fig.subplots_adjust(left=0.06, right=1, top=0.98, bottom=0.14)
fig.canvas.toolbar.pack_forget()

## Read temperatures for all eternity
while True:
    ti = time.time()                                                            #begin/reset timer------------------------------------------
    #measure temperature on all channels
    for n in range(0, len(scan_CH)):
        if n == 0:
            currenttime = time.strftime("%Y-%m-%d %H:%M:%S")                    #get current system time (yyyy mm dd hh mm ss)
            CH['time'] = np.append(CH['time'], currenttime)
        temperature = ReadTemperature()                                         #measure temperature
        # temperature = (temperature - Tcorr_intercept[scan_CH[n]-1]) / Tcorr_slope[scan_CH[n]-1] #calculate corrected temperature
        CH[scan_CH[n]].append(temperature)
        alltemps.append(temperature)
        if len(CH[scan_CH[n]]) >= graph_pts:
            del CH[scan_CH[n]][0]
            truncate = True

    if truncate:
        del alltemps[:len(scan_CH)]
        CH['time'] = np.delete(CH['time'], 0)

    ## Update graphs
    time_vec = range(len(CH['time']))
    plt.cla()
    #plot all temperatures
    for n in range(len(scan_CH)):
        plt.plot(time_vec, CH[scan_CH[n]], colorvec[n], lineWidth=2.0, label='Ch '+scan_CH[n])
    #temperature graph setup
    ax1.set_ylim([min(alltemps)-0.25, max(alltemps)+0.25])
    ax1.ticklabel_format(style='plain')
    plt.ylabel('Temperature (deg. C)', fontsize=5)
    plt.yticks(fontsize=5)
    plt.grid(color='gray', alpha=0.3)
    plt.legend(bbox_to_anchor=(0.5, 0.99), loc='upper center', ncol=4, fontsize=6)
    ax1.patch.set_facecolor('black')
    plt.ticklabel_format(useOffset=False)
    plt.xticks(np.arange(min(time_vec), max(time_vec), tick_spacing), CH['time'][np.arange(min(time_vec), max(time_vec), tick_spacing)], rotation='vertical', fontsize=5)

    plt.pause(0.001)

    ## Read csv and append environment data to end of file
    if (os.path.isfile(envdatadir+filename+'.env.csv')) and (overwrite == False):
        with open(envdatadir+filename+'.env.csv', 'a') as envfile:              #open file with append properties
            envfile.write(currenttime)                                          #add time of measurement
            for n in range(len(scan_CH)):                                       #add all latest temperatures
                envfile.write(','+str(CH[scan_CH[n]][-1]))
            envfile.write('\n')
    elif (os.path.isfile(envdatadir+filename+'.env.csv')) and (overwrite == True):
        with open(envdatadir+filename+'.env.csv', 'w') as envfile:              #open file with write properties
            envfile.write('Temperature (deg. C),')                              #write first header
            for n in range(len(scan_CH)):
                envfile.write('CH['+str(scan_CH[n])+']')                        #write first header
            envfile.write('\n') #end of first header
            envfile.write(currenttime)                                          #add time of measurement
            for n in range(0, len(scan_CH)):                                    #add all temperatures
                envfile.write(','+str(CH[scan_CH[n]][-1]))
            envfile.write('\n')
        overwrite = False
    else:
        with open(envdatadir+filename+'.env.csv', 'w') as envfile:              #open file with write properties
            envfile.write('Temperature (deg. C),')                              #write first header
            for n in range(len(scan_CH)):
                envfile.write('CH['+str(scan_CH[n])+']')                        #write first header
            envfile.write('\n') #end of first header
            envfile.write(currenttime)                                          #add time of measurement
            for n in range(0, len(scan_CH)):                                    #add all temperatures
                envfile.write(','+str(CH[scan_CH[n]][-1]))
            envfile.write('\n')

    tf = time.time()                                                            #stop timer------------------------------------------
    if sleeptimer-(tf-ti) > 0:
        time.sleep(sleeptimer-(tf-ti))                                          #sleep for sleeptimer less time taken for above lines
#while end
