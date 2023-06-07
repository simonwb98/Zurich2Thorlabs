# zi2tl_python

## In short
This repository contains python code I've written to read out signals from a Zurich UHFLI Lock-in amplifier and to controll the operation of a Thorlabs TCube controlled translation stage ``` MTS50-Z8 ```. The Lock-in is used for filtering the laser signal from the Thorlabs photodiode directly (i.e. without the need for nanonis or other controllers) from environmental noise sources and to feed that signal into a PID controller. The controller output is then used for appropriately moving the Thorlabs stage back and forth to remain at a particular photodiode voltage signal, as a voltage setpoint in Zurich instrument's LabOne Interface. A live plot updates the user about the current Thorlabs position as well as the error signal from the PID loop.

![Example of Real-time plot: The upper window shows the position of the translation stage as stored by the TCube controller. The lower one displays the PID error, i.e. the difference between the setpoint voltage and the readout.](docs/exemplary_plot.png)


## Setting up and Troubleshooting

To properly set up this PID loop to the translation stage, the user must give the program a position to which the stage should move. Upon homing, a plot window pops up that refreshes avery 100ms (this can be modified in '''main()''') and updates the user about translation stage position and PID error signal. By default, the program selects the fourth PID controller from the Zurich Lock-in amplifier, with the node tree '''/device_id/pids/3'''. 


## Improvement ideas

To avoid the use of global variables as the '''interrupted''' flag that handles a KeyboardInterruptError to avoid killing the kernel and to appropriately shut down communication with the TCube, a class-based approach might be cleaner. In this case, the global variables could just be defined as attributes of a '''Zurich_2_Thorlabs''' object.

## References

[1]: [YouTube Video from Thorlabs about Python Automation](https://www.youtube.com/watch?v=VbcCDI6Z6go)
[2]: [Zurich Instruments Github](https://github.com/zhinst/zhinst-toolkit)
[3]: [Introduction to Zurich Instruments' Python API](https://github.com/zhinst/blogs/blob/59879b799f5b6dcf69f13e88bce79e2e94153db3/A%20Pythonic%20Approach%20to%20LabOne/A%20Pythonic%20Approach%20to%20LabOne.ipynb)
