#!/bin/bash

sensors | grep "Core $1" | awk '{ printf($3"\n");}'
