#!/bin/bash
cd `dirname -- "${BASH_SOURCE[0]}"`
uvicorn server:app --reload
