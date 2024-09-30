#include "util.h"

#include "datastack.h"

#include "filedisp.h"

#include "tracer.h"

#include "structmember.h"

#include "frameobject.h"

/* Conditional inclusion of sys/resource.h for Unix-like systems */
#ifndef _WIN32
#include <sys/resource.h>
#include <unistd.h>   // For Unix-like systems
#endif

#ifdef _WIN32
#include <windows.h>
#include <psapi.h>
#endif

#include "Python.h"

#include "compile.h"        /* in 2.3, this wasn't part of Python.h */

#include <stdio.h>          /* For reading CU cu_costs */

#include <stdlib.h>

#include <string.h>

/* Py 2.x and 3.x compatibility */

#ifndef Py_TYPE
#define Py_TYPE(o)(((PyObject * )(o)) -> ob_type)
#endif

#if PY_MAJOR_VERSION >= 3

#define MyType_HEAD_INIT PyVarObject_HEAD_INIT(NULL, 0)

#else

#define MyType_HEAD_INIT PyObject_HEAD_INIT(NULL) 0,

  #endif /* Py3k */

unsigned long long cu_costs[256] = {
    [0] = 2, [1] = 2, [2] = 4, [3] = 4, [4] = 4, [5] = 4, [6] = 4, [7] = 4, [8] = 4, [9] = 2, [10] = 2, [11] = 4, [12] = 2,
    [13] = 4, [14] = 4, [15] = 4, [16] = 4, [17] = 4, [18] = 4, [19] = 4, [20] = 2, [21] = 4, [22] = 8, [23] = 6, [24] = 6,
    [25] = 4, [26] = 4, [27] = 4, [28] = 4, [29] = 4, [30] = 4, [31] = 6, [32] = 6, [33] = 6, [34] = 2, [35] = 6, [36] = 6,
    [37] = 6, [38] = 2, [39] = 4, [40] = 4, [41] = 4, [42] = 4, [43] = 4, [44] = 2, [45] = 2, [46] = 2, [47] = 4, [48] = 2,
    [49] = 6, [50] = 6, [51] = 6, [52] = 6, [53] = 4, [54] = 6, [55] = 4, [56] = 4, [57] = 4, [58] = 4, [59] = 4, [60] = 4,
    [61] = 4, [62] = 4, [63] = 4, [64] = 6, [65] = 6, [66] = 8, [67] = 8, [68] = 8, [69] = 12, [70] = 2, [71] = 1610, [72] = 8,
    [73] = 6, [74] = 4, [75] = 6, [76] = 6, [77] = 4, [78] = 4, [79] = 4, [80] = 6, [81] = 6, [82] = 4, [83] = 2, [84] = 126,
    [85] = 1000, [86] = 4, [87] = 8, [88] = 6, [89] = 4, [90] = 2, [91] = 2, [92] = 2, [93] = 512, [94] = 8, [95] = 6, [96] = 6,
    [97] = 4, [98] = 4, [99] = 2, [100] = 2, [101] = 2, [102] = 2, [103] = 6, [104] = 8, [105] = 8, [106] = 4, [107] = 4,
    [108] = 38, [109] = 126, [110] = 4, [111] = 4, [112] = 4, [113] = 6, [114] = 4, [115] = 4, [116] = 4, [117] = 4, [118] = 6,
    [119] = 6, [120] = 4, [121] = 4, [122] = 4, [123] = 6, [124] = 32, [125] = 2, [126] = 2, [127] = 4, [128] = 4, [129] = 4,
    [130] = 6, [131] = 10, [132] = 8, [133] = 12, [134] = 4, [135] = 4, [136] = 8, [137] = 2, [138] = 2, [139] = 2, [140] = 4,
    [141] = 6, [142] = 12, [143] = 6, [144] = 2, [145] = 8, [146] = 8, [147] = 6, [148] = 2, [149] = 6, [150] = 6, [151] = 6,
    [152] = 6, [153] = 4, [154] = 4, [155] = 4, [156] = 6, [157] = 4, [158] = 4, [159] = 4, [160] = 4, [161] = 2, [162] = 4,
    [163] = 6, [164] = 6, [165] = 6, [166] = 6, [167] = 2, [168] = 4, [169] = 4, [170] = 2, [171] = 8, [172] = 2, [173] = 4,
    [174] = 4, [175] = 4, [176] = 4, [177] = 4, [178] = 4, [179] = 4, [180] = 4, [255] = 8
};

unsigned long long MAX_STAMPS = 6500000;

#define CRYPTO_MODULE_NAME "contracting.stdlib.bridge.crypto"
#define RANDOMX_FUNCTION_NAME "randomx_hash"

