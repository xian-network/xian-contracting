#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <hdf5.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

// HDF5 Reference Manual: https://support.hdfgroup.org/HDF5/doc/RM/RM_H5Front.html

#define ATTR_LEN_MAX 64000 // http://davis.lbl.gov/Manuals/HDF5-1.8.7/UG/13_Attributes.html#SpecIssues
#define ATTR_VALUE "value"
#define ATTR_BLOCK "block"
#define LOCK_SUFFIX "-lock"
#define LOCK_TIMEOUT 10 // Timeout in seconds

static char dirname_buf[PATH_MAX + 1];

static void lock_acquire(char *filepath) {
    char dirname_buf[PATH_MAX] = {0}; // Ensure dirname_buf is defined locally or is reset before use

    // Construct the lock directory path
    strcat(dirname_buf, filepath);
    strcat(dirname_buf, LOCK_SUFFIX);

    // Try to acquire the lock normally first
    if (mkdir(dirname_buf, S_IRWXU) == 0) {
        printf("Lock acquired normally for %s\n", filepath);
        return; // Lock acquired successfully
    } else if (errno == EEXIST) {
        // The lock is already held, attempt to break it
        printf("Force acquiring lock, removing existing lock for %s\n", filepath);
        if (rmdir(dirname_buf) == 0) {
            // Successfully removed the existing lock, try to acquire again
            if (mkdir(dirname_buf, S_IRWXU) == 0) {
                printf("Lock force acquired for %s\n", filepath);
                return; // Lock acquired successfully after force
            } else {
                perror("Error force acquiring lock: ");
            }
        } else {
            perror("Error removing existing lock: ");
        }
    } else {
        perror("Error acquiring lock: ");
    }
}

static void lock_release(char *filepath) {
    char dirname_buf[PATH_MAX] = {0}; // Reset dirname_buf before use

    strcat(dirname_buf, filepath);
    strcat(dirname_buf, LOCK_SUFFIX);

    if (rmdir(dirname_buf) != 0) {
        perror("Error releasing lock: ");
    }

    // No need to memset dirname_buf here if it's defined locally or properly managed
}

static void
write_attr(hid_t gid, char *name, char *value)
{
    H5Adelete(gid, name);
    if(value)
    {
        hid_t atype = H5Tcopy(H5T_C_S1);
        H5Tset_size(atype, strlen(value));
        hid_t aid = H5Acreate(gid, name, atype, H5Screate(H5S_SCALAR), H5P_DEFAULT, H5P_DEFAULT);
        H5Awrite(aid, atype, value);
        H5Aclose(aid);
        H5Tclose(atype);
    }
}

static PyObject *
set(PyObject *self, PyObject *args)
{
#ifndef DEBUG
    H5Eset_auto2(H5P_DEFAULT, NULL, NULL);
#endif

    char *filepath, *group, *value, *blocknum;
    if(!PyArg_ParseTuple(args, "sszz", &filepath, &group, &value, &blocknum))
        return NULL;

    lock_acquire(filepath);

    hid_t fid = H5Fopen(filepath, H5F_ACC_RDWR, H5P_DEFAULT);
    if(fid < 0)
    {
        fid = H5Fcreate(filepath, H5F_ACC_EXCL, H5P_DEFAULT, H5P_DEFAULT);
        if(fid < 0)
        {
            lock_release(filepath);
            return PyErr_Format(PyExc_OSError, "failed to open/create file \"%s\"", filepath);
        }
    }

    hid_t gid = H5Gopen(fid, group, H5P_DEFAULT);
    if(gid < 0)
    {
        hid_t lcpl = H5Pcreate(H5P_LINK_CREATE);
        H5Pset_create_intermediate_group(lcpl, 1);
        gid = H5Gcreate(fid, group, lcpl, H5P_DEFAULT, H5P_DEFAULT);
        H5Pclose(lcpl);
    }

    write_attr(gid, ATTR_VALUE, value);
    write_attr(gid, ATTR_BLOCK, blocknum);

    H5Gclose(gid);
    H5Fclose(fid);

    lock_release(filepath);

    Py_RETURN_NONE;
}

