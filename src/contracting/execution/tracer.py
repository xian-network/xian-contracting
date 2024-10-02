import sys
import dis
import threading
import psutil
import os

# Define the opcode costs
cu_costs = {
    0: 2, 1: 2, 2: 4, 3: 4, 4: 4, 5: 4, 6: 4, 7: 4, 8: 4, 9: 2, 10: 2, 11: 4, 12: 2,
    13: 4, 14: 4, 15: 4, 16: 4, 17: 4, 18: 4, 19: 4, 20: 2, 21: 4, 22: 8, 23: 6, 24: 6,
    25: 4, 26: 4, 27: 4, 28: 4, 29: 4, 30: 4, 31: 6, 32: 6, 33: 6, 34: 2, 35: 6, 36: 6,
    37: 6, 38: 2, 39: 4, 40: 4, 41: 4, 42: 4, 43: 4, 44: 2, 45: 2, 46: 2, 47: 4, 48: 2,
    49: 6, 50: 6, 51: 6, 52: 6, 53: 4, 54: 6, 55: 4, 56: 4, 57: 4, 58: 4, 59: 4, 60: 4,
    61: 4, 62: 4, 63: 4, 64: 6, 65: 6, 66: 8, 67: 8, 68: 8, 69: 12, 70: 2, 71: 1610, 72: 8,
    73: 6, 74: 4, 75: 6, 76: 6, 77: 4, 78: 4, 79: 4, 80: 6, 81: 6, 82: 4, 83: 2, 84: 126,
    85: 1000, 86: 4, 87: 8, 88: 6, 89: 4, 90: 2, 91: 2, 92: 2, 93: 512, 94: 8, 95: 6, 96: 6,
    97: 4, 98: 4, 99: 2, 100: 2, 101: 2, 102: 2, 103: 6, 104: 8, 105: 8, 106: 4, 107: 4,
    108: 38, 109: 126, 110: 4, 111: 4, 112: 4, 113: 6, 114: 4, 115: 4, 116: 4, 117: 4, 118: 6,
    119: 6, 120: 4, 121: 4, 122: 4, 123: 6, 124: 32, 125: 2, 126: 2, 127: 4, 128: 4, 129: 4,
    130: 6, 131: 10, 132: 8, 133: 12, 134: 4, 135: 4, 136: 8, 137: 2, 138: 2, 139: 2, 140: 4,
    141: 6, 142: 12, 143: 6, 144: 2, 145: 8, 146: 8, 147: 6, 148: 2, 149: 6, 150: 6, 151: 6,
    152: 6, 153: 4, 154: 4, 155: 4, 156: 6, 157: 4, 158: 4, 159: 4, 160: 4, 161: 2, 162: 4,
    163: 6, 164: 6, 165: 6, 166: 6, 167: 2, 168: 4, 169: 4, 170: 2, 171: 8, 172: 2, 173: 4,
    174: 4, 175: 4, 176: 4, 177: 4, 178: 4, 179: 4, 180: 4, 255: 8
}

# Define maximum stamps
MAX_STAMPS = 6500000

class Tracer:
    def __init__(self):
        self.cost = 0
        self.stamp_supplied = 0
        self.last_frame_mem_usage = 0
        self.total_mem_usage = 0
        self.started = False
        self.call_count = 0
        self.max_call_count = 800000
        self.instruction_cache = {}
        self.lock = threading.Lock()

    def start(self):
        sys.settrace(self.trace_func)
        self.cost = 0
        self.call_count = 0
        self.started = True

    def stop(self):
        if self.started:
            sys.settrace(None)
            self.started = False

    def reset(self):
        self.stop()
        self.cost = 0
        self.stamp_supplied = 0
        self.last_frame_mem_usage = 0
        self.total_mem_usage = 0
        self.call_count = 0

    def set_stamp(self, stamp):
        self.stamp_supplied = stamp

    def add_cost(self, new_cost):
        self.cost += new_cost
        if self.cost > self.stamp_supplied or self.cost > MAX_STAMPS:
            self.stop()
            raise AssertionError("The cost has exceeded the stamp supplied!")

    def get_stamp_used(self):
        return self.cost

    def get_last_frame_mem_usage(self):
        return self.last_frame_mem_usage

    def get_total_mem_usage(self):
        return self.total_mem_usage

    def is_started(self):
        return self.started

    def get_memory_usage(self):
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        # Return the RSS (Resident Set Size)
        return mem_info.rss

    def trace_func(self, frame, event, arg):
        if event == 'line':
            self.call_count += 1
            if self.call_count > self.max_call_count:
                self.stop()
                raise AssertionError("Call count exceeded threshold! Infinite Loop?")

            # Check if the function matches the target module and function names
            code = frame.f_code
            current_function_name = code.co_name
            globals_dict = frame.f_globals
            module_name = globals_dict.get('__name__', '')

            # Only trace code within contracts (if '__contract__' in globals)
            if '__contract__' not in globals_dict:
                return

            # Get the opcode at the current instruction
            lasti = frame.f_lasti
            opcode = self.get_opcode(code, lasti)

            # Update memory usage
            if self.last_frame_mem_usage == 0:
                self.last_frame_mem_usage = self.get_memory_usage()

            new_memory_usage = self.get_memory_usage()
            if new_memory_usage > self.last_frame_mem_usage:
                self.total_mem_usage += (new_memory_usage - self.last_frame_mem_usage)
            self.last_frame_mem_usage = new_memory_usage

            # Check for memory usage limit (set an arbitrary limit, e.g., 500MB)
            if self.total_mem_usage > 500 * 1024 * 1024:
                self.stop()
                raise AssertionError(f"Transaction exceeded memory usage! Total usage: {self.total_mem_usage} bytes")

            # Add cost based on opcode
            opcode_cost = cu_costs.get(opcode, 1)  # Default cost if opcode not found
            self.cost += opcode_cost

            if self.cost > self.stamp_supplied or self.cost > MAX_STAMPS:
                self.stop()
                raise AssertionError("The cost has exceeded the stamp supplied!")

        return self.trace_func

    def get_opcode(self, code, offset):
        # Cache the instruction map per code object
        with self.lock:
            instruction_map = self.instruction_cache.get(code)
            if instruction_map is None:
                instruction_map = {}
                for instr in dis.get_instructions(code):
                    instruction_map[instr.offset] = instr.opcode
                self.instruction_cache[code] = instruction_map
            opcode = instruction_map.get(offset, None)
            if opcode is None:
                # Instruction not found; default to 0
                opcode = 0
            return opcode
