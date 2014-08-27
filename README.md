README for MBGui tool.

Currently supported:

- Read Input/Holding registers, no coils
- Writes to single/multiple registers
- Exception codes are filtered and displayed
- Several user checks
- Load memory map from xml file, listbox with scrollbar and fill modbus entry boxes on double click
- Attempt to serial connection and send commands on <return> press also (not only via button)
- Program periodically write/read operations, store result in a plain-text file with timestamp (broken)
- Displays outgoing TX frame (bytes) with CRC appended
- Displays Response/Exception information
- Store/load MB commands from Menu

Features missing:

- Make unit ID a list to be able to poll several MB servers with a single command
- Coil support, maybe...

Known bugs/enhancements required:

- When reading more than 100 input/holding registers, window resize bad
- Clean up and remove repeated code/blocks, create classes, etc
- Clean up grid, use max values/weights