static PyObject *
get_attr(char *filepath, char *group, char *name)
{
    static char buf[ATTR_LEN_MAX + 1];

    lock_acquire(filepath);

    hid_t fid = H5Fopen(filepath, H5F_ACC_RDONLY, H5P_DEFAULT);
    if(fid < 0)
    {
        lock_release(filepath);
        Py_RETURN_NONE;
    }

    hid_t aid = H5Aopen_by_name(fid, group, name, H5P_DEFAULT, H5P_DEFAULT);
    if(aid < 0)
    {
        H5Fclose(fid);
        lock_release(filepath);
        Py_RETURN_NONE;
    }

    hid_t atype = H5Tcopy(H5T_C_S1);
    H5Tset_size(atype, sizeof(buf));
    memset(buf, 0, sizeof(buf));
    if(H5Aread(aid, atype, buf) < 0)
    {
        H5Tclose(atype);
        H5Aclose(aid);
        H5Fclose(fid);
        lock_release(filepath);
        Py_RETURN_NONE;
    }

    H5Tclose(atype);
    H5Aclose(aid);
    H5Fclose(fid);

    lock_release(filepath);

    return PyUnicode_FromString(buf);
}

static PyObject *
get_value(PyObject *self, PyObject *args)
{
#ifndef DEBUG
    H5Eset_auto2(H5P_DEFAULT, NULL, NULL);
#endif

    char *filepath, *group;
    if(!PyArg_ParseTuple(args, "ss", &filepath, &group))
        return NULL;

    return get_attr(filepath, group, ATTR_VALUE);
}

static PyObject *
get_block(PyObject *self, PyObject *args)
{
#ifndef DEBUG
    H5Eset_auto2(H5P_DEFAULT, NULL, NULL);
#endif

    char *filepath, *group;
    if(!PyArg_ParseTuple(args, "ss", &filepath, &group))
        return NULL;

    return get_attr(filepath, group, ATTR_BLOCK);
}

static PyObject *
delete(PyObject *self, PyObject *args)
{
#ifndef DEBUG
    H5Eset_auto2(H5P_DEFAULT, NULL, NULL);
#endif

    char *filepath, *group;
    if(!PyArg_ParseTuple(args, "ss", &filepath, &group))
        return NULL;

    lock_acquire(filepath);

    hid_t fid = H5Fopen(filepath, H5F_ACC_RDWR, H5P_DEFAULT);
    hid_t gid = H5Gopen(fid, group, H5P_DEFAULT);
    H5Adelete(gid, ATTR_VALUE);
    H5Adelete(gid, ATTR_BLOCK);

    H5Gclose(gid);
    H5Fclose(fid);

    lock_release(filepath);

    Py_RETURN_NONE;
}

static herr_t
store_group_name(hid_t id, const char *name, const H5O_info_t *object_info, void *op_data)
{
    if(strcmp(name, ".") == 0 || object_info->num_attrs == 0)
        return 0;
    return PyList_Append((PyObject *) op_data, PyUnicode_FromString(name));
}

static PyObject *
get_groups(PyObject *self, PyObject *args)
{
#ifndef DEBUG
    H5Eset_auto2(H5P_DEFAULT, NULL, NULL);
#endif

    char *filepath;
    if(!PyArg_ParseTuple(args, "s", &filepath))
        return NULL;

    lock_acquire(filepath);

    hid_t fid = H5Fopen(filepath, H5F_ACC_RDONLY, H5P_DEFAULT);
    if(fid < 0)
    {
        lock_release(filepath);
        Py_RETURN_NONE;
    }

    PyObject *group_names = PyList_New(0);
#if (H5_VERS_MAJOR == 1 && H5_VERS_MINOR >= 12) || H5_VERS_MAJOR > 1
    if(H5Ovisit(fid, H5_INDEX_NAME, H5_ITER_NATIVE, store_group_name, group_names, H5O_INFO_ALL) < 0)
#else
    if(H5Ovisit(fid, H5_INDEX_NAME, H5_ITER_NATIVE, store_group_name, group_names) < 0)
#endif
    {
        H5Fclose(fid);
        lock_release(filepath);
        Py_RETURN_NONE;
    }

    H5Fclose(fid);

    lock_release(filepath);

    return group_names;
}

static PyMethodDef methods[] = {
    {"set",         set,        METH_VARARGS, "Set value"},
    {"get_value",   get_value,  METH_VARARGS, "Get value"},
    {"get_block",   get_block,  METH_VARARGS, "Get block"},
    {"delete",      delete,     METH_VARARGS, "Delete value & block"},
    {"get_groups",  get_groups, METH_VARARGS, "Get groups"}
};

static struct PyModuleDef h5cmodule = {
    PyModuleDef_HEAD_INIT,
    "h5c",
    NULL,
    -1,
    methods
};

PyMODINIT_FUNC
PyInit_h5c(void)
{
    return PyModule_Create(&h5cmodule);
}
