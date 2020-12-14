#!/bin/bash

# Finds and removes all .db files in the directory in which this script is run

find . -type f -name "*.db" -delete
