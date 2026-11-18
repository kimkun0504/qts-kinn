"""The Lab: the owner's own algorithms, run on every stock (decision 0023, docs/LAB.md).

An algorithm is Python code with a ``signal(data)`` function. The Lab loads the data through the
sealed store (``data``), runs the code in a worker process (``worker``), checks it for lookahead
(``algorithm``), turns its signals into trades under one set of rules (``engine``), builds a
book (``book``) and summarises the result (``metrics``). ``store`` keeps the algorithms and the
runs in the Lab folder.
"""
