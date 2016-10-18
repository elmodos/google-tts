#!/usr/bin/env python

import sys
import argparse
import os
import urllib
import urllib2
import subprocess

# string to be used as split points for long strings that don't fit in 100 symbols
delimiters = ["\n\n",
              "\n",
              ". ",
              ", ",
              " ",
              ".",
              ","
              ]


def split_text(text, max_length=100):
    index_start = 0
    text_len = len(text)
    text_chunks = []

    while True:
        index_end = text_len

        if index_end - index_start > max_length:
            index_end = index_start + max_length
        else:
            # chunk ends at end of original string
            substring = text[index_start:index_end]
            text_chunks.append(substring)
            break

        index_start_next = index_end

        # look for delimiters by their priority
        for index, delimiter in enumerate(delimiters):
            idx = text.rfind(delimiter, index_start, index_end)
            if idx > 0:
                index_end = idx
                index_start_next = index_end + len(delimiter)
                break
        substring = text[index_start:index_end]
        text_chunks.append(substring)
        index_start = index_start_next

    return text_chunks


def play_audio_file(file_name, speed="1.0"):
    subprocess.call(["mplayer", "-af", "scaletempo", "-speed", speed, file_name])


def start_speaking(text, language, speed=1.0):
    # Enforcing unicode
    if not isinstance(text, unicode):
        text = unicode(text, "utf-8")
        
    # Google TTS accepts text strings under 100 characters long, so splitting smart way
    text_lines = split_text(text)
    file_name = './speech.mp3'

    for idx, val in enumerate(text_lines):
        # format direct link
        google_tts_url_base = 'http://translate.google.com/translate_tts'
        params = {'ie': 'UTF-8',
                  'client': 'tw-ob',
                  'total': len(text_lines),
                  'idx': idx,
                  'tl': language,
                  'textlen': len(val),
                  'q': val.encode('utf-8')
                  }
        url_query = urllib.urlencode(params)
        url = "%s?%s" % (google_tts_url_base, url_query)

        # http headers sniffed from Chrome
        headers = {"Host": "translate.google.com",
                   "Cache-Control": "max-age=0",
                   "Connection": "close",
                   "Upgrade-Insecure-Requests": "1",
                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                   "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                                 "AppleWebKit/537.36 (KHTML, like Gecko) "
                                 "Chrome/53.0.2785.143 Safari/537.36"
                   }
        req = urllib2.Request(url=url, headers=headers)
        sys.stdout.write('Requesting mp3 for text:\n"%s"\n' % val)
        sys.stdout.flush()
        if len(val) > 0:
            try:
                response = urllib2.urlopen(req)

                # write mp3 data
                with open(file_name, 'wb') as output:
                    output.write(response.read())
                    output.close()

                # play mp3 file
                play_audio_file(file_name=file_name, speed=speed)

                # delete file
                os.remove(file_name)
            except urllib2.URLError as e:
                print ('Error: "%s"' % e)


def parse_arguments():
    parser = argparse.ArgumentParser()

    # language i.e. uk_UA or en
    parser.add_argument('-l', '--language', action='store', nargs='?', help='Language to speak text in.', default='en')

    # speech speed, float 0.25, 1.0, 2.0
    parser.add_argument('-p', '--speed', action='store', nargs='?', help='Speech speed, i.e. 0.24 or 1.0', default='1.0')

    # provide a file to speak from or a string
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', type=argparse.FileType('r'), help='File to read text from.')
    group.add_argument('-s', '--string', action='store', nargs='+', help='A string of text to be read.')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    input_text = ''
    if args.file:
        input_text = args.file.read()
    if args.string:
        input_text = ' '.join(map(str, args.string))

    start_speaking(input_text, args.language, args.speed)