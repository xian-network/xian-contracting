#include "util.h"

#include "datastack.h"

#include "filedisp.h"

#include "tracer.h"

#include "structmember.h"

#include "frameobject.h"

#include <sys/resource.h>

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

unsigned long long cu_costs[] = {2, 4, 5, 2, 4, 1000, 1000, 1000, 2, 2, 3, 2, 1000, 1000, 4, 1000, 1000, 1000, 30, 3,
                                1000, 4, 3, 3, 3, 4, 4, 4, 5, 1000, 1000, 1000, 1000, 6, 30, 7, 12, 1000, 1610, 4, 7,
                                1000, 6, 6, 6, 6, 6, 2, 15, 15, 2, 126, 1000, 4, 4, 4, 4, 2, 2, 8, 8, 2, 6, 6, 4, 4,
                                1000, 2, 2, 2, 5, 8, 7, 4, 4, 38, 126, 4, 4, 4, 4, 4, 4, 3, 1000, 1000, 2, 4, 2, 3,
                                1000, 2, 2, 2, 1000, 1000, 1000, 5, 9, 7, 12, 1000, 7, 2, 2, 2, 1000, 1000, 12, 12, 15,
                                2, 8, 8, 5, 2, 5, 7, 9, 2, 8, 15, 30, 7, 8, 4};

unsigned long long MAX_STAMPS = 6500000;

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
  unsigned long long call_count; // Add this line to track call counts
}
Tracer;

static int
Tracer_init(Tracer * self, PyObject * args, PyObject * kwds) {
  //char *fname = getenv("CU_COST_FNAME");

  //read_cu_costs(fname, self->cu_costs); // Read cu cu_costs from ones interpreted in Python

  self -> started = 0;
  self -> cost = 0;
  self -> last_frame_mem_usage = 0;
  self -> total_mem_usage = 0;

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

static long get_memory_usage() {
  struct rusage r_usage;
  getrusage(RUSAGE_SELF, & r_usage);

  //    printf("%ld\n", r_usage.ru_maxrss);

  return r_usage.ru_maxrss;
}

static int
Tracer_trace(Tracer * self, PyFrameObject * frame, int what, PyObject * arg) {
    self->call_count++;
    printf("Call count: %llu\n", self->call_count);
    if (self->call_count > 150000) {
        PyErr_SetString(PyExc_AssertionError, "Call count exceeded threshold! Infinite Loop?");
        PyEval_SetTrace(NULL, NULL); // Stop tracing
        self->started = 0; // Mark tracer as stopped
        return RET_ERROR; // Use an appropriate return code
    }


    unsigned long long estimate = 0;
    unsigned long long factor = 1000;
    const char * str;
    // IF, Frame object globals contains __contract__ and it is true, continue
    PyObject * kv = PyUnicode_FromString("__contract__");
    PyObject * globals = PyFrame_GetGlobals(frame);
    int t = PyDict_Contains(globals, kv);
    Py_DECREF(globals);

    if (t != 1) {
      return RET_OK;
    }

    if (self -> last_frame_mem_usage == 0) {
      self -> last_frame_mem_usage = get_memory_usage();
    }

    int opcode;

    switch (what) {
    case PyTrace_LINE: /* 2 */ {
      PyObject * code = PyFrame_GetCode(frame); // Declare 'code' variable here
      const char * str = PyBytes_AS_STRING(PyCode_GetCode((PyCodeObject * ) code));
      Py_DECREF(code);
      int lasti = PyFrame_GetLasti(frame);
      opcode = str[lasti];

      if (opcode < 0) opcode = -opcode;

      estimate = (self -> cost + cu_costs[opcode]) / factor;
      estimate = estimate + 1;

      long new_memory_usage = get_memory_usage();

      if (new_memory_usage > self -> last_frame_mem_usage) {
        self -> total_mem_usage += (new_memory_usage - self -> last_frame_mem_usage);
        printf("[TRACER] TX total memory usage: %ld\n", self -> total_mem_usage);
      }

      self -> last_frame_mem_usage = new_memory_usage;

      //estimate = estimate * factor;
      if ((self -> cost > self -> stamp_supplied) || self -> cost > MAX_STAMPS) {
        PyErr_SetString(PyExc_AssertionError, "The cost has exceeded the stamp supplied!");
        PyEval_SetTrace(NULL, NULL);
        self -> started = 0;
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
          return RET_ERROR;
        }

        self -> cost += cu_costs[opcode];
        break;
      }
      default:
      break;
    }

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
