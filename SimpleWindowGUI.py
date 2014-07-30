#!/usr/bin/env python
#  -*- coding: utf-8 -*-

__author__ = "Antonio Lignan"

# // TODO: Reduce repeated code: create classes for buttons, labels, etc... this was done on the go!

import Tkinter as tk
import ModbusRTUMaster as MB

# The following are to process the response/exceptions from read/write operations
from pymodbus.pdu import ExceptionResponse
from pymodbus.register_read_message import *
from pymodbus.register_write_message import *

# To read mmap.xml file
import os
import collections
from xml.dom import minidom

DEBUG_MB = 1

if DEBUG_MB:
    import logging

# Name of the memory map XML file
MMAP_FILE_NAME = '\mmap.xml'

# Available type of MB request types
mb_cmd = ['input', 'holding', 'write']

# List of MB exception codes
# Taken from http://www.kepware.com/Support_Center/SupportDocuments/KTAN90006_Modbus_Exception_Codes.pdf
mb_exc_codes = {1: "Illegal function",
                2: "Illegal data address",
                3: "Illegal data value",
                4: "Failure In Associated Device",
                5: "Acknowledge",
                6: "Busy, Rejected Message",
                7: "NAK – Negative Acknowledgement",
                8: "Memory Parity Error",
                9: "Gateway Path Unavailable",
                10: "Gateway Target Device Failed to respond"}


