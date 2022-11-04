# rpypi
Raspberry Pypi — use packages without the excessive disk saturation

---

#### Proposed usage:
---
On the server side, we might prepare a server to serve import requests

```sh
$ rpypi-server --config <config file>
Serving multi-architecture python libraries at:
- unix:///var/run/rpypi.socket
- tcp:///0.0.0.0:3698
- http://0.0.0.0:36981
- tcp6:///[::]:36982
```

---

Then, on any network raspberry pi devices we would simply do:

```python
import rpypi; rpy.pi
# Now all of these can be remotely imported!
from tensorflow import *
from numpy import *
from rasa import *
from pandas import *
from matplotlib import *
```

> _Great, but why?_
I've been hacking on Raspberry Pi's for a long while now, and one of the most obnoxious things I experience is `ImportError` or `ModuleNotFound`. Instead, going forward I don't want to have to think about setting up an RPi's Python packages when I could install just one and never have to deal with the issue again. 
Moreover, this solution scales incredibly well when you can serve various different architectures, versions, and dynamically-linked modules when you can guarantee the CPU's will match the remote. 
This is where Rust comes in -- we would like to be able to serve on-demand modules that work across multiple versions and CPU architectures. 
To do this a few things are required: (1) hacking the system importer; (2) a file server; (3) a thicc disk; (4) some Monster energy drinks and a dream. 
