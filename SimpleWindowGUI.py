#!/usr/bin/env python
#  -*- coding: utf-8 -*-

__author__ = "Antonio Lignan"

# // TODO: Reduce repeated code: create classes for buttons, labels, etc... this was done on the go!

import Tkinter as tk
import tkMessageBox
import ModbusRTUMaster as MB
from tkFileDialog import askopenfilename

# The following are to process the response/exceptions from read/write operations
from pymodbus.pdu import ExceptionResponse
from pymodbus.register_read_message import *
from pymodbus.register_write_message import *
from pymodbus.utilities import computeCRC

# To read mmap.xml file
import os
import collections
from xml.dom import minidom

# To periodically execute a request
# import time, threading

DEBUG_MB = 1

if DEBUG_MB:
    import logging

ABOUT_INFO = "Hello world"

# Name of the default memory map XML file
mmap_abs_path = os.path.dirname(os.path.abspath(__file__)) + "\mmap.xml"

# Name of the default command file
cmd_abs_path = os.path.dirname(os.path.abspath(__file__)) + "\cmd.txt"

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


# Auxiliary function to do dirty stuff that I'm not proud of
def str_hex(val, fill):
    a = str(hex(int(val))[2:].zfill(fill))
    # We only expect values up to 4...
    if fill > 2:
        a = a[:2] + " " + a[2:]
    return a


# I'm not too proud of this one too...
def get_fc(cmd, num):
    if cmd == mb_cmd[0]:
        return '04'
    if cmd == mb_cmd[1]:
        return '03'
    if cmd == mb_cmd[2]:
        if num > 1:
            return '10'
        else:
            return '06'


class PopUpWindow(object):
    def __init__(self, master, data, my_list, my_dict):
        top = self.top = tk.Toplevel(master)
        self.display_text = tk.StringVar()
        self.value = ''
        self.data = data
        self.my_list = my_list
        self.my_dict = my_dict

        tk.Message(top, textvariable=self.display_text, width=200).grid(column=0, row=1, columnspan=8, sticky='EW')
        self.top_text = tk.Entry(self.top, justify='left')
        self.top_text.grid(column=0, row=2, columnspan=8, sticky='EW')

        # Create buttons, close should kill the pop-up menu, save should be triggered upon click or return press
        button_save = tk.Button(top, text=u"SAVE", command=self.store, justify='center')
        button_close = tk.Button(top, text=u"CANCEL", command=self.cleanup, justify='center')

        button_save.grid(column=0, row=4, columnspan=4, sticky='EW')
        button_close.grid(column=4, row=4, columnspan=4, sticky='EW')

        top.title(u"Save")
        self.display_text.set(u"Name the request and click SAVE")

    # Destroy the frame and get the content from the entry box
    def cleanup(self):
        self.value = ''
        self.data = ''
        self.top.destroy()

    # Store the command and close
    def store(self):
        self.value = self.top_text.get()

        # Create a string with the command information
        aux = '\n' + self.value + " " + ":" + " " + self.data

        # First check if the cmd.xml exists ON my location
        if not os.path.isfile(cmd_abs_path):
            # TODO: create an error pop-up box
            self.cleanup()
            return

        # Open the document and append
        try:
            cmd_file = open(cmd_abs_path, 'a')
        except:
            # TODO: create an error pop-up box
            self.cleanup()
            return

        cmd_file.write(aux)
        cmd_file.close()

        # Now store the entry to the dict, refresh the command list, enable back the list and store
        self.my_list.config(state='normal')

        aux = []
        tmp = self.data[:-1].split()
        aux.append(tmp[0])
        aux.append(tmp[1])
        aux.append(tmp[2])
        if tmp[3] != "None":
            new = ""
            for i in range(3, len(tmp)-1):
                new = new + tmp[i]
            aux.append(new)
        else:
            aux.append(tmp[3])
        aux.append(tmp[len(tmp)-1])

        self.my_dict[self.value] = aux

        self.my_list.insert(tk.END, self.value)

        # And destroy the window
        self.cleanup()


