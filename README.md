README for MBGui tool.

Currently supported:

- Read Input/Holding registers
- Writes to single/multiple registers
- Exception codes are filtered and displayed
- Several user checks
- Load memory map from xml file, listbox with scrollbar and fill modbus entry boxes on double click
- Attempt to serial connection and send commands on <return> press also (not only via button)

Features missing:

- Display outgoing frame in TX label
- Display received frame as well
- CRC calculator
- Save/load frames
- Program periodically write/read operations, store result in file

Known bugs:

- When reading more than 100 input/holding registers, window resize bad