#!/bin/bash

ssh $1 "who |grep -v '(unknown)' | wc -l"
