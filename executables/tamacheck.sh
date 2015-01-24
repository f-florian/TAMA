#!/bin/bash

ssh $1 "who |grep -v '(unknown)' | wc -l && sensors | grep -i 'Core 0' | awk '{print \$3}'"
