import sys
import dis
import threading
import psutil
import os

cu_costs = {
    dis.opmap.get('NOP', 0): 1,
    dis.opmap.get('POP_TOP', 1): 1,
    dis.opmap.get('PUSH_NULL', 2): 1,
    dis.opmap.get('INTERPRETER_EXIT', 3): 1,
    dis.opmap.get('END_FOR', 4): 1,
    dis.opmap.get('BINARY_OP', 5): 2,
    dis.opmap.get('LOAD_SUPER_ATTR', 6): 2,
    dis.opmap.get('LOAD_FAST', 7): 1,
    dis.opmap.get('STORE_FAST', 8): 1,
    dis.opmap.get('DELETE_FAST', 9): 1,
    dis.opmap.get('LOAD_CONST', 10): 1,
    dis.opmap.get('LOAD_NAME', 11): 2,
    dis.opmap.get('STORE_NAME', 12): 2,
    dis.opmap.get('DELETE_NAME', 13): 2,
    dis.opmap.get('LOAD_GLOBAL', 14): 2,
    dis.opmap.get('STORE_GLOBAL', 15): 2,
    dis.opmap.get('DELETE_GLOBAL', 16): 2,
    dis.opmap.get('LOAD_ATTR', 17): 2,
    dis.opmap.get('STORE_ATTR', 18): 2,
    dis.opmap.get('DELETE_ATTR', 19): 2,
    dis.opmap.get('LOAD_METHOD', 20): 2,
    dis.opmap.get('CALL_METHOD', 21): 2,
    dis.opmap.get('IMPORT_NAME', 22): 10,
    dis.opmap.get('IMPORT_FROM', 23): 4,
    dis.opmap.get('JUMP_FORWARD', 24): 1,
    dis.opmap.get('JUMP_IF_FALSE_OR_POP', 25): 1,
    dis.opmap.get('JUMP_IF_TRUE_OR_POP', 26): 1,
    dis.opmap.get('JUMP_ABSOLUTE', 27): 1,
    dis.opmap.get('POP_JUMP_IF_FALSE', 28): 1,
    dis.opmap.get('POP_JUMP_IF_TRUE', 29): 1,
    dis.opmap.get('LOAD_BUILD_CLASS', 30): 2,
    dis.opmap.get('RETURN_VALUE', 31): 1,
    dis.opmap.get('YIELD_VALUE', 32): 2,
    dis.opmap.get('YIELD_FROM', 33): 2,
    dis.opmap.get('SETUP_ANNOTATIONS', 34): 1,
    dis.opmap.get('IMPORT_STAR', 35): 10,
    dis.opmap.get('POP_BLOCK', 36): 1,
    dis.opmap.get('POP_EXCEPT', 37): 1,
    dis.opmap.get('STORE_NAME', 38): 2,
    dis.opmap.get('DELETE_NAME', 39): 2,
    dis.opmap.get('UNPACK_SEQUENCE', 40): 2,
    dis.opmap.get('FOR_ITER', 41): 2,
    dis.opmap.get('UNPACK_EX', 42): 2,
    dis.opmap.get('STORE_ATTR', 43): 2,
    dis.opmap.get('DELETE_ATTR', 44): 2,
    dis.opmap.get('STORE_GLOBAL', 45): 2,
    dis.opmap.get('DELETE_GLOBAL', 46): 2,
    dis.opmap.get('LOAD_CONST', 47): 1,
    dis.opmap.get('LOAD_NAME', 48): 2,
    dis.opmap.get('BUILD_TUPLE', 49): 2,
    dis.opmap.get('BUILD_LIST', 50): 2,
    dis.opmap.get('BUILD_SET', 51): 2,
    dis.opmap.get('BUILD_MAP', 52): 2,
    dis.opmap.get('BUILD_CONST_KEY_MAP', 53): 2,
    dis.opmap.get('BUILD_STRING', 54): 2,
    dis.opmap.get('BUILD_TUPLE_UNPACK', 55): 3,
    dis.opmap.get('BUILD_LIST_UNPACK', 56): 3,
    dis.opmap.get('BUILD_SET_UNPACK', 57): 3,
    dis.opmap.get('BUILD_MAP_UNPACK', 58): 3,
    dis.opmap.get('BUILD_MAP_UNPACK_WITH_CALL', 59): 3,
    dis.opmap.get('LOAD_ATTR', 60): 2,
    dis.opmap.get('COMPARE_OP', 61): 2,
    dis.opmap.get('IMPORT_NAME', 62): 10,
    dis.opmap.get('IMPORT_FROM', 63): 4,
    dis.opmap.get('JUMP_FORWARD', 64): 1,
    dis.opmap.get('JUMP_IF_FALSE_OR_POP', 65): 1,
    dis.opmap.get('JUMP_IF_TRUE_OR_POP', 66): 1,
    dis.opmap.get('JUMP_ABSOLUTE', 67): 1,
    dis.opmap.get('POP_JUMP_IF_FALSE', 68): 1,
    dis.opmap.get('POP_JUMP_IF_TRUE', 69): 1,
    dis.opmap.get('LOAD_GLOBAL', 70): 2,
    dis.opmap.get('SETUP_FINALLY', 71): 4,
    dis.opmap.get('LOAD_FAST', 72): 1,
    dis.opmap.get('STORE_FAST', 73): 1,
    dis.opmap.get('DELETE_FAST', 74): 1,
    dis.opmap.get('LOAD_CONST', 75): 1,
    dis.opmap.get('LOAD_NAME', 76): 2,
    dis.opmap.get('BUILD_TUPLE', 77): 2,
    dis.opmap.get('BUILD_LIST', 78): 2,
    dis.opmap.get('BUILD_SET', 79): 2,
    dis.opmap.get('BUILD_MAP', 80): 2,
    dis.opmap.get('LOAD_ATTR', 81): 2,
    dis.opmap.get('COMPARE_OP', 82): 2,
    dis.opmap.get('IMPORT_NAME', 83): 10,
    dis.opmap.get('IMPORT_FROM', 84): 4,
    dis.opmap.get('JUMP_FORWARD', 85): 1,
    dis.opmap.get('JUMP_IF_FALSE_OR_POP', 86): 1,
    dis.opmap.get('JUMP_IF_TRUE_OR_POP', 87): 1,
    dis.opmap.get('JUMP_ABSOLUTE', 88): 1,
    dis.opmap.get('POP_JUMP_IF_FALSE', 89): 1,
    dis.opmap.get('POP_JUMP_IF_TRUE', 90): 1,
    dis.opmap.get('LOAD_GLOBAL', 91): 2,
    dis.opmap.get('SETUP_FINALLY', 92): 4,
    dis.opmap.get('STORE_ATTR', 93): 2,
    dis.opmap.get('DELETE_ATTR', 94): 2,
    dis.opmap.get('STORE_GLOBAL', 95): 2,
    dis.opmap.get('DELETE_GLOBAL', 96): 2,
    dis.opmap.get('ROT_TWO', 97): 1,
    dis.opmap.get('ROT_THREE', 98): 1,
    dis.opmap.get('ROT_FOUR', 99): 1,
    dis.opmap.get('LOAD_CONST', 100): 1,
    dis.opmap.get('LOAD_NAME', 101): 2,
    dis.opmap.get('BUILD_TUPLE', 102): 2,
    dis.opmap.get('BUILD_LIST', 103): 2,
    dis.opmap.get('BUILD_SET', 104): 2,
    dis.opmap.get('BUILD_MAP', 105): 2,
    dis.opmap.get('LOAD_ATTR', 106): 2,
    dis.opmap.get('COMPARE_OP', 107): 2,
    dis.opmap.get('IMPORT_NAME', 108): 10,
    dis.opmap.get('IMPORT_FROM', 109): 4,
    dis.opmap.get('JUMP_FORWARD', 110): 1,
    dis.opmap.get('JUMP_IF_FALSE_OR_POP', 111): 1,
    dis.opmap.get('JUMP_IF_TRUE_OR_POP', 112): 1,
    dis.opmap.get('JUMP_ABSOLUTE', 113): 1,
    dis.opmap.get('POP_JUMP_IF_FALSE', 114): 1,
    dis.opmap.get('POP_JUMP_IF_TRUE', 115): 1,
    dis.opmap.get('LOAD_GLOBAL', 116): 2,
    dis.opmap.get('SETUP_FINALLY', 117): 4,
    dis.opmap.get('CALL_FUNCTION', 118): 2,
    dis.opmap.get('MAKE_FUNCTION', 119): 4,
    dis.opmap.get('BUILD_SLICE', 120): 2,
    dis.opmap.get('EXTENDED_ARG', 121): 1,
    dis.opmap.get('FORMAT_VALUE', 122): 2,
    dis.opmap.get('MATCH_MAPPING', 123): 2,
    dis.opmap.get('MATCH_SEQUENCE', 124): 2,
    dis.opmap.get('MATCH_KEYS', 125): 2,
    dis.opmap.get('COPY_DICT_WITHOUT_KEYS', 126): 2,
    dis.opmap.get('WITH_EXCEPT_START', 127): 4,
    dis.opmap.get('GET_AITER', 128): 2,
    dis.opmap.get('GET_ANEXT', 129): 2,
    dis.opmap.get('BEFORE_ASYNC_WITH', 130): 2,
    dis.opmap.get('END_ASYNC_FOR', 131): 2,
    dis.opmap.get('STORE_FAST', 132): 1,
    dis.opmap.get('DELETE_FAST', 133): 1,
    dis.opmap.get('LOAD_FAST', 134): 1,
    dis.opmap.get('LIST_TO_TUPLE', 135): 1,
    dis.opmap.get('RETURN_GENERATOR', 136): 1,
    dis.opmap.get('LOAD_ASSERTION_ERROR', 137): 1,
    dis.opmap.get('RETURN_VALUE', 138): 1,
    dis.opmap.get('PREP_RERAISE_STAR', 139): 1,
    dis.opmap.get('POP_EXCEPT_AND_RERAISE', 140): 1,
    dis.opmap.get('LOAD_GLOBAL', 141): 2,
    dis.opmap.get('LOAD_FAST', 142): 1,
    dis.opmap.get('STORE_FAST', 143): 1,
    dis.opmap.get('DELETE_FAST', 144): 1,
    dis.opmap.get('RAISE_VARARGS', 145): 2,
    dis.opmap.get('CALL_FUNCTION_EX', 146): 4,
    dis.opmap.get('SETUP_ANNOTATIONS', 147): 1,
    dis.opmap.get('STORE_LOCALS', 148): 1,
    dis.opmap.get('LOAD_LOCALS', 149): 1,
    dis.opmap.get('COMPARE_OP', 150): 2,
    dis.opmap.get('IS_OP', 151): 2,
    dis.opmap.get('CONTAINS_OP', 152): 2,
    dis.opmap.get('JUMP_IF_NOT_EXC_MATCH', 153): 2,
    dis.opmap.get('LOAD_METHOD', 154): 2,
    dis.opmap.get('CALL_METHOD', 155): 2,
    dis.opmap.get('LIST_EXTEND', 156): 2,
    dis.opmap.get('SET_UPDATE', 157): 2,
    dis.opmap.get('DICT_MERGE', 158): 2,
    dis.opmap.get('DICT_UPDATE', 159): 2,
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
        self.instruction_cache.clear()  # Clear the instruction cache to prevent memory leaks

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
        return mem_info.rss

    def trace_func(self, frame, event, arg):
        if event == 'line':
            self.call_count += 1
            if self.call_count > self.max_call_count:
                self.stop()
                raise AssertionError("Call count exceeded threshold! Infinite Loop?")

            code = frame.f_code
            globals_dict = frame.f_globals

            # Only trace code within contracts
            if '__contract__' not in globals_dict:
                return

            lasti = frame.f_lasti
            opcode = self.get_opcode(code, lasti)

            new_memory_usage = self.get_memory_usage()
            if self.last_frame_mem_usage == 0:
                self.last_frame_mem_usage = new_memory_usage

            # Track incremental memory usage
            if new_memory_usage > self.last_frame_mem_usage:
                self.total_mem_usage += (new_memory_usage - self.last_frame_mem_usage)
            self.last_frame_mem_usage = new_memory_usage

            # Memory usage limit
            if self.total_mem_usage > 500 * 1024 * 1024:
                self.stop()
                raise AssertionError(f"Transaction exceeded memory usage! Total usage: {self.total_mem_usage} bytes")

            # Add cost based on opcode
            opcode_cost = cu_costs.get(opcode, 1)
            self.add_cost(opcode_cost)

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
            return instruction_map.get(offset, 0)
