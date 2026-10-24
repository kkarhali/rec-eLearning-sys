#!/usr/bin/env python3
"""Update every table of contents / index field inside a .docx using LibreOffice (UNO).

pandoc writes the TOC as an empty Word field that Word refreshes on open, but
LibreOffice, Google Docs and PDF exports show it empty. This script opens the
document in a headless LibreOffice, refreshes all indexes so real page numbers
are written into the file, and saves it back as .docx.

Usage: python3 scripts/lo_update_toc.py file.docx [more.docx ...]
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import uno  # system python3 has the LibreOffice UNO bridge
from com.sun.star.beans import PropertyValue


def _prop(name, value):
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def update(files: list[Path]) -> None:
    port = _free_port()
    profile = tempfile.mkdtemp(prefix="lo-profile-")
    proc = subprocess.Popen(
        ["soffice", "--headless", "--invisible", "--nologo", "--norestore",
         f"-env:UserInstallation=file://{profile}",
         f"--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
        ctx = None
        for _ in range(60):
            try:
                ctx = resolver.resolve(f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext")
                break
            except Exception:
                time.sleep(1)
        if ctx is None:
            sys.exit("could not connect to LibreOffice")
        desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
        for f in files:
            url = uno.systemPathToFileUrl(str(f.resolve()))
            doc = desktop.loadComponentFromURL(url, "_blank", 0, (_prop("Hidden", True),))
            try:
                indexes = doc.getDocumentIndexes()
                for i in range(indexes.getCount()):
                    indexes.getByIndex(i).update()
                # also refresh plain fields (PAGE etc.)
                doc.getTextFields().refresh()
                doc.storeToURL(url, (_prop("FilterName", "MS Word 2007 XML"), _prop("Overwrite", True)))
                print(f"updated {indexes.getCount()} index(es) in {f}")
            finally:
                doc.close(True)
    finally:
        try:
            desktop.terminate()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    update([Path(a) for a in sys.argv[1:]])
