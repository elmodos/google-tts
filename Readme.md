Google-TTS
====================

A python script for using Google's undocumented TTS API to listen long strings in selected language

Usage
=====

```
usage: google_say.py [-h] [-l [LANGUAGE]] [-p [SPEED]]
                     (-f FILE | -s STRING [STRING ...])

optional arguments:
  -h, --help            show this help message and exit
  -l [LANGUAGE], --language [LANGUAGE]
                        Language to speak text in.
  -p [SPEED], --speed [SPEED]
                        Speech speed, i.e. 0.24 or 1.0
  -f FILE, --file FILE  File to read text from.
  -s STRING [STRING ...], --string STRING [STRING ...]
                        A string of text to be read.
```


Examples
---

To start speaking text from a file:

```
google_say.py -l uk_UA -p 1.5 -f text.txt 
```

To say a phrase from command line parameter:
```
google_say.py -l uk_UA -p 1.5 -s Доброго дня
```
