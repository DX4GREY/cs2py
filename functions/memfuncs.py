import struct
import pymem
from pymem.process import module_from_name
from ext.datatypes import *


def GetProcess(procname):
    proc = pymem.Pymem(procname)
    return proc

def GetModuleBase(modulename: str, process_object: pymem.Pymem):
    if not modulename or not process_object:
        return None
    module = module_from_name(process_object.process_handle, modulename)
    if module:
        return module.lpBaseOfDll
    return None

class ProcMemHandler:

    @staticmethod
    def ReadPointer(proc, address):
        return proc.read_longlong(address)

    @staticmethod
    def ReadBytes(proc, address, bytes_count):
        return proc.read_bytes(address, bytes_count)

    @staticmethod
    def WriteBytes(proc, address, newbytes):
        return proc.write_bytes(address, newbytes, len(newbytes))

    @staticmethod
    def ReadInt(proc, address):
        return proc.read_int(address)

    @staticmethod
    def ReadLong(proc, address):
        return proc.read_longlong(address)

    @staticmethod
    def ReadFloat(proc, address):
        return proc.read_float(address)

    @staticmethod
    def ReadDouble(proc, address):
        return proc.read_double(address)

    @staticmethod
    def ReadVec(proc, address):
        bytes_ = ProcMemHandler.ReadBytes(proc, address, 12)
        x, y, z = struct.unpack('fff', bytes_)
        return Vector3(x, y, z)

    @staticmethod
    def ReadShort(proc, address):
        bytes_ = ProcMemHandler.ReadBytes(proc, address, 2)
        return struct.unpack('h', bytes_)[0]

    @staticmethod
    def ReadUShort(proc, address):
        bytes_ = ProcMemHandler.ReadBytes(proc, address, 2)
        return struct.unpack('H', bytes_)[0]

    @staticmethod
    def ReadUInt(proc, address):
        return proc.read_uint(address)

    @staticmethod
    def ReadULong(proc, address):
        bytes_ = ProcMemHandler.ReadBytes(proc, address, 8)
        return struct.unpack('Q', bytes_)[0]

    @staticmethod
    def ReadBool(proc, address):
        return proc.read_bool(address)

    @staticmethod
    def ReadString(proc, address, length):
        return proc.read_string(address, length)

    @staticmethod
    def ReadChar(proc, address):
        bytes_ = ProcMemHandler.ReadBytes(proc, address, 2)
        return struct.unpack('c', bytes_)[0].decode('utf-8')

    @staticmethod
    def ReadMatrix(proc, address):
        bytes_ = ProcMemHandler.ReadBytes(proc, address, 4 * 16)
        matrix = struct.unpack('16f', bytes_)
        matrix = Matrix([
        [matrix[0], matrix[1], matrix[2], matrix[3]],
        [matrix[4], matrix[5], matrix[6], matrix[7]],
        [matrix[8], matrix[9], matrix[10], matrix[11]],
        [matrix[12], matrix[13], matrix[14], matrix[15]]])
        return matrix

    @staticmethod
    def WriteInt(proc, address, value):
        return proc.write_int(address, value)

    @staticmethod
    def WriteShort(proc, address, value):
        bytes_ = struct.pack('h', value)
        return ProcMemHandler.WriteBytes(proc, address, bytes_)

    @staticmethod
    def WriteUShort(proc, address, value):
        bytes_ = struct.pack('H', value)
        return ProcMemHandler.WriteBytes(proc, address, bytes_)

    @staticmethod
    def WriteUInt(proc, address, value):
        return proc.write_uint(address, value)

    @staticmethod
    def WriteLong(proc, address, value):
        return proc.write_longlong(address, value)

    @staticmethod
    def WriteULong(proc, address, value):
        bytes_ = struct.pack('Q', value)
        return ProcMemHandler.WriteBytes(proc, address, bytes_)

    @staticmethod
    def WriteFloat(proc, address, value):
        return proc.write_float(address, value)

    @staticmethod
    def WriteDouble(proc, address, value):
        return proc.write_double(address, value)

    @staticmethod
    def WriteBool(proc, address, value):
        return proc.write_bool(address, value)

    @staticmethod
    def WriteString(proc, address, value):
        return proc.write_string(address, value)

    @staticmethod
    def WriteVec(proc, address, value):
        bytes_ = struct.pack('fff', value.x, value.y, value.z)
        return ProcMemHandler.WriteBytes(proc, address, bytes_)


def get_spectator_list(proc, clientBaseAddress, Offsets, local_controller_address, local_team):
    spectators = []
    try:
        EntityList = ProcMemHandler.ReadPointer(proc, clientBaseAddress + Offsets.offset.dwEntityList)
        # resolve local pawn address for comparison
        local_pawn = ProcMemHandler.ReadPointer(proc, clientBaseAddress + Offsets.offset.dwLocalPlayerPawn)
    except Exception:
        return spectators

    try:
        for i in range(64):
            try:
                ListEntry = ProcMemHandler.ReadPointer(proc, EntityList + (8 * (i & 0x7FFF) >> 9) + 16)
                if not ListEntry:
                    continue

                controller = ProcMemHandler.ReadPointer(proc, ListEntry + 112 * (i & 0x1FF))
                if not controller or controller == local_controller_address:
                    continue

                # get pawn handle from controller
                try:
                    pawnHandle = ProcMemHandler.ReadInt(proc, controller + Offsets.offset.m_hPlayerPawn)
                except Exception:
                    pawnHandle = 0
                if not pawnHandle:
                    continue

                # resolve pawn pointer from entity list
                ListEntry2 = ProcMemHandler.ReadPointer(proc, EntityList + 0x8 * ((pawnHandle & 0x7FFF) >> 9) + 0x10)
                if not ListEntry2:
                    continue

                pawn = ProcMemHandler.ReadPointer(proc, ListEntry2 + 0x70 * (pawnHandle & 0x1FF))
                if not pawn:
                    continue

                # read observer services from controller
                try:
                    observer_services = ProcMemHandler.ReadPointer(proc, controller + Offsets.offset.m_pObserverServices)
                except Exception:
                    observer_services = 0
                if not observer_services:
                    continue

                # read observer target handle
                try:
                    observer_target = ProcMemHandler.ReadInt(proc, observer_services + Offsets.offset.m_hObserverTarget)
                except Exception:
                    observer_target = 0
                if not observer_target:
                    continue

                # resolve observer target controller/pawn pointer
                target_entry = ProcMemHandler.ReadPointer(proc, EntityList + 0x8 * ((observer_target & 0x7FFF) >> 9) + 0x10)
                if not target_entry:
                    continue
                target_controller = ProcMemHandler.ReadPointer(proc, target_entry + 0x70 * (observer_target & 0x1FF))
                if not target_controller:
                    continue

                # if the target controller/pawn equals our local controller, this controller is spectating us
                if target_controller == local_controller_address:
                    # get name
                    try:
                        name_addr = ProcMemHandler.ReadPointer(proc, controller + Offsets.offset.m_sSanitizedPlayerName)
                        name = ProcMemHandler.ReadString(proc, name_addr, 64) if name_addr else None
                        if name:
                            spectators.append(name.strip())
                    except Exception:
                        continue
            except Exception:
                continue
    except Exception:
        return spectators

    return spectators
