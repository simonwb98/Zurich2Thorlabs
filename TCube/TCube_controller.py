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

def main():
    
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
        jog_params.MaxVelocity = Decimal(1) # units in mm/s
        jog_params.JogMode = JogParametersBase.JogModes.SingleStep
        
        # send updated jog params back to the controller
        controller.SetJogParams(jog_params)
        
        print('Moving Motor')
        controller.MoveJog(MotorDirection.Forward, 60000) # move one step forwards, abort if this takes longer than specified time in ms
        
        controller.StopPolling()
        controller.Disconnect(False) 
    
if __name__ == "__main__":
    main()