# Class to build a simple GUI window
class SimpleWindowGUI:
    def __init__(self, title):
        self.master = tk.Tk()
        self.master.title(title)
        self.frame = tk.Frame(self.master, borderwidth=5, bg='white')

        # Create a text entry variables for the connection module
        self.entry_port = tk.StringVar()
        self.entry_parity = tk.StringVar()
        self.entry_stopbits = tk.StringVar()
        self.entry_baudrate = tk.StringVar()
        self.entry_bytesize = tk.StringVar()

        # Text entry variables for MB command
        self.entry_reg = tk.StringVar()
        self.entry_count = tk.StringVar()
        self.entry_unit = tk.StringVar()
        self.entry_data = tk.StringVar()

        # Create a text box widgets to store the text input into the text entry variable
        self.entry_box_port = tk.Entry(self.frame, textvariable=self.entry_port, justify="center")
        self.entry_box_parity = tk.Entry(self.frame, textvariable=self.entry_parity, justify="center")
        self.entry_box_stopbits = tk.Entry(self.frame, textvariable=self.entry_stopbits, justify="center")
        self.entry_box_baudrate = tk.Entry(self.frame, textvariable=self.entry_baudrate, justify="center")
        self.entry_box_bytesize = tk.Entry(self.frame, textvariable=self.entry_bytesize, justify="center")

        self.entry_box_reg = tk.Entry(self.frame, textvariable=self.entry_reg, justify="center")
        self.entry_box_count = tk.Entry(self.frame, textvariable=self.entry_count, justify="center")
        self.entry_box_unit = tk.Entry(self.frame, textvariable=self.entry_unit, justify="center")
        self.entry_box_data = tk.Entry(self.frame, textvariable=self.entry_data, justify="center")

        # Create a label tag for the serial port connection, port, parity, etc
        self.label_connection_text = tk.StringVar()
        self.label_port_text = tk.StringVar()
        self.label_parity_text = tk.StringVar()
        self.label_baudrate_text = tk.StringVar()
        self.label_stopbits_text = tk.StringVar()
        self.label_bytesize_text = tk.StringVar()
        self.button_connect_text = tk.StringVar()

        self.label_reg_text = tk.StringVar()
        self.label_count_text = tk.StringVar()
        self.label_unit_text = tk.StringVar()
        self.label_data_text = tk.StringVar()
        self.label_command_send_hdr_text = tk.StringVar()
        self.label_command_receive_hdr_text = tk.StringVar()
        self.label_command_send_text = tk.StringVar()
        self.label_command_receive_text = tk.StringVar()

        # Variable to select command type using radiobutton widget
        self.command_type = tk.StringVar()

        # Create radio button options
        self.cmd_type_input = tk.Radiobutton(self.frame, text="Read Input", variable=self.command_type, value=mb_cmd[0],
                                             justify="left", bg='white')
        self.cmd_type_holding = tk.Radiobutton(self.frame, text="Read Holding", variable=self.command_type,
                                               value=mb_cmd[1], justify="left", bg='white')
        self.cmd_type_write = tk.Radiobutton(self.frame, text="Write Register", variable=self.command_type,
                                             value=mb_cmd[2], justify="left", bg='white')

        # Create a dict and list widget with the mmap content, the dictionary will be ordered,
        # based on the order the registers are written in the mmap file
        self.mmap_entries = collections.OrderedDict()
        self.list_mmap = tk.Listbox(self.frame, bg='white')

        # This is the scrollbar for the listbox
        self.list_mmap_scrollbar = tk.Scrollbar(self.list_mmap, orient=tk.VERTICAL)
        self.list_mmap.config(yscrollcommand=self.list_mmap_scrollbar.set)
        self.list_mmap_scrollbar.config(command=self.list_mmap.yview)

        # Create an empty MB object, the constructor will be invoked at connection time
        self.client = "None"

        # A connection status
        self.connected = False

        # Initialize all windows class components
        self.initialize()

        # Geometric specific
        self.master.resizable(False, False)
        self.master.update()
        self.master.geometry(self.master.geometry())

        # And loop
        self.master.mainloop()

    # To avoid repeating code, status can be readonly, normal, we
    # swap readonly for disable in the case of the radio button widgets
    def toggle_mb_entries(self, status):
        self.entry_box_reg.config(state=status)
        self.entry_box_count.config(state=status)
        self.entry_box_unit.config(state=status)
        self.entry_box_data.config(state=status)

        if status == 'readonly':
            status = 'disabled'

        self.cmd_type_holding.config(state=status)
        self.cmd_type_input.config(state=status)
        self.cmd_type_write.config(state=status)
        self.list_mmap.config(state=status)

    # To avoid repeating code, status can be readonly, normal
    def toggle_conn_entries(self, status):
        self.entry_box_port.config(state=status)
        self.entry_box_parity.config(state=status)
        self.entry_box_baudrate.config(state=status)
        self.entry_box_bytesize.config(state=status)
        self.entry_box_stopbits.config(state=status)

    def initialize_mmap(self):
        # First check if the mmap.xml exists ON my location
        mmap_abs_path = os.path.dirname(os.path.abspath(__file__)) + MMAP_FILE_NAME
        if not os.path.isfile(mmap_abs_path):
            return "No mmap.xml file found"

        # Load XML file and parse
        try:
            mmap = minidom.parse(mmap_abs_path)
        except:
            return "File mmap.xml could not be parsed"

        # Create a dictionary to store the entries in the following way (encode as string, not unicode):
        # {Name : [Address, Type, Length], ...]
        registers = mmap.getElementsByTagName('reg')
        for entry in registers:
            self.mmap_entries[entry.getElementsByTagName("name")[0].childNodes[0].data.encode('UTF-8')] = [
                entry.getElementsByTagName("address")[0].childNodes[0].data.encode('UTF-8'),
                entry.getElementsByTagName("type")[0].childNodes[0].data.encode('UTF-8'),
                entry.getElementsByTagName("length")[0].childNodes[0].data.encode('UTF-8')
            ]

        # Now add the registers into the list
        for key, value in self.mmap_entries.items():
            self.list_mmap.insert(tk.END, key)

        return "Memory map found, available registers below"

    def initialize(self):
        # Create a grid layout manager
        self.frame.grid()

        # Add the text box widget to the layout manager, stick to the East/West edges of the cell,
        # bind to an event when press enter
        self.entry_box_port.grid(column=2, row=0, columnspan=4, sticky='EW', padx=10)
        self.entry_box_port.bind("<Button-1>", self.on_click_text_entry_box_port)
        self.entry_box_parity.grid(column=2, row=1, columnspan=4, sticky='EW', padx=10)
        self.entry_box_parity.bind("<Button-1>", self.on_click_text_entry_box_parity)
        self.entry_box_baudrate.grid(column=2, row=2, columnspan=4, sticky='EW', padx=10)
        self.entry_box_baudrate.bind("<Button-1>", self.on_click_text_entry_box_baudrate)
        self.entry_box_stopbits.grid(column=2, row=3, columnspan=4, sticky='EW', padx=10)
        self.entry_box_stopbits.bind("<Button-1>", self.on_click_text_entry_box_stopbits)
        self.entry_box_bytesize.grid(column=2, row=4, columnspan=4, sticky='EW', padx=10)
        self.entry_box_bytesize.bind("<Button-1>", self.on_click_text_entry_box_bytesize)

        self.entry_box_reg.grid(column=2, row=7, columnspan=4, sticky='EW', padx=10)
        self.entry_box_reg.bind("<Button-1>", self.on_click_text_entry_box_parity)
        self.entry_box_count.grid(column=2, row=8, columnspan=4, sticky='EW', padx=10)
        self.entry_box_count.bind("<Button-1>", self.on_click_text_entry_box_baudrate)
        self.entry_box_unit.grid(column=2, row=9, columnspan=4, sticky='EW', padx=10)
        self.entry_box_unit.bind("<Button-1>", self.on_click_text_entry_box_stopbits)
        self.entry_box_data.grid(column=2, row=10, columnspan=4, sticky='EW', padx=10)
        self.entry_box_data.bind("<Button-1>", self.on_click_text_entry_box_bytesize)

        # Create a simple button bind to an event handler
        button_connect = tk.Button(self.frame, textvariable=self.button_connect_text, command=self.on_button_connect)
        button_connect.grid(column=0, row=0, columnspan=2, sticky='EW')
        self.button_connect_text.set(u"CONNECT")

        button_send_command = tk.Button(self.frame, text=u"SEND COMMAND ", command=self.on_button_send)
        button_send_command.grid(column=8, row=10, columnspan=2, sticky='EW')

        # Create labels, black font and white background, text left-aligned ("w"),
        # expand the label across 2 cells in the grid layout manager (columnspan),
        # bind the variable tag to the widget

        label_port = tk.Label(self.frame, textvariable=self.label_port_text, anchor="w", fg="black", bg="white")
        label_port.grid(column=6, row=0, columnspan=4, sticky='EW')
        self.label_port_text.set(u"Serial Port")
        label_parity = tk.Label(self.frame, textvariable=self.label_parity_text, anchor="w", fg="black", bg="white")
        label_parity.grid(column=6, row=1, columnspan=4, sticky='EW')
        self.label_parity_text.set(u"(E)ven, (O)dd, (N)one")
        label_baudrate = tk.Label(self.frame, textvariable=self.label_baudrate_text, anchor="w", fg="black", bg="white")
        label_baudrate.grid(column=6, row=2, columnspan=4, sticky='EW')
        self.label_baudrate_text.set(u"Baud Rate")
        label_stopbits = tk.Label(self.frame, textvariable=self.label_stopbits_text, anchor="w", fg="black", bg="white")
        label_stopbits.grid(column=6, row=3, columnspan=4, sticky='EW')
        self.label_stopbits_text.set(u"Stop bits")
        label_bytesize = tk.Label(self.frame, textvariable=self.label_bytesize_text, anchor="w", fg="black", bg="white")
        label_bytesize.grid(column=6, row=4, columnspan=4, sticky='EW')
        self.label_bytesize_text.set(u"Byte size")

        label_reg = tk.Label(self.frame, textvariable=self.label_reg_text, anchor="w", fg="black", bg="white")
        label_reg.grid(column=0, row=7, columnspan=2, sticky='EW')
        self.label_reg_text.set(u"Register (decimal)")
        label_count = tk.Label(self.frame, textvariable=self.label_count_text, anchor="w", fg="black", bg="white")
        label_count.grid(column=0, row=8, columnspan=2, sticky='EW')
        self.label_count_text.set(u"Number (regs, decimal)")
        label_unit = tk.Label(self.frame, textvariable=self.label_unit_text, anchor="w", fg="black", bg="white")
        label_unit.grid(column=0, row=9, columnspan=2, sticky='EW')
        self.label_unit_text.set(u"MB Server ID (decimal)")
        label_data = tk.Label(self.frame, textvariable=self.label_data_text, anchor="w", fg="black", bg="white")
        label_data.grid(column=0, row=10, columnspan=2, sticky='EW')
        self.label_data_text.set(u"Data (hex, no lead '0x')")

        # This is the connection status label
        label_connection = tk.Label(self.frame, textvariable=self.label_connection_text, anchor="w",
                                    fg="black", bg="grey")
        label_connection.grid(column=0, row=5, columnspan=10, sticky='EW')
        self.label_connection_text.set(u"Awaiting connection!")

        # This is the command status label (Request sent)
        label_command_send_hdr = tk.Label(self.frame, textvariable=self.label_command_send_hdr_text, anchor="w",
                                          fg="black", bg="white")
        label_command_send = tk.Label(self.frame, textvariable=self.label_command_send_text, anchor="w",
                                      fg="black", bg="grey")
        label_command_send_hdr.grid(column=0, row=15, columnspan=1, sticky='EW')
        label_command_send.grid(column=1, row=15, columnspan=10, sticky='EW')
        self.label_command_send_hdr_text.set(u"TX")
        self.label_command_send_text.set(u"Awaiting command")

        # This is the command status label (Receive response/exception)
        label_command_receive_hdr = tk.Label(self.frame, textvariable=self.label_command_receive_hdr_text, anchor="w",
                                             fg="black", bg="white")
        label_command_receive = tk.Label(self.frame, textvariable=self.label_command_receive_text, anchor="w",
                                         fg="black", bg="grey")
        label_command_receive_hdr.grid(column=0, row=16, columnspan=1, sticky='EW')
        label_command_receive.grid(column=1, row=16, columnspan=10, sticky='EW')
        self.label_command_receive_hdr_text.set(u"RX")
        self.label_command_receive_text.set(u"Awaiting response/exception")

        # Empty label, as I don't know how to place emtpy rows as Tkinter ignores it...
        tk.Label(self.frame, anchor="w", bg="white").grid(column=0, row=6, columnspan=10, sticky='EW')
        tk.Label(self.frame, anchor="w", bg="white").grid(column=0, row=11, columnspan=10, sticky='EW')
        tk.Label(self.frame, anchor="w", bg="white").grid(column=0, row=14, columnspan=10, sticky='EW')

        # Initialize radio buttons
        self.cmd_type_input.grid(column=8, row=7, sticky='W')
        self.cmd_type_holding.grid(column=8, row=8, sticky='W')
        self.cmd_type_write.grid(column=8, row=9, sticky='W')
        self.cmd_type_input.select()

        # Initialize lists and its scrollbar, create a label for the list and bind to events
        tk.Label(self.frame, anchor="w", bg="grey", text=self.initialize_mmap()).grid(column=0, row=12,
                                                                                      columnspan=10,
                                                                                      sticky='EW')
        self.list_mmap.grid(column=0, columnspan=3, row=13, sticky='WE')
        self.list_mmap.columnconfigure(0, weight=1)
        self.list_mmap_scrollbar.grid(column=0, sticky='EW')
        self.list_mmap.bind("<Double-Button-1>", self.on_double_click_list_mmap)

        # Print instructions on the text box
        self.entry_port.set(u"/dev/ttyUSB0")
        self.entry_parity.set(u"E")
        self.entry_baudrate.set(u"19200")
        self.entry_stopbits.set(u"1")
        self.entry_bytesize.set(u"8")

        # Disable all MB related cells, until we are connected
        self.toggle_mb_entries('readonly')

        # Enable login
        if DEBUG_MB:
            logging.basicConfig()
            log = logging.getLogger()
            log.setLevel(logging.DEBUG)

    # Default behaviour when pressing the CONNECT/DISCONNECT button to create a serial connection
    def on_button_connect(self):
        if self.connected is False:
            # Check if any of the cells are empty
            if self.entry_box_port.get() == "" or \
               self.entry_box_parity.get() == "" or \
               self.entry_box_baudrate.get() == "" or \
               self.entry_box_bytesize.get() == "" or \
               self.entry_box_stopbits.get() == "":
                    self.label_connection_text.set(u"Invalid: cell missing!")
                    return

            self.label_connection_text.set(u"Connecting... !")
            self.client = MB.create_port(self.entry_box_port.get(),
                                         int(self.entry_box_baudrate.get()),
                                         self.entry_box_parity.get(),
                                         int(self.entry_box_stopbits.get()),
                                         int(self.entry_box_bytesize.get()))

            if MB.connect(self.client) is True:
                self.label_connection_text.set(u"CONNECTED !")
                self.connected = True
                self.button_connect_text.set(u"DISCONNECT")

                # Block the text entry
                self.toggle_conn_entries('readonly')

                # And enable the MB related ones
                self.toggle_mb_entries('normal')
            else:
                self.label_connection_text.set(u"Failed to connect, check settings... !")
        else:
            MB.close(self.client)
            self.connected = False
            self.button_connect_text.set(u"CONNECT")
            self.label_connection_text.set(u"Awaiting connection!")

            # Enable the text entry again, revert the MB ones
            self.toggle_conn_entries('normal')
            self.toggle_mb_entries('readonly')

    def on_button_send(self):
        # Create a dictionary with the command types and corresponding functions to call
        cmd_key = {mb_cmd[0]: MB.read_input_registers,
                   mb_cmd[1]: MB.read_holding_registers}

        # Prevent eager users...
        if self.connected is False:
            self.label_connection_text.set(u"Not connected! connect first")
            return

        # Re-set the TX/RX expected label
        self.label_command_receive_text.set(u"Awaiting response/exception")
        self.label_command_send_text.set(u"Awaiting command")

        # Check the content of the common fields
        if not self.entry_box_reg.get().isdigit() or \
           not self.entry_box_count.get().isdigit() or \
           not self.entry_box_unit.get().isdigit():
                self.label_command_send_text.set(u"Invalid data, Reg value/numbers, ID must be numbers")
                return

        # Filter this as it has different arguments
        if self.command_type.get() == mb_cmd[2]:

            # We cannot accept empty data fields or odd data i.e 004 (I don't want to pad, I'm a lazy fuck)
            if len(self.entry_box_data.get()) <= 0:
                self.label_command_send_text.set(u"Data values have to be even (not odd, zero)")
                return

            # Now let's check if the string is actually a hexadecimal one
            test = self.entry_box_data.get()

            try:
                int(test, 16)
            except ValueError:
                # Maybe we are using white spaces in between, let's check:
                test = test.replace(" ", "")
                try:
                    int(test, 16)
                except ValueError:
                    self.label_command_send_text.set(u"Data values are not hexadecimal!")
                    return

            # If we have an odd string, add a leading zero:
            if len(test) % 2 != 0:
                test = '0'+test

            # MB expects a list of integers, so create one for them, each slot should have a 16-bit value
            a_list = [test[i:i+4] for i in range(0, len(test), 4)]

            for i in range(0, len(a_list)):
                a_list[i] = int(a_list[i], 16)

            # We support both single/multiple write operations in the same command, the
            # key is using the number of registers, we need to check if this matches the
            # data passed to us

            if int(self.entry_box_count.get()) != len(a_list):
                self.label_command_send_text.set(u"Number of registers to write do not match data length!")
                return

            # Depending on the number of registers to write, use either write operation from MB
            if int(self.entry_box_count.get()) > 1:
                print "here"
                result = MB.write_registers(self.client, int(self.entry_box_reg.get()),
                                            a_list, int(self.entry_box_unit.get()))
            else:
                result = MB.write_single_register(self.client, int(self.entry_box_reg.get()),
                                                  a_list[0], int(self.entry_box_unit.get()))
        else:
            # Retrieve the command type and call the corresponding function
            result = cmd_key[self.command_type.get()](self.client,
                                                      int(self.entry_box_reg.get()),
                                                      int(self.entry_box_count.get()),
                                                      int(self.entry_box_unit.get()))
        if result is None:
            self.label_command_send_text.set(u"Command was not executed, result None")
            return

        # print type(result)

        # Create single array to print result to user
        registers_result = ''
        base_cmd_register = int(self.entry_box_reg.get())

        if isinstance(result, WriteMultipleRegistersResponse):
            registers_result = "Wrote from {0} to {1} registers at {2}".format(str(result.address),
                                                                               str(result.address + result.count),
                                                                               str(result.unit_id))
            self.label_command_receive_text.set(registers_result)

        elif isinstance(result, WriteSingleRegisterResponse):
            registers_result = str(base_cmd_register) + ':' + str(hex(result.value)[2:].zfill(2))
            self.label_command_receive_text.set(registers_result)

        elif isinstance(result, ExceptionResponse):
            error_message = "Exception (EC{0} : {1})".format(str(result.exception_code),
                                                             mb_exc_codes[result.exception_code])
            self.label_command_receive_text.set(error_message)

        elif isinstance(result, ReadInputRegistersResponse) or isinstance(result, ReadHoldingRegistersResponse):
            # Filter timeout, at the moment noticeable by a zero-string returned
            if len(result.registers) == 0:
                self.label_command_send_text.set(u"TIMEOUT!")
                return

            for regs in result.registers:
                registers_result = registers_result + ' ' + str(base_cmd_register) + ':' + str(hex(regs)[2:].zfill(2))
                base_cmd_register += 1
            # Remove leading/ending spaces
            registers_result.strip()
            self.label_command_receive_text.set(registers_result)

        # Print the modbus frame sent on the TX label

    # This event is triggered by a double click, user selects a register from the memory map
    # and its content is updated in the command boxes
    def on_double_click_list_mmap(self, event):
        if not self.connected:
            return

        # Clear previous option
        self.entry_box_reg.delete(0, tk.END)
        self.entry_box_count.delete(0, tk.END)

        widget = event.widget
        selection = widget.curselection()
        value = widget.get(selection[0])

        self.entry_box_reg.insert(0, self.mmap_entries[value][0])
        self.entry_box_count.insert(0, self.mmap_entries[value][2])

        # If the register is an input/holding register, also select for the user
        if self.mmap_entries[value][1] == mb_cmd[0]:
            self.cmd_type_input.select()
        else:
            self.cmd_type_holding.select()


    # The functions below are meant only for clearing the text box content on a mouse click,
    # this could be optimized into a single function, this has to be done eventually :)

    def on_click_text_entry_box_port(self, event):
        self.entry_box_port.delete(0, tk.END)

    def on_click_text_entry_box_parity(self, event):
        self.entry_box_parity.delete(0, tk.END)

    def on_click_text_entry_box_baudrate(self, event):
        self.entry_box_baudrate.delete(0, tk.END)

    def on_click_text_entry_box_stopbits(self, event):
        self.entry_box_stopbits.delete(0, tk.END)

    def on_click_text_entry_box_bytesize(self, event):
        self.entry_box_bytesize.delete(0, tk.END)