#!/bin/bash

ssh $1 "sensors | grep -i 'Core 0' | awk '{print \$3}'"