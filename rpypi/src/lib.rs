//! rpypi
//! Use the speed of Rust to serve dynamically importable
//! python packages over the network. 
//!
//! This concept was originally popularized by David Beazley 
//! and Brian K. Jones, and it deserves a "remaster" imo.

use pyo3::prelude::*;
use once_cell::unsync::Lazy;

const name_hack: &'str = r#"
# rpy was just imported 
# rpypi - secret rust hack is happening
# now that both are present, need to set 
# rpy.pi = an object whose __repr__ function
# value invokes `rpypi.install()` before returning (he he heh)
"#; 

struct UnpinPython(Python);


const py_hack = Lazy::new(|python: Python| {
    // Construct a hijacked Python instance 
    // and injects a second, shadowed module name
    // `rpy`.
    //
    // For this to work, we don't need to worry about 
    // the pointer to the Python object always being correct,
    // we just need to know how to get to it, hence box-pin.
    // When you box something, you move the value to the heap. 
    // The Box itself is just a pointer. 
    // The address of the pointer will move around, but the address 
    // of the data in the heap will not.
    let mut python = python;
    let py_box: Pin<Box<Python>> = Box::pin(python);
    todo!("Pass py_box to a raw handle that constructs a shadow module, 'rpy'");
    todo!("Get inner python handle as interior mut, staple on name_hack");
    PyModule::new(python, "rpypi")
});

#[pyclass(frozen)]
struct rpy {
}

impl rpy {
    fn pi(&self) -> PyResult<()> { Ok(()) }
}

