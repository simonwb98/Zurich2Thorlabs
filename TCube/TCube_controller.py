# -*- coding: utf-8 -*-
"""
Created on Tue May 23 16:56:41 2023

@author: Simon

Connect to Thorlabs driver and give movement commands. This script works for a Thorlabs TCube controller. KCubes can also be implemented
by changing the method names appropriately. In particular, another import must be made:

    from Thorlabs.MotionControl.GenericMotorCLI import KCubeMotor
"""

# imports for Thorlabs
import time
import clr # need to import pythonnet (can be done from pip)

#imports for zurich
from zhinst import utils as ziutils
import zhinst.core

# imports for live plotting and asynchronous programming
import numpy as np
import datetime as dt
import asyncio
import signal
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import sys
import os


# to access dll namespaces from Thorlabs, we need to first add the references
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.TCube.DCServoCLI.dll")

# import methods/objects from Thorlabs namespaces
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.GenericMotorCLI.ControlParameters import JogParametersBase
from Thorlabs.MotionControl.TCube.DCServoCLI import *
from System import Decimal # Kinesis libraries use Decimal type for move parameters and stage settings

# connect to lock-in
device_id = "dev2142"
apilevel = 6
(daq, device, props) = ziutils.create_api_session(device_id, apilevel)

user_position = float(input("Please specify position in mm: "))
animation_active = True

async def display_coroutine(controller: TCubeDCServo, daq: zhinst.core.ziDAQServer, sampling_rate: float):
    global interrupted

    # initialize plot 
    app = QtWidgets.QApplication(sys.argv)
    win = pg.GraphicsLayoutWidget()
    win.show()

    show_last = 300 #int, number of data points
    x = np.linspace(-show_last*sampling_rate, -sampling_rate, show_last, endpoint=True) # time arr

    # initialize y data for thorlabs and zurich
    y_tl = np.zeros(show_last)
    y_zi = np.zeros(show_last)

    # initialize plot windows
    # thorlabs
    plot_item1 = pg.PlotItem()
    pen1 = pg.mkPen(color=(255, 0, 0))
    plot1 = plot_item1.plot(pen=pen1)
    win.addItem(plot_item1, row=1, col=1, rowspan=1, colspan=1)
    plot1.setData(x, y_tl)

    # zurich
    plot_item2 = pg.PlotItem()
    pen2 = pg.mkPen(color=(0, 0, 255))
    plot2 = plot_item2.plot(pen=pen2)
    win.addItem(plot_item2, row=2, col=1, rowspan=1, colspan=1)
    plot2.setData(x, y_zi)

    # decoration tl plot window
    plot_item1.getAxis("bottom").setLabel("Time", units="s")
    plot_item1.getAxis("left").setLabel("Position", units="mm")
    plot_item1.setTitle(f"{controller.GetDeviceInfo().Name} Translation stage")

    # decoration zi plot window
    plot_item2.getAxis("bottom").setLabel("Time", units="s")
    plot_item2.getAxis("left").setLabel("Demod signal", units="V")
    plot_item2.setTitle(f"{device} Lock-in")

    while not interrupted:
        await asyncio.sleep(sampling_rate)
        pos = controller.Position.ToString()
        sample = daq.getSample("/%s/demods/0/sample" % device)
        get_polar(sample)

        # update tl data
        x = np.append(x, x[-1] + sampling_rate)
        x = x[1:] # pop off first element
        y_tl = np.append(y_tl, float(pos))
        y_tl = y_tl[1:]

        # update zi data
        y_zi = np.append(y_zi, sample["R"])
        y_zi = y_zi[1:]
        
        # update plots with new data
        plot1.setData(x, y_tl)
        plot2.setData(x, y_zi)
        QtCore.QCoreApplication.processEvents()
    app.exec_()
            
    

def handle_interrupt(signum, frame):
    print("Program interrupted. Disconnecting from controller ...")
    print("You can close the plot window now.")
    global interrupted 
    interrupted = True

def get_polar(sample):
    sample["R"] = np.abs(sample["x"] + 1j * sample["y"])
    sample["theta"] = np.angle(sample["x"] + 1j * sample["y"])


async def main(): 
    global interrupted
    interrupted = False
    signal.signal(signal.SIGINT, handle_interrupt)

    serial_num = str('83835052') # use S/N of T Cube controller
    
    DeviceManagerCLI.BuildDeviceList() # load available devices into memory
    controller = TCubeDCServo.CreateTCubeDCServo(serial_num) # create controller variable
    
    if not controller == None: # check if connection worked
        controller.Connect(serial_num)
        
        if not controller.IsSettingsInitialized(): # wait for connection and initialization
            controller.WaitForSettingsInitialized(3000) # in units of ms
        
        controller.StartPolling(50) # instruct controller to send updates about position and motor status to PC with update rate of 50ms
        time.sleep(.1) # give controller time to update, good habits to set as twice the duration of polling rate
        controller.EnableDevice()
        time.sleep(.1)
        
        # load parameters for translation stage into the TCube
        config = controller.LoadMotorConfiguration(serial_num, DeviceConfiguration.DeviceSettingsUseOptionType.UseFileSettings)
        config.DeviceSettingsName = str('MTS50-Z8') # use part number of this stage
        config.UpdateCurrentConfiguration()
        controller.SetSettings(controller.MotorDeviceSettings, True, False)
        info = controller.GetDeviceInfo()
        
        print(f"Controller {serial_num} = {info.Name}")

        print('Homing Motor')
        controller.Home(60000) # if command does not complete by the end of this time, it will throw an error
        
        # to change the jog params of the translation stage, first import them with the GetJogParams method and then modify
        jog_params = controller.GetJogParams()
        jog_params.StepSize = Decimal(1) # units in mm
        jog_params.MaxVelocity = Decimal(2) # units in mm/s
        jog_params.JogMode = JogParametersBase.JogModes.SingleStep
        
        # send updated jog params back to the controller
        controller.SetJogParams(jog_params)
        
        print('Moving Motor')
        controller.MoveTo(Decimal(user_position), 0) # immediately continue
        time.sleep(.25)
        print("Press \"Ctrl+c\" to interrupt")
        sampling_rate = .1 #float, rate in s

        try:
            display_task = asyncio.create_task(display_coroutine(controller, daq, sampling_rate))
            await display_task
        # except KeyboardInterrupt:
        #     interrupted = True
        #     controller.StopPolling()
        #     controller.Disconnect(False)
        #     print("Disconnected")
        finally:
            if interrupted:
                controller.StopPolling()
                controller.Disconnect(False)
                print("Disconnected")



            
        
        # want the controller to move first to user specified position and then 
        # depending on the input of the zurich to move towards or away from the assumed position.


asyncio.run(main())
sys.exit()