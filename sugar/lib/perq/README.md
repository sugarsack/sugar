# Persistent Queue

In order to keep client continue running tasks in background even if
client restarted (or crashed). For this, persistent Queue helps keep
track of tasks that was not completed.

There is production ready alternative implementation:
[`persist-queue`](https://pypi.org/project/persist-queue/). It allows
keep queue data in file system as files or in SQLite
database. However, only SQLite-based version is semi-working as it is
needed and it still suffering with the time lagging. It is also
polling based.

In Sugar Project, queue should be able to have realtime reaction
between multi processes through the disk, where data is stored.

## Variants

Persistent Queue has two modes of working:

- Poll based. This is useful when two distant systems are sharing the
  same directory to store and retrieve data. Default poll is each 5
  seconds.

- Message based. This is useful to communicate between child forked
  daemon subprocess, which supposed to pick up a message data and
  process it accordingly.

# Usage Example

Note: make sure queue's data store has proper permissions. Internally
it is using _either_ `pickle` (default) or `msgpack` (optional). Use
of `pickle` is default, because it allows to serialise arbitrary
Python object just like that. But it is a little bit slower, which is
still not a problem for Sugar Project in this use case. In some cases,
where messages are merely JSON-like, `msgpack` is sufficient, as it
has significantly faster serialisation (dumping) speed.

## Polling

This is an example how one process can send and another can receive
messages. Both processes can be restarted any time.

Sender:

```python
import time
from sugar.lib.perq.fsqueue import FSQueue

fs = FSQueue("/tmp/data")
while True:
    obj = str(time.time())
    fs.put(obj)
    time.sleep(0.5)
    print("Put object", obj)
```

Receiver:

```python
from sugar.lib.perq.fsqueue import FSQueue

fs = FSQueue("/tmp/data")
while True:
    print(fs.get())

```

In the above example typically there will be written five to six
objects, then after five seconds receiver will read all of them.

## Notification

This is an example how process can send data to its sub-process and
communicate instantly. Both process and sub-process can be restarted
at any time.

Process/Sub-process:

```python
from sugar.lib.perq.fsqueue import FSQueue
import multiprocessing
import time

fsq = FSQueue("/tmp/data").use_notify(multiprocessing.Queue())

def sender():
    while True:
        obj = str(time.time())
        fsq.put(obj)
        print("Put:", obj)
        time.sleep(1)


def receiver():
    while True:
        print(fsq.get())


snd = multiprocessing.Process(target=sender)
snd.start()

rcv = multiprocessing.Process(target=receiver)
rcv.start()
rcv.join()
```

In this example sub-process will read the disk with the data righ
after anything was put there and it behaves and feels like just a
typical `multiprocessing.Queue`, except the unprocessed data is not
lost and can be picked later, in case sub-process crashed.