# Class to build a simple GUI window
class SimpleWindowGUI:
    def __init__(self, title):
        self.master = tk.Tk()
        self.master.title(title)
        self.frame = tk.Frame(self.master, borderwidth=5, bg='white')
        self.master.iconbitmap(default='transparent.ico')

        # Create this for a pop-up window
        self.top = None

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
        self.entry_periodic = tk.StringVar()

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
        self.entry_box_periodic = tk.Entry(self.frame, textvariable=self.entry_periodic, justify="center", width=15)

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
        self.button_send_command_text = tk.StringVar()
        self.button_save_text = tk.StringVar()

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

        # Add a check button to enable periodically send the same command
        self.checkbox_enabled = tk.IntVar()
        self.checkbox_periodic_request = tk.Checkbutton(self.frame, text=u"Send request every",
                                                        variable=self.checkbox_enabled, bg='white',
                                                        fg='black', anchor='w')

        # Create send command button
        self.button_send_command = tk.Button(self.frame, textvariable=self.button_send_command_text,
                                             command=self.on_button_send)

        # Create a list to store the saved requests and its button
        self.button_save = tk.Button(self.frame, textvariable=self.button_save_text, command=self.popup)
        self.cmd_entries = collections.OrderedDict()
        self.list_cmd = tk.Listbox(self.frame, bg='white')

        # This is the scrollbar for the listbox
        self.list_cmd_scrollbar = tk.Scrollbar(self.list_cmd, orient=tk.VERTICAL)
        self.list_cmd.config(yscrollcommand=self.list_cmd_scrollbar.set)
        self.list_cmd_scrollbar.config(command=self.list_cmd.yview)

        # Create the menu bar
        menu_bar = tk.Menu(self.master)
        self.master.config(menu=menu_bar)
        file_menu = tk.Menu(menu_bar)

        menu_bar.add_cascade(label="Load", menu=file_menu)
        menu_bar.add_cascade(label="About", command=self.display_about)

        file_menu.add_cascade(label="Memory Map...", command=self.load_memory_map)
        file_menu.add_cascade(label="Stored Requests...", command=self.load_saved_requests)

        # Create an empty MB object, the constructor will be invoked at connection time
        self.client = "None"

        # A connection status
        self.connected = False

        # A periodic status
        self.periodic_enabled = False

        # Initialize all windows class components
        self.initialize()

        # Geometric specific
        self.master.resizable(False, False)
        self.master.update()
        self.master.geometry(self.master.geometry())

        # And loop
        self.master.mainloop()

    # The classic about popup window
    def display_about(self):
        # TODO: get somehow the firmware version, date, etc, license!!!
        tkMessageBox.showinfo("About MBGui", ABOUT_INFO)

    # Load a memory map file
    def load_memory_map(self):
        global mmap_abs_path
        if self.connected:
            mmap_abs_path = askopenfilename()
            self.initialize_mmap()

    # Load stored requests
    def load_saved_requests(self):
        global cmd_abs_path
        if self.connected:
            cmd_abs_path = askopenfilename()
            self.initialize_cmd()

    # To avoid repeating code, status can be readonly, normal, we
    # swap readonly for disable in the case of the radio button widgets
    def toggle_mb_entries(self, status):
        self.entry_box_reg.config(state=status)
        self.entry_box_count.config(state=status)
        self.entry_box_unit.config(state=status)
        self.entry_box_data.config(state=status)
        self.entry_box_periodic.config(state=status)

        if status == 'readonly':
            status = 'disabled'

        self.cmd_type_holding.config(state=status)
        self.cmd_type_input.config(state=status)
        self.cmd_type_write.config(state=status)
        self.list_mmap.config(state=status)
        self.list_cmd.config(state=status)
        self.checkbox_periodic_request.config(state=status)
        self.button_save.config(state=status)
        self.button_send_command.config(state=status)

    # To avoid repeating code, status can be readonly, normal
    def toggle_conn_entries(self, status):
        self.entry_box_port.config(state=status)
        self.entry_box_parity.config(state=status)
        self.entry_box_baudrate.config(state=status)
        self.entry_box_bytesize.config(state=status)
        self.entry_box_stopbits.config(state=status)

    # Populates a list with a given list of stored commands
    def initialize_cmd(self):
        # First check if the cmd.xml exists ON my location
        if not os.path.isfile(cmd_abs_path):
            return "No command file found"

        # Load Text file
        try:
            cmd_file = open(cmd_abs_path, 'r+')
        except:
            return "File could not be open"

        # Create a dictionary to store the command entries, ignore the lines starting
        # with a comment push, remove the end-of-lines
        for element in cmd_file:
            discard_blank = element.rstrip()
            if '#' not in element and discard_blank and ":" in discard_blank:
                cmd_name = discard_blank.split(' : ')[0]
                cmd_values = discard_blank.replace("\r\n", "").split(' : ')[1].split(' ')

                # Filter invalid commands, remember to filter out the pesky carriage return at the end,
                # Check for a minimum elements in command
                cmd_args = []
                cmd_last = cmd_values[len(cmd_values)-1]

                if cmd_last in mb_cmd and len(cmd_values) >= 5:
                    cmd_args.append(cmd_values[0])
                    cmd_args.append(cmd_values[1])
                    cmd_args.append(cmd_values[2])

                    if cmd_values[3] == "None":
                        cmd_args.append("")
                    else:
                        aux = ""
                        for i in range(3, len(cmd_values)-1):
                            aux = aux + " " + cmd_values[i]
                        cmd_args.append(aux.strip())
                    cmd_args.append(cmd_last)

                    self.cmd_entries[cmd_name] = cmd_args

        cmd_file.close()

        # Check if my dictionary is empty
        if not self.cmd_entries:
            return "Command file is empty"

        # Enter the commands into the list
        for key, value in self.cmd_entries.items():
            self.list_cmd.insert(tk.END, key)

        return "Found commands below"

    # Populates a list with a given memory map
    def initialize_mmap(self):

        # Flush the list before populating
        self.list_mmap.delete(0, tk.END)

        # Ensure the dictionary is empty before populating
        self.mmap_entries.clear()

        # First check if the mmap.xml exists ON my location
        if not os.path.isfile(mmap_abs_path):
            return "No mmap.xml file found"

        # Load XML file and parse
        try:
            mmap = minidom.parse(mmap_abs_path)
        except:
            return "File could not be parsed"

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

        return "Available registers below"

    def initialize(self):
        # Create a grid layout manager
        self.frame.grid()

        # Add the text box widget to the layout manager, stick to the East/West edges of the cell,
        # bind to an event when press enter to emulate the connect button, but bind also to mouse click to clear cells
        self.entry_box_port.grid(column=2, row=0, columnspan=3, sticky='EW', padx=10)
        self.entry_box_port.bind("<Button-1>", self.on_click_text_entry_box_port)
        self.entry_box_port.bind("<Return>", self.call_on_button_connect)
        self.entry_box_parity.grid(column=2, row=1, columnspan=3, sticky='EW', padx=10)
        self.entry_box_parity.bind("<Button-1>", self.on_click_text_entry_box_parity)
        self.entry_box_parity.bind("<Return>", self.call_on_button_connect)
        self.entry_box_baudrate.grid(column=2, row=2, columnspan=3, sticky='EW', padx=10)
        self.entry_box_baudrate.bind("<Button-1>", self.on_click_text_entry_box_baudrate)
        self.entry_box_baudrate.bind("<Return>", self.call_on_button_connect)
        self.entry_box_stopbits.grid(column=2, row=3, columnspan=3, sticky='EW', padx=10)
        self.entry_box_stopbits.bind("<Button-1>", self.on_click_text_entry_box_stopbits)
        self.entry_box_stopbits.bind("<Return>", self.call_on_button_connect)
        self.entry_box_bytesize.grid(column=2, row=4, columnspan=3, sticky='EW', padx=10)
        self.entry_box_bytesize.bind("<Button-1>", self.on_click_text_entry_box_bytesize)
        self.entry_box_bytesize.bind("<Return>", self.call_on_button_connect)

        self.entry_box_reg.grid(column=2, row=7, columnspan=3, sticky='EW', padx=10)
        self.entry_box_reg.bind("<Return>", self.call_on_button_send)
        self.entry_box_count.grid(column=2, row=8, columnspan=3, sticky='EW', padx=10)
        self.entry_box_count.bind("<Return>", self.call_on_button_send)
        self.entry_box_unit.grid(column=2, row=9, columnspan=3, sticky='EW', padx=10)
        self.entry_box_unit.bind("<Return>", self.call_on_button_send)
        self.entry_box_data.grid(column=2, row=10, columnspan=3, sticky='EW', padx=10)
        self.entry_box_data.bind("<Return>", self.call_on_button_send)
        self.entry_box_periodic.grid(column=2, row=11, columnspan=1, sticky='EW', padx=10)
        self.entry_box_data.bind("<Return>", self.call_on_button_send)

        # Create a simple button bind to an event handler
        button_connect = tk.Button(self.frame, textvariable=self.button_connect_text, command=self.on_button_connect)
        button_connect.grid(column=0, row=0, columnspan=2, sticky='EW')
        self.button_connect_text.set(u"CONNECT")

        # Place the store command button on my frame
        self.button_save.grid(column=7, row=10, columnspan=2, sticky='EW')
        self.button_save_text.set(u"SAVE COMMAND")

        # Initialize button to send request
        self.button_send_command.grid(column=7, row=11, columnspan=2, sticky='EW')
        self.button_send_command_text.set(u"SEND COMMAND ")

        # Create labels, black font and white background, text left-aligned ("w"),
        # expand the label across 2 cells in the grid layout manager (columnspan),
        # bind the variable tag to the widget

        label_port = tk.Label(self.frame, textvariable=self.label_port_text, anchor="w", fg="black", bg="white")
        label_port.grid(column=5, row=0, columnspan=4, sticky='EW')
        self.label_port_text.set(u"Serial Port")
        label_parity = tk.Label(self.frame, textvariable=self.label_parity_text, anchor="w", fg="black", bg="white")
        label_parity.grid(column=5, row=1, columnspan=4, sticky='EW')
        self.label_parity_text.set(u"(E)ven, (O)dd, (N)one")
        label_baudrate = tk.Label(self.frame, textvariable=self.label_baudrate_text, anchor="w", fg="black", bg="white")
        label_baudrate.grid(column=5, row=2, columnspan=4, sticky='EW')
        self.label_baudrate_text.set(u"Baud Rate")
        label_stopbits = tk.Label(self.frame, textvariable=self.label_stopbits_text, anchor="w", fg="black", bg="white")
        label_stopbits.grid(column=5, row=3, columnspan=4, sticky='EW')
        self.label_stopbits_text.set(u"Stop bits")
        label_bytesize = tk.Label(self.frame, textvariable=self.label_bytesize_text, anchor="w", fg="black", bg="white")
        label_bytesize.grid(column=5, row=4, columnspan=4, sticky='EW')
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

        # Label with periodic interval instructions
        label_periodic = tk.Label(self.frame, text=u"secs", fg="black", bg="white", width=5, anchor='w', justify='left')
        label_periodic.grid(column=3, row=11, columnspan=1, sticky='EW')

        # This is the connection status label
        label_connection = tk.Label(self.frame, textvariable=self.label_connection_text, anchor="w",
                                    fg="black", bg="grey")
        label_connection.grid(column=0, row=5, columnspan=8, sticky='EW')
        self.label_connection_text.set(u"Awaiting connection!")

        # This is the command status label (Request sent)
        label_command_send_hdr = tk.Label(self.frame, textvariable=self.label_command_send_hdr_text, anchor="w",
                                          fg="black", bg="white")
        label_command_send = tk.Label(self.frame, textvariable=self.label_command_send_text, anchor="w",
                                      fg="black", bg="grey")
        label_command_send_hdr.grid(column=0, row=17, columnspan=1, sticky='EW')
        label_command_send.grid(column=1, row=17, columnspan=7, sticky='EW')
        self.label_command_send_hdr_text.set(u"TX")
        self.label_command_send_text.set(u"Awaiting command")

        # This is the command status label (Receive response/exception)
        label_command_receive_hdr = tk.Label(self.frame, textvariable=self.label_command_receive_hdr_text, anchor="w",
                                             fg="black", bg="white")
        label_command_receive = tk.Label(self.frame, textvariable=self.label_command_receive_text, anchor="w",
                                         fg="black", bg="grey")
        label_command_receive_hdr.grid(column=0, row=18, columnspan=1, sticky='EW')
        label_command_receive.grid(column=1, row=18, columnspan=7, sticky='EW')
        self.label_command_receive_hdr_text.set(u"RX")
        self.label_command_receive_text.set(u"Awaiting response/exception")

        # Empty label, as I don't know how to place emtpy rows as Tkinter ignores it...
        tk.Label(self.frame, anchor="w", bg="white").grid(column=0, row=6, columnspan=8, sticky='EW')
        # tk.Label(self.frame, anchor="w", bg="white").grid(column=0, row=11, columnspan=8, sticky='EW')
        tk.Label(self.frame, anchor="w", bg="white").grid(column=0, row=13, columnspan=8, sticky='EW')
        tk.Label(self.frame, anchor="w", bg="white").grid(column=0, row=16, columnspan=8, sticky='EW')

        # Initialize radio buttons
        self.cmd_type_input.grid(column=7, row=7, sticky='W')
        self.cmd_type_holding.grid(column=7, row=8, sticky='W')
        self.cmd_type_write.grid(column=7, row=9, sticky='W')
        self.cmd_type_input.select()

        # Initialize lists and its scrollbar, create a label for the list and bind to events
        tk.Label(self.frame, anchor="w", bg="grey", text=self.initialize_mmap()).grid(column=0, row=14,
                                                                                      columnspan=3,
                                                                                      sticky='EW')
        self.list_mmap.grid(column=0, columnspan=3, row=15, sticky='WE')
        self.list_mmap.columnconfigure(0, weight=1)
        self.list_mmap_scrollbar.grid(column=0, sticky='EW')
        self.list_mmap.bind("<Double-Button-1>", self.on_double_click_list_mmap)

        self.checkbox_periodic_request.grid(column=0, row=11, columnspan=2, sticky='NW')

        # Initialize lists and its scrollbar, create a label for the list and bind to events
        tk.Label(self.frame, anchor="w", bg="grey", text=self.initialize_cmd()).grid(column=3, row=14,
                                                                                     columnspan=5,
                                                                                     sticky='EW')
        self.list_cmd.grid(column=3, columnspan=5, row=15, sticky='WE')
        self.list_cmd.columnconfigure(0, weight=1)
        self.list_cmd_scrollbar.grid(column=0, sticky='EW')
        self.list_cmd.bind("<Double-Button-1>", self.on_double_click_list_cmd)

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

    # Wrapper to call on_button_connect from triggers with associated events (like entry boxes)
    def call_on_button_connect(self, event):
        if not self.connected:
            self.on_button_connect()

    # Wrapper to call on_button_send from triggers
    def call_on_button_send(self, event):
        if self.connected:
            self.on_button_send()

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

    # Auxiliary function to retrieve request function code
    def create_outgoing_frame(self, a_unit, a_reg, a_count, a_data, a_type):
        if a_count is None:
            a_count = 0

        if isinstance(a_reg, str):
            a_reg = int(a_reg)-1
            a_reg = str(a_reg)

        tx_frame = '{0} {1} {2} '.format(str_hex(a_unit, 2), get_fc(a_type, a_count), str_hex(a_reg, 4))

        # Fill frame based on supported function code
        if a_type == mb_cmd[2]:
            # Write single register, as the data is sent as hexadecimal number, we need to convert to string
            if a_count == 1:
                tx_frame = tx_frame + "{0} ".format(str_hex(str(a_data), 4))

            # In case of multiple write:
            # ID + FC + Reg + Count + Count (bytes, 8-bit wide) + data
            else:
                tx_frame = tx_frame + "{0} {1} ".format(str_hex(a_count, 4), str_hex(str(int(a_count)*2), 2))
                for val in a_data:
                    tx_frame = tx_frame + "{0} ".format(str_hex(val, 4))

        # Read operation, in both holding/input register types the structure is the same
        else:
            tx_frame = tx_frame + "{0} ".format(str_hex(a_count, 4))

        # Calculate CRC and append
        crc_frame = tx_frame.replace(' ', '').decode('hex')
        tx_frame = tx_frame + '{0}'.format(str_hex(computeCRC(crc_frame), 4))
        # print tx_frame
        return tx_frame

    # Wrapper to launch the request after the checks have been done
    def execute_command(self, cmd, cmd_type, val):
        # Create a dictionary with the command types and corresponding functions to call
        cmd_key = {mb_cmd[0]: MB.read_input_registers,
                   mb_cmd[1]: MB.read_holding_registers}

        cmd_unit = self.entry_box_unit.get()
        cmd_reg = self.entry_box_reg.get()
        cmd_count = self.entry_box_count.get()

        if cmd == 'write' and val is not None:
            # Depending on the number of registers to write, use either write operation from MB
            if int(cmd_count) > 1:
                result = MB.write_registers(self.client, int(cmd_reg), val, int(cmd_unit))
            else:
                result = MB.write_single_register(self.client, int(cmd_reg), val[0], int(cmd_unit))

        elif cmd == 'read':
            # Retrieve the command type and call the corresponding function
            result = cmd_key[self.command_type.get()](self.client, int(cmd_reg), int(cmd_count), int(cmd_unit))
        else:
            result = None

        # Update TX label
        tx_frame = self.create_outgoing_frame(cmd_unit, cmd_reg, cmd_count, val, cmd_type)
        self.label_command_send_text.set("OK! - " + tx_frame)

        if result is None:
            self.toggle_mb_entries('normal')
            self.label_command_receive_text.set(u"FAIL, check if device is ON")
            return

        # Create single array to print result to user
        registers_result = ''
        base_cmd_register = int(self.entry_box_reg.get())

        if isinstance(result, WriteMultipleRegistersResponse):
            registers_result = "Wrote registers {0} to {1} Unit {2}".format(str(result.address),
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
                self.toggle_mb_entries('normal')
                self.label_command_send_text.set(u"TIMEOUT!")
                return

            for regs in result.registers:
                registers_result = registers_result + ' ' + str(base_cmd_register) + ':' + str(hex(regs)[2:].zfill(2))
                base_cmd_register += 1
            # Remove leading/ending spaces
            registers_result.strip()
            self.label_command_receive_text.set(registers_result)

        # If enabled, trigger the request again
        if self.checkbox_enabled.get():
            # Block the entry boxes
            self.periodic_enabled = True
            self.toggle_mb_entries('readonly')
            self.button_send_command_text.set(u"STOP PERIODIC")

            # Launch the request (broken)
            # self.master.after(20000, self.execute_command(cmd, val))
        else:
            self.toggle_mb_entries('normal')

    # Check if data on the MB cells are valid, returns None if anything wrong, else returns data to call
    # the execute_command method
    def check_valid_mb_info(self):
        # Check the content of the common fields
        if not self.entry_box_reg.get().isdigit() or \
           not self.entry_box_count.get().isdigit() or \
           not self.entry_box_unit.get().isdigit():
                self.label_command_send_text.set(u"Invalid data, Reg value/numbers, ID must be numbers")
                return None, None, None

        # Checks done on the periodic checkbox: empty, as strings are converted to integers, any floating number
        # will be rounded, so that's on the user side...
        if self.checkbox_enabled.get() and self.entry_box_periodic.get() is '':
            self.label_command_send_text.set(u"No periodic interval set")
            return None, None, None

        cmd_type = self.command_type.get()

        # Filter this as it has different arguments
        if cmd_type == mb_cmd[2]:

            # We cannot accept empty data fields or odd data i.e 004 (I don't want to pad, I'm a lazy fuck)
            if len(self.entry_box_data.get()) <= 0:
                self.label_command_send_text.set(u"Data values have to be even (not odd, zero)")
                return None, None, None

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
                    return None, None, None

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
                return None, None, None

            # Block MB fields
            self.toggle_mb_entries('readonly')
            return 'write', cmd_type, a_list
        else:
            self.toggle_mb_entries('readonly')
            return 'read', cmd_type, None

    # Event handler for clicking on the send request button
    def on_button_send(self):

        # Prevent eager users...
        if self.connected is False:
            self.label_connection_text.set(u"Not connected! connect first")
            return

        # If the periodic mode is enabled, then disable and remove lock
        if self.periodic_enabled is True:
            # Stop the timer

            # Clear the flag
            self.periodic_enabled = False

            # Enable the MB entry boxes and re-draw button
            self.toggle_mb_entries('normal')
            self.button_send_command_text.set(u'SEND COMMAND ')

            # And exit
            return

        # Re-set the TX/RX expected label
        self.label_command_receive_text.set(u"Awaiting response/exception")
        self.label_command_send_text.set(u"Awaiting command")

        cmd, cmd_type, data = self.check_valid_mb_info()

        if cmd is None:
            return

        self.execute_command(cmd, cmd_type, data)

    # Auxiliary function to clear text entry boxes
    def clear_boxes(self):
        self.entry_box_reg.delete(0, tk.END)
        self.entry_box_count.delete(0, tk.END)

    # This event is triggered by a double click, user selects a register from the memory map
    # and its content is updated in the command boxes
    def on_double_click_list_cmd(self, event):
        if not self.connected:
            return

        # Clear previous option
        self.clear_boxes()
        self.entry_box_unit.delete(0, tk.END)
        self.entry_box_data.delete(0, tk.END)

        # Get user input via event and populate box entries
        widget = event.widget
        selection = widget.curselection()
        value = widget.get(selection[0])

        self.entry_box_reg.insert(0, self.cmd_entries[value][0])
        self.entry_box_count.insert(0, self.cmd_entries[value][1])
        self.entry_box_unit.insert(0, self.cmd_entries[value][2])

        if self.cmd_entries[value][3] and self.cmd_entries[value][3] != "None":
            self.entry_box_data.insert(0, self.cmd_entries[value][3])

        self.radio_input_from_val(self.cmd_entries[value][4])

    # Auxiliary function to select the radio button option from a val
    def radio_input_from_val(self, val):
        if val == mb_cmd[0]:
            self.cmd_type_input.select()
        elif val == mb_cmd[1]:
            self.cmd_type_holding.select()
        elif val == mb_cmd[2]:
            self.cmd_type_write.select()

    # This event is triggered by a double click, user selects a register from the memory map
    # and its content is updated in the command boxes
    def on_double_click_list_mmap(self, event):
        if not self.connected:
            return

        # Clear previous option
        self.clear_boxes()

        # Get user input via event
        widget = event.widget
        selection = widget.curselection()
        value = widget.get(selection[0])

        self.entry_box_reg.insert(0, self.mmap_entries[value][0])
        self.entry_box_count.insert(0, self.mmap_entries[value][2])

        # If the register is an input/holding register, also select for the user
        self.radio_input_from_val(self.mmap_entries[value][1])

    # Auxiliary method that closes the pop-up window
    def close_pop_up(self):
        self.top.destroy()
        self.toggle_mb_entries('normal')

    # Creates the pop-up window for the user to save the command with a given name
    def popup(self):
        cmd, cmd_info, data = self.check_valid_mb_info()

        if cmd is None:
            return

        # Test if the data box entry is empty, then replace by a None
        data_field = "None"
        if self.entry_box_data.get():
            data_field = self.entry_box_data.get()

        # Create the command string
        cmd_in_string = "{0} {1} {2} {3} {4}\n".format(self.entry_box_reg.get(),
                                                       self.entry_box_count.get(),
                                                       self.entry_box_unit.get(),
                                                       data_field,
                                                       self.command_type.get())

        self.w = PopUpWindow(self.master, cmd_in_string, self.list_cmd, self.cmd_entries)
        self.master.wait_window(self.w.top)

        # After the pop-up window has been destroyed, restore the entry boxes and lists
        self.toggle_mb_entries('normal')

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