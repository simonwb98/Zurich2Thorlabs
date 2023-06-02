# -*- coding: utf-8 -*-
"""
Created on Tue May 23 16:56:41 2023

@author: Simon

Connect to Thorlabs driver and give movement commands. This script works for a Thorlabs TCube controller. KCubes can also be implemented
by changing the method names appropriately. In particular, another import must be made:

    from Thorlabs.MotionControl.GenericMotorCLI import KCubeMotor
"""


import time
import clr # need to import pythonnet (can be done from pip)
from matplotlib import pyplot as plt
import datetime as dt
import asyncio
import signal


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

user_position = float(input("Please specify position in mm: "))
animation_active = True

async def display_coroutine(controller: TCubeDCServo, refresh_rate: float, xs: list, ys: list):
    await asyncio.sleep(refresh_rate)

    pos = controller.Position.ToString()
    xs.append(dt.datetime.now().strftime('%H:%M:%S.%f'))
    ys.append(pos)

def handle_interrupt(signum, frame):
    print("Program interrupted. Disconnecting from controller ...")
    global interrupted 
    interrupted = True
    # raise KeyboardInterrupt


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
        print("Press Ctrl+c to interrupt")

        fig, ax = plt.subplots()
        xs = []
        ys = []
        plt.ion()

        try:
            while not interrupted:
                await asyncio.gather(display_coroutine(controller, .25, xs, ys))
                ln, = ax.plot(xs, ys)
                ax.set_xlabel("Time")
                ax.set_ylabel("Position (mm)")
                plt.xticks(rotation=45, ha="right")
                plt.show()
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