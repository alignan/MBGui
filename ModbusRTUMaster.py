#!/usr/bin/env python
#  -*- coding: utf-8 -*-

# Auxiliary class to handle Modbus transactions for Modbus GUI tool
#
# Copyright (C) 2014, Antonio Liñan,
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#  3. The names of its contributors may not be used to endorse or promote
#     products derived from this software without specific prior written
#     permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Any feedback is very welcome.
# https://github.com/alignan/MBGui

__author__ = "Antonio Lignan"

from pymodbus.client.sync import ModbusSerialClient as ModbusClient

# If we need to subtract from registers
offset = 1


# Modbus related part
def create_port(port, baudrate, parity, stopbits, bytesize):
    client = ModbusClient(method='rtu', timeout=0.5)
    client.port = port
    client.bytesize = bytesize
    client.stopbits = stopbits
    client.baudrate = baudrate
    client.parity = parity
    return client


# Will return TRUE if connected, FALSE otherwise
def connect(client):
    return client.connect()


# No return type
def close(client):
    return client.close()


# Reads the content of a read-only register
def read_input_registers(client, reg, count, unit):
    result = client.read_input_registers(reg-offset, count, unit=unit)
    return result


# Reads the content of a write/read register
def read_holding_registers(client, reg, count, unit):
    result = client.read_holding_registers(reg-offset, count, unit=unit)
    return result


# Writes to a single register
def write_single_register(client, reg, data, unit):
    result = client.write_register(reg-offset, data, unit=unit)
    return result


# Writes to a registers (multiple registers), receives a list
def write_registers(client, reg, data, unit):
    result = client.write_registers(reg-offset, data, unit=unit)
    return result