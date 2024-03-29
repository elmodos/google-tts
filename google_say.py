#!/usr/bin/env python3

import sys
import argparse
import os
import urllib.parse
import urllib.request
import subprocess
import threading
import tempfile


# string to be used as split points for long strings that don't fit in 100 symbols
delimiters = ["\n\n",
              "\n",
              ". ",
              ", ",
              " ",
              ".",
              ","
              ]

temp_dir = tempfile.mkdtemp(prefix="google_say_temp")
player_lock = threading.RLock()
player_process = None
should_stop_playing = False


class DownloadThread(threading.Thread):
    def __init__(self, text, language, total=0, index=0):
        super(DownloadThread, self).__init__()
        self.text = text
        self.language = language
        self.total = total
        self.index = index
        self.file_name = os.path.join(temp_dir, 'speech%i.mp3' % index)

    def run(self):
        # format direct link
        google_tts_url_base = 'http://translate.google.com/translate_tts'
        params = {'ie': 'UTF-8',
                  'client': 'tw-ob',
                  'total': self.total,
                  'idx': self.index,
                  'tl': self.language,
                  'textlen': len(self.text),
                  'q': self.text.encode('utf-8')
                  }
        url_query = urllib.parse.urlencode(params)
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
        req = urllib.request.Request(url=url, headers=headers)
        sys.stdout.write('Requesting mp3 for text:\n"%s"\n' % self.text)
        sys.stdout.flush()
        if len(self.text) > 0:
            try:
                # run request
                response = urllib.request.urlopen(req)

                # write mp3 data
                with open(self.file_name, 'wb') as output:
                    output.write(response.read())
                    output.close()
            except urllib.URLError as e:
                print ('Error: "%s"' % e)


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

    # filter out empty lines
    text_chunks = [line for line in text_chunks if len(line) > 0]
    return text_chunks


def play_audio_file(file_name, speed):
    global player_lock
    global player_process

    # run player and store process id
    player_lock.acquire()
    player_process = subprocess.Popen(args=["mplayer", "-af", "scaletempo", "-speed", speed, file_name])
    player_lock.release()

    # lock thread until player process exits
    player_process.wait()


def start_speaking(text, language, speed):
    global should_stop_playing

    # get short strings list
    text_lines = split_text(text)

    # iterations
    total = len(text_lines)
    index = 0
    file_name_to_play = None

    while True:
        # check if killed from outside, kind of thread safe, read only
        if should_stop_playing:
            break

        # start downloading next mp3 file
        if index < total:
            # current string to download
            string = text_lines[index]
            thread = DownloadThread(string, language, total, index)
            thread.start()
        else:
            thread = None

        # play current mp3 file if any
        if file_name_to_play is not None:
            play_audio_file(file_name_to_play, speed)
            try:
                os.remove(file_name_to_play)
            except:
                pass

        # iterate
        index += 1

        # wait until download thread is done
        if thread is not None:
            thread.join()
            file_name_to_play = thread.file_name
        else:
            file_name_to_play = None
            break

    # delete temp dir
    try:
        os.removedirs(temp_dir)
    except:
        pass


def stop_speaking():
    global player_process
    global player_lock
    global should_stop_playing

    # force kill player
    player_lock.acquire()
    should_stop_playing = True
    if player_process is not None:
        print("Killing player process...")
        try:
            player_process.terminate()
        except:
            print("Cannot kill player process, it might already return")
    player_lock.release()


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
