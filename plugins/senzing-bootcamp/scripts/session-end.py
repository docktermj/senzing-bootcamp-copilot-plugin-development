#!/usr/bin/env python3
"""sessionEnd hook: to preserve your in-progress recap when the session ends.

When a bootcamp is active, fold the in-progress module recap checkpoint into
docs/bootcamp_recap.md so quitting mid-module never loses that module's narrative
(deterministic, idempotent, append-only — see recap_checkpoint.py), and stop any
container the bootcamp started so it does not linger after exit, using the runtime
CLI recorded with it (``<runtime> stop``, never remove, so it can be restarted on
resume — see docker_lifecycle.py, INV-101). Silent and non-blocking: it emits no
output, and every container step is optional and warns-and-continues when that
runtime's CLI is absent or errors.

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the
interpreter and this script, quoted (``python3 "<path>"``), per INV-052. Python is already a hard bootcamp dependency.
"""
import sys

import docker_lifecycle
import recap_checkpoint

if recap_checkpoint.bootcamp_active():
    recap_checkpoint.fold_checkpoint()
    docker_lifecycle.stop_started_containers()

sys.exit(0)
