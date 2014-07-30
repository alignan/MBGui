#!/usr/bin/env python
#  -*- coding: utf-8 -*-

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