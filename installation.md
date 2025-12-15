# Installation

> WIP

### Retrieve USB information

Retrieve your device information. You will at least need the vendor ID and product ID.

#### Mac OS

Click the apple logo in the top left (same for logging off and shutting down the system) -> About this Mac -> System Report... (on the bottom) -> USB, and then find your USB Thermal Printer.

#### Linux

In a terminal, run `lsusb`, and you'll find the ID's listed as `ID VndID:PrdID`.


## Configuration file

Set the connection type to either `serial` or `usb`.

```yaml
printer:
  connection_type:
```


## Common issues

### USB

#### NoBackendAvailable

This happens when the vendor information is not properly matching with the `in_ep` and `out_ep`. To retrieve this information, open a python shell (while in the python `venv`) and run the following script to retrieve all the information:

```python
import usb.core

print(usb.core.find(idVendor=0x2730, idProduct=0x2002))
```

