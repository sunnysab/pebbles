#! /usr/bin/env python
# This file requires ollama to be installed. You can install it with:
# pip install ollama

import ollama
from pprint import pprint

client = ollama.Client(host='http://192.168.130.200:11434')

response = ollama.generate(model='azure99/blossom-v5', prompt='你好啊', stream=True)
for chunk in response:
    pprint(chunk)