/* The Tracer type. */

typedef struct {
  PyObject_HEAD

  /* Variables to keep track of metering */
  unsigned long long cost;
  unsigned long long stamp_supplied;
  long last_frame_mem_usage;
  long total_mem_usage;
  int started;
  char * cu_cost_fname;
  unsigned long long process_id;
  unsigned long long call_count; // Add this line to track call counts
}
Tracer;

static int get_process_id() {
    #ifdef _WIN32
        DWORD pid = GetCurrentProcessId();
        return pid;
    #else
        pid_t pid = getpid();
        return pid;
    #endif
}

static int
Tracer_init(Tracer * self, PyObject * args, PyObject * kwds) {
  
  //char *fname = getenv("CU_COST_FNAME");

  //read_cu_costs(fname, self->cu_costs); // Read cu cu_costs from ones interpreted in Python

  self -> started = 0;
  self -> cost = 0;
  self -> last_frame_mem_usage = 0;
  self -> total_mem_usage = 0;
  self -> process_id = get_process_id();

  return RET_OK;
}

static void
Tracer_dealloc(Tracer * self) {
  if (self -> started) {
    PyEval_SetTrace(NULL, NULL);
  }

  Py_TYPE(self) -> tp_free((PyObject * ) self);
}

/*
 * The Trace Function
 */

/* Function to get memory usage */
static long get_memory_usage() {
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS_EX pmc;
    GetProcessMemoryInfo(GetCurrentProcess(), (PROCESS_MEMORY_COUNTERS*)&pmc, sizeof(pmc));
    return (long)pmc.PrivateUsage;  // Returns the Private Usage in bytes
#else
    struct rusage r_usage;
    getrusage(RUSAGE_SELF, &r_usage);
    return (long)r_usage.ru_maxrss;  // max resident set size
#endif
}

static int
Tracer_trace(Tracer * self, PyFrameObject * frame, int what, PyObject * arg) {

    self->call_count++;

    if (self->call_count > 800000) {
        PyErr_SetString(PyExc_AssertionError, "Call count exceeded threshold! Infinite Loop?");
        PyEval_SetTrace(NULL, NULL); // Stop tracing
        self->started = 0; // Mark tracer as stopped
        return RET_ERROR; // Use an appropriate return code
    }

    // Check if the current function matches the target module and function names
    PyCodeObject *code = PyFrame_GetCode(frame);
    if (code == NULL) {
        return RET_OK;
    }
    if (get_process_id() != self->process_id) {
        Py_DECREF(code);
        return RET_OK;
    }
    const char *current_function_name = PyUnicode_AsUTF8(code->co_name);
    if (current_function_name == NULL) {
        Py_DECREF(code);
        return RET_OK;
    }
    PyObject *globals = PyFrame_GetGlobals(frame);
    if (globals == NULL) {
        Py_DECREF(code);
        return RET_OK;
    }
    PyObject *module_name_obj = PyDict_GetItemString(globals, "__name__");
    if (module_name_obj == NULL) {
        Py_DECREF(globals);
        Py_DECREF(code);
        return RET_OK;
    }
    const char *current_module_name = PyUnicode_AsUTF8(module_name_obj);
    if (current_module_name == NULL) {
        Py_DECREF(globals);
        Py_DECREF(code);
        return RET_OK;
    }
    if (strcmp(current_function_name, RANDOMX_FUNCTION_NAME) == 0 &&
        strcmp(current_module_name, CRYPTO_MODULE_NAME) == 0) {
        self->cost += 100000; // Increment the cost by a specific value (e.g., 100)
    }


    unsigned long long estimate = 0;
    unsigned long long factor = 1000;
    const char * str;
    // IF, Frame object globals contains __contract__ and it is true, continue
    PyObject * kv = PyUnicode_FromString("__contract__");
    int t = PyDict_Contains(globals, kv);
    Py_DECREF(kv);

    if (t != 1) {
      Py_DECREF(globals);
      Py_DECREF(code);
      return RET_OK;
    }

    if (self -> last_frame_mem_usage == 0) {
      self -> last_frame_mem_usage = get_memory_usage();
    }

    int opcode;

    switch (what) {
    case PyTrace_LINE: /* 2 */ {
      const char * str = PyBytes_AS_STRING(PyCode_GetCode(code));
      int lasti = PyFrame_GetLasti(frame);
      opcode = str[lasti];

      if (opcode < 0) opcode = -opcode;
      estimate = (self -> cost + cu_costs[opcode]) / factor;
      estimate = estimate + 1;

      long new_memory_usage = get_memory_usage();

      if (new_memory_usage > self -> last_frame_mem_usage) {
        self -> total_mem_usage += (new_memory_usage - self -> last_frame_mem_usage);
      }

      self -> last_frame_mem_usage = new_memory_usage;

      //estimate = estimate * factor;
      if ((self -> cost > self -> stamp_supplied) || self -> cost > MAX_STAMPS) {
        PyErr_SetString(PyExc_AssertionError, "The cost has exceeded the stamp supplied!");
        PyEval_SetTrace(NULL, NULL);
        self -> started = 0;
        Py_DECREF(globals);
        Py_DECREF(code);
        return RET_ERROR;
      }

      #ifdef unix
      if (self -> total_mem_usage > 500000) {
        PyErr_Format(PyExc_AssertionError, "Transaction exceeded memory usage! Total usage: %ld kilobytes", self -> total_mem_usage);
        #else
        if (self -> total_mem_usage > 500000000) {
          PyErr_Format(PyExc_AssertionError, "Transaction exceeded memory usage! Total usage: %ld bytes", self -> total_mem_usage);
          #endif
          PyEval_SetTrace(NULL, NULL);
          self -> started = 0;
          Py_DECREF(globals);
          Py_DECREF(code);
          return RET_ERROR;
        }
        //printf("Opcode: %d\n Cost: %lld\n Total Cost: %lld\n", opcode, cu_costs[opcode], self -> cost);
        self -> cost += cu_costs[opcode];
        break;
      }
      default:
      break;
    }

    Py_DECREF(globals);
    Py_DECREF(code);
    return RET_OK;
    }

    static PyObject *
      Tracer_start(Tracer * self, PyObject * args) {
        PyEval_SetTrace((Py_tracefunc) Tracer_trace, (PyObject * ) self);
        self -> cost = 0;
        self->call_count = 0;
        self -> started = 1;
        return Py_BuildValue("");
      }

    static PyObject *
      Tracer_stop(Tracer * self, PyObject * args) {
        if (self -> started) {
          PyEval_SetTrace(NULL, NULL);
          self -> started = 0;
        }

        return Py_BuildValue("");
      }

    static PyObject *
      Tracer_set_stamp(Tracer * self, PyObject * args, PyObject * kwds) {
        PyArg_ParseTuple(args, "L", & self -> stamp_supplied);
        return Py_BuildValue("");
      }

    static PyObject *
      Tracer_reset(Tracer * self) {
        self -> cost = 0;
        self -> stamp_supplied = 0;
        self -> started = 0;
        self -> last_frame_mem_usage = 0;
        self -> total_mem_usage = 0;

        return Py_BuildValue("");
      }

    static PyObject *
      Tracer_add_cost(Tracer * self, PyObject * args, PyObject * kwds) {
        // This allows you to arbitrarily add to the cost variable from Python
        // Implemented for adding costs to database read / write operations
        unsigned long long new_cost;
        PyArg_ParseTuple(args, "L", & new_cost);
        self -> cost += new_cost;

        if (self -> cost > self -> stamp_supplied) {
          PyErr_SetString(PyExc_AssertionError, "The cost has exceeded the stamp supplied!\n");
          PyEval_SetTrace(NULL, NULL);
          self -> started = 0;
          return NULL;
        }

        return Py_BuildValue("");
      }

    static PyObject *
      Tracer_get_stamp_used(Tracer * self, PyObject * args, PyObject * kwds) {
        return Py_BuildValue("L", self -> cost);
      }

    static PyObject *
      Tracer_get_last_frame_mem_usage(Tracer * self, PyObject * args, PyObject * kwds) {
        return Py_BuildValue("L", self -> last_frame_mem_usage);
      }

    static PyObject *
      Tracer_get_total_mem_usage(Tracer * self, PyObject * args, PyObject * kwds) {
        return Py_BuildValue("L", self -> total_mem_usage);
      }

    static PyObject *
      Tracer_is_started(Tracer * self) {
        return Py_BuildValue("i", self -> started);
      }

    static PyMemberDef
    Tracer_members[] = {
      {
        "started",
        T_OBJECT,
        offsetof(Tracer, started),
        0,
        PyDoc_STR("Whether or not the tracer has been enabled")
      },
    };

    static PyMethodDef
    Tracer_methods[] = {
      {
        "start",
        (PyCFunction) Tracer_start,
        METH_VARARGS,
        PyDoc_STR("Start the tracer")
      },

      {
        "stop",
        (PyCFunction) Tracer_stop,
        METH_VARARGS,
        PyDoc_STR("Stop the tracer")
      },

      {
        "reset",
        (PyCFunction) Tracer_reset,
        METH_VARARGS,
        PyDoc_STR("Resets the tracer")
      },

      {
        "add_cost",
        (PyCFunction) Tracer_add_cost,
        METH_VARARGS,
        PyDoc_STR("Add to the cost. Throws AssertionError if cost exceeds stamps supplied.")
      },

      {
        "set_stamp",
        (PyCFunction) Tracer_set_stamp,
        METH_VARARGS,
        PyDoc_STR("Set the stamp before starting the tracer")
      },

      {
        "get_stamp_used",
        (PyCFunction) Tracer_get_stamp_used,
        METH_VARARGS,
        PyDoc_STR("Get the stamp usage after it's been completed")
      },

      {
        "get_last_frame_mem_usage",
        (PyCFunction) Tracer_get_last_frame_mem_usage,
        METH_VARARGS,
        PyDoc_STR("Get the memory usage of the last Python frame processed.")
      },

      {
        "get_total_mem_usage",
        (PyCFunction) Tracer_get_total_mem_usage,
        METH_VARARGS,
        PyDoc_STR("Get the total memory usage after it's been completed")
      },

      {
        "is_started",
        (PyCFunction) Tracer_is_started,
        METH_VARARGS,
        PyDoc_STR("Returns 1 if tracer is started, 0 if not.")
      },

      {
        NULL
      }
    };

    static PyTypeObject
    TracerType = {
        MyType_HEAD_INIT
        "contracting.execution.metering.tracer",    /*tp_name*/
        sizeof(Tracer),                             /*tp_basicsize*/
        0,                                          /*tp_itemsize*/
        (destructor)Tracer_dealloc,                 /*tp_dealloc*/
        0,                                          /*tp_print*/
        0,                                          /*tp_getattr*/
        0,                                          /*tp_setattr*/
        0,                                          /*tp_compare*/
        0,                                          /*tp_repr*/
        0,                                          /*tp_as_number*/
        0,                                          /*tp_as_sequence*/
        0,                                          /*tp_as_mapping*/
        0,                                          /*tp_hash */
        0,                                          /*tp_call*/
        0,                                          /*tp_str*/
        0,                                          /*tp_getattro*/
        0,                                          /*tp_setattro*/
        0,                                          /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,   /*tp_flags*/
        "Tracer objects",                           /* tp_doc */
        0,                                          /* tp_traverse */
        0,                                          /* tp_clear */
        0,                                          /* tp_richcompare */
        0,                                          /* tp_weaklistoffset */
        0,                                          /* tp_iter */
        0,                                          /* tp_iternext */
        Tracer_methods,                             /* tp_methods */
        Tracer_members,                             /* tp_members */
        0,                                          /* tp_getset */
        0,                                          /* tp_base */
        0,                                          /* tp_dict */
        0,                                          /* tp_descr_get */
        0,                                          /* tp_descr_set */
        0,                                          /* tp_dictoffset */
        (initproc)Tracer_init,                      /* tp_init */
        0,                                          /* tp_alloc */
        0,                                          /* tp_new */
    };

    /* Module definition */

    #define MODULE_DOC PyDoc_STR("Fast tracer for Smart Contract metering.")

    #if PY_MAJOR_VERSION >= 3

    static PyModuleDef
    moduledef = {
      PyModuleDef_HEAD_INIT,
      "contracting.execution.metering.tracer",
      MODULE_DOC,
      -1,
      NULL,
      /* methods */
      NULL,
      NULL,
      /* traverse */
      NULL,
      /* clear */
      NULL
    };

    PyObject *
      PyInit_tracer(void) {
        Py_Initialize();
        PyObject * mod = PyModule_Create( & moduledef);

        if (mod == NULL) {
          Py_DECREF(mod);
          return NULL;
        }

        TracerType.tp_new = PyType_GenericNew;

        if (PyType_Ready( & TracerType) < 0) {
          Py_DECREF(mod);
          Py_DECREF( & TracerType);
          printf("Not ready");
          return NULL;
        }

        PyModule_AddObject(mod, "Tracer", (PyObject * ) & TracerType);
        return mod;
      }

    #else

    void
    inittracer(void) {
      PyObject * mod;
      mod = Py_InitModule3("contracting.execution.metering.tracer", NULL, MODULE_DOC);

      if (mod == NULL) {
        Py_DECREF(mod);
        return;
      }

      TracerType.tp_new = PyType_GenericNew;
      if (PyType_Ready( & TracerType) < 0) {
        Py_DECREF(mod);
        Py_DECREF( & TracerType);
        return;
      }

      PyModule_AddObject(mod, "Tracer", (PyObject * ) & TracerType);
    }

    #endif /* Py3k */
