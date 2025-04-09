#!/usr/bin/env python
# -*- coding: utf-8 -*-
# MarkMelGen.py
# free and open-source software, Paul Wardley Davies, see MarkMelGen/license.txt

# Using Markov Chains to Generate New Music
# See https://groups.google.com/g/music21list/c/WndF4uvp6_8/m/EkVLeLtlBQAJ
#
# To create Markov chain melodies:
# Choose a corpus of melodies.
# Iterate through the notes each melody, keeping track of the frequency that n notes moves to note x
# with a dictionary. So, the end result for a trigram should be something like
# Markov_dict = {('B', 'C'): {'A': .01, 'F': .02, 'B': .0 }, ('B', 'D'): {'A': .02, 'B': .01}, and so on...}.
# This gives you the transition probabilities.
# To compose, choose starting notes, then append further notes given the transitional probabilities.

import argparse
import ast
import configparser
import contextlib
import copy
import datetime
import json
import logging
import subprocess
import MarkMelGen_utilities
import markmelgen_style
import math
import music21
import pickle
import pyparsing
import os
import random
import re
import sys
import warnings  # Import the warnings module

from enum import Enum, auto
from fractions import Fraction

from logging_config import logger

from MarkMelGen_utilities import *
from markmelgen_style import *
from music21 import *
from music21 import environment
from music21.musicxml.archiveTools import compressXML
from music21.stream.makeNotation import consolidateCompletedTuplets
from music21.stream.makeNotation import splitElementsToCompleteTuplets
from music21.musicxml.xmlObjects import MusicXMLWarning
from numpy.random import choice
from showscore import show

# Define log_filename as a global variable
log_filename = None

logger = logging.getLogger("MMG")


def setup_logger(loglevel):
    global log_filename  # Declare log_filename as global to modify it
   
    iso_datetime_str = get_iso_datetime_str()
    log_path = "log" + os.sep
    log_filename = f"{log_path}MarkMelGen_log_{iso_datetime_str}.log"

    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    if loglevel != "INFO":
        console_handler.setLevel(level=getattr(logging, loglevel))
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    if loglevel != "INFO":
        file_handler.setLevel(level=getattr(logging, loglevel))
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.info(f"Logging to {log_filename}")


# Example log messages
# logger.debug("Debug test message")
# logger.info("Info test message")
# logger.warning("Warning test message")
# logger.error("Error test message")
# logger.critical("Critical test message")

# Log levels (from lowest to highest):
# DEBUG: Detailed information for diagnosing problems.
# INFO: General information about application operation.
# WARNING: An indication of something unexpected or concerning.
# ERROR: A serious problem that prevents part of the program from functioning.
# CRITICAL: A severe problem that may cause the program to terminate.

# You can set a threshold level on loggers and handlers,
# meaning they will only process messages of that severity or higher.


# Suppress the specific MusicXMLWarning
warnings.filterwarnings("ignore", category=music21.musicxml.xmlObjects.MusicXMLWarning)

_section_name_matches = [
    "intro",
    "verse",
    "prechorus",
    "chorus",
    "solo",
    "bridge",
    "outro",
]


class Section(Enum):
    INTRO = 0
    VERSE = 1
    PRECHORUS = 2
    CHORUS = 3
    SOLO = 4
    BRIDGE = 5
    OUTRO = 6


class Config_Song_Section(Enum):
    song_intro = 0
    song_verse = 1
    song_prechorus = 2
    song_chorus = 3
    song_solo = 4
    song_bridge = 5
    song_outro = 6


BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED = 0
BEAT_PLACEMENTS_DENIED_SET = []
BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET = []

CADENCE_ALTERNATE_PHRASE_END = False
# CADENCE_ALTERNATE_PHRASE_END = True

CADENCE_DUR_MIN = 1.0

# CADENCE_SECTION_END = False
CADENCE_SECTION_END = True

CADENCE_TONE_FREQUENCY = ""
CADENCE_TONE_PROBABILITY = ""
CADENCE_TONE_SAMPLES = ""

CALL_COUNT_MAX = 100

CONF_FILENAME = ""

DURATION_EQ = ""

DURATION_SET = []

DUR_RATIONAL = False

DUR_TUPLET = False

DUR_LEAST = 0
# DUR_LEAST = 0.25
# DUR_LEAST = Fraction(1, 12)

DUR_LONGEST = 0
# DUR_LONGEST = 0.25
# DUR_LONGEST = Fraction(1, 6)

DUR_PREV_DIFF = 0  # where 0, do not compare with previous duration, 2 is duration is >= 1/2 previous and <= 2 x previous etc
# DUR_PREV_DIFF = 0.5 # not valid so ignored
# DUR_PREV_DIFF = 1   # not valid so ignored
# DUR_PREV_DIFF = 1.1
# DUR_PREV_DIFF = 2

DURATION_MIN_MUSIC21 = 0.0005  # actually 1/2048th

here = os.path.dirname(os.path.abspath(__file__)) + "/"

INPUT_LYRICS_PATH = here
INPUT_MUSIC_PATH = here
INPUT_LYRICS_FILENAME = ""

INPUT_LYRICS_FULLY_QUALIFIED = ""

INPUT_MUSIC_FILENAME = ""

INPUT_MUSIC_FULLY_QUALIFIED = ""

INPUT_STYLE_PATH = here + "input" + os.sep + "style" + os.sep  # added INPUT_STYLE_PATH

INSTRUMENT = "Piano"

MAX_PHRASE_REST = 8.0

OUTPUT_PATH = here

DISPLAY_GRAPHS = True
DISPLAY_HTML = True
DISPLAY_MXL = True
DISPLAY_KAR = True

# lists of key values that control the durations and pitches for each section (Intro ... Outro)
# The final value is the default value for all sections.
PER_SECTION_LIST_LENGTH = 8

PER_SECTION_DURATION_SET = [None] * PER_SECTION_LIST_LENGTH
PER_SECTION_DUR_LEAST = [None] * PER_SECTION_LIST_LENGTH
PER_SECTION_DUR_LONGEST = [None] * PER_SECTION_LIST_LENGTH
PER_SECTION_DUR_PREV_DIFF = [None] * PER_SECTION_LIST_LENGTH
PER_SECTION_DUR_RATIONAL = [None] * PER_SECTION_LIST_LENGTH
PER_SECTION_DUR_TUPLET = [None] * PER_SECTION_LIST_LENGTH
PER_SECTION_REST_NOTE_LINE_OFFSET = [None] * PER_SECTION_LIST_LENGTH
PER_SECTION_TONES_ON_KEY = [None] * PER_SECTION_LIST_LENGTH
PER_SECTION_TONE_PREV_INTERVAL = [None] * PER_SECTION_LIST_LENGTH
PER_SECTION_TONE_RANGE_BOTTOM = [None] * PER_SECTION_LIST_LENGTH
PER_SECTION_TONE_RANGE_TOP = [None] * PER_SECTION_LIST_LENGTH
PER_SECTION_TONE_SCALE_SET = [None] * PER_SECTION_LIST_LENGTH

REST_NOTE_LINE_OFFSET = None

TEMPO_BPM = 0.0

TIME_SIG_WANTED = None
# TIME_SIG_WANTED = '3/4'
# TIME_SIG_WANTED = '4/4'

# Tone filters
TONE_ASCENT = False  # Turn off TONE_ASCENT
TONE_ASCENT_COUNT = 0  # not a configuration paramenter, just a global variable
# TONE_ASCENT_MIN_INTERVAL = 1 # gives infinite loop on valid_note
TONE_ASCENT_MIN_INTERVAL = 2  # gives runs down scale
# TONE_ASCENT_MIN_INTERVAL = 3 # gives descent leaps
# TONE_ASCENT_MIN_INTERVAL = 4 # gives descent chord arpeggio

# TONE_ASCENT_TRIGGER = None
TONE_ASCENT_TRIGGER = "C3"
TONE_ASCENT_TRIGGERED = False  # not a configuration paramenter, just a global variable
TONE_ASCENT_TRIGGER_COUNT = 0  # not a configuration paramenter, just a global variable
TONE_ASCENT_TRIGGER_EVERY_N_TIMES = 1

TONE_DESCENT = False  # Turn off TONE_DESCENT
TONE_DESCENT_COUNT = 0  # not a configuration paramenter, just a global variable
# TONE_DESCENT_MAX_INTERVAL = 1 # gives infinite loop on valid_note
TONE_DESCENT_MAX_INTERVAL = 2  # gives runs down scale
# TONE_DESCENT_MAX_INTERVAL = 3 # gives descent leaps
# TONE_DESCENT_MAX_INTERVAL = 4 # gives descent chord arpeggio

# TONE_DESCENT_TRIGGER = None
TONE_DESCENT_TRIGGER = "C5"
TONE_DESCENT_TRIGGERED = False  # not a configuration paramenter, just a global variable
TONE_DESCENT_TRIGGER_COUNT = 0  # not a configuration paramenter, just a global variable
TONE_DESCENT_TRIGGER_EVERY_N_TIMES = 4

TONE_EQ = ""

TONES_ON_KEY = False
# TONES_ON_KEY = True
TONES_OFF_KEY = False
# TONES_OFF_KEY = True

TONE_PREV_INTERVAL = 0  # maximum number of semitones between notes. 0 = Off
# TONE_PREV_INTERVAL = 1    # caused hang together with TONE_SCALE_SET
# TONE_PREV_INTERVAL = 2    # very limited melodic movement
# TONE_PREV_INTERVAL = 3    # very limited melodic movement
# TONE_PREV_INTERVAL = 4    # limited melodic movement
# TONE_PREV_INTERVAL = 5    # slightly limited melodic movement
# TONE_PREV_INTERVAL = 6    # slightly limited melodic movement
# TONE_PREV_INTERVAL = 7    # normal melodic movement
# TONE_PREV_INTERVAL = 8    # slightly jumpy melodic movement
# TONE_PREV_INTERVAL = 9    # slightly jumpy melodic movement
# TONE_PREV_INTERVAL = 10   # jumpy melodic movement
# TONE_PREV_INTERVAL = 11   # jumpy melodic movement
# TONE_PREV_INTERVAL = 12   # jumpy melodic movement

TONE_RANGE_MID = "C4"
TONE_RANGE_BOTTOM = "C3"
TONE_RANGE_TOP = "C5"

TONE_SCALE_ANHEMITONIC = [
    1,
    2,
    4,
    5,
    6,
]  # anhemitonic (without semitones; e.g., c–d–f–g–a–c′), pentatonic scale without semitones,  1 2 4 5 6 (AKA Japanese mode)
TONE_SCALE_HEMITONIC = [
    1,
    3,
    4,
    5,
    7,
]  # hemitonic form (with semitones; e.g., c–e–f–g–b–c′)  pentatonic scale with semitones      1 3 4 5 7

# TONE_SCALE_NEW = [2, 3, 4, 6, 7]  # user defined scale
TONE_SCALE_SET = ["A", "C", "D", "D#", "E", "G"]

TONE_SCALE_ON_ANHEMITONIC = False
TONE_SCALE_ON_HEMITONIC = False


# ------------ FUNCTIONS -------------------------------------------


def add_new_lyrics_to_old_phrase(
    sect, section_name_text, section_line_num, lyric_line, stream_line
):
    """
    function that takes a stream of notes, wipes any old lyrics, adds new lyrics
    and returns the new stream
    """
    # print('add_new_lyrics_to_old_phrase')
    # print('lyric_line', lyric_line)
    # stream_line.show('text')

    new_stream = music21.stream.Stream()
    new_stream.append(stream_line)
    # new_stream.show('text')

    # split and count new lyric syllables
    syllable_line = split_hyphens(lyric_line)
    # print('syllable_line', syllable_line)

    syllable_list = syllable_line.split()  # Split `a_string` by whitespace.
    # print('syllable_list', syllable_list)

    number_of_syllables = len(syllable_list)  ## counts he-llo as one syllable not two
    # print('number_of_syllables', number_of_syllables)

    note_num = 0

    # wipe any old lyrics and add new lyrics
    for n in new_stream.flatten():
        if type(n) == music21.note.Note:
            # print('note', n, n.duration.quarterLength, n.lyric)
            # print('n.lyrics', n.lyrics)
            n.lyric = None
            if (
                note_num < number_of_syllables
            ):  # only set lyric when enough new syllables
                n.lyric = syllable_list[note_num]
            else:
                logger.warning(
                    "Warning:Lyric-First %s line %d has a lyric at note %d but later %s has no lyric there.",
                    sect,
                    section_line_num,
                    (note_num + 1),
                    section_name_text,
                )
                
            note_num = note_num + 1

    # if there are more new lyric syllables than old notes, add them to the next note/rest.

    # if note_num <= number_of_syllables:
    if note_num < number_of_syllables:
        logger.warning(
            "Warning:Lyric-First %s line %d has %d notes, but later %s has %d syllables. %d too many.",
            sect,
            section_line_num,
            note_num,
            section_name_text,
            number_of_syllables,
            (number_of_syllables - note_num),
        )

        if (number_of_syllables - note_num) == 1:
            n.lyric = " " + syllable_list[note_num]
        if (number_of_syllables - note_num) == 2:
            n.lyric = " " + syllable_list[note_num] + " " + syllable_list[note_num + 1]
        if (number_of_syllables - note_num) == 3:
            n.lyric = (
                " "
                + syllable_list[note_num]
                + " "
                + syllable_list[note_num + 1]
                + " "
                + syllable_list[note_num + 2]
            )
        if (number_of_syllables - note_num) == 4:
            n.lyric = (
                " "
                + syllable_list[note_num]
                + " "
                + syllable_list[note_num + 1]
                + " "
                + syllable_list[note_num + 2]
                + " "
                + syllable_list[note_num + 3]
            )
        if (number_of_syllables - note_num) == 5:
            n.lyric = (
                " "
                + syllable_list[note_num]
                + " "
                + syllable_list[note_num + 1]
                + " "
                + syllable_list[note_num + 2]
                + " "
                + syllable_list[note_num + 3]
                + " "
                + syllable_list[note_num + 4]
            )

    return new_stream


def remove_lyrics_from_phrase(stream_line):
    """
    function that takes a stream of notes and rests, wipes any old lyrics
    and returns the new stream
    """

    new_stream = music21.stream.Stream()
    new_stream.append(stream_line)

    # wipe any old lyrics
    for n in new_stream.flatten():
        if type(n) == music21.note.Note or type(n) == music21.note.Rest:
            n.lyric = None

    return new_stream


def get_semitone_interval(tone_prev, tone):
    """
    function that takes two notes (with octave set)
    and returns the semitone interval between them
    """
    if tone_prev == 0 or tone == 0 or type(tone_prev) == music21.note.Rest:
        return 0
    if tone_prev.octave == None:
        print("exit: Error get_semitone_interval tone_prev.octave == None ")
        sys.exit()
    if tone.octave == None:
        print("exit: Error get_semitone_interval tone.octave == None ")
        sys.exit()

    # calculate interval
    aInterval = interval.Interval(tone_prev, tone)
    AIntSemi = abs(aInterval.semitones)

    return AIntSemi


def get_random_octave():
    """
    function that uses
    globals to
    returns a valid random octave
    """
    low_oct = int(TONE_RANGE_BOTTOM.strip()[-1])
    high_oct = int(TONE_RANGE_TOP.strip()[-1])
    the_valid_tone_octave = random.randint(low_oct, high_oct)
    # print('get_random_octave: TONE_RANGE_BOTTOM',TONE_RANGE_BOTTOM,'TONE_RANGE_TOP',TONE_RANGE_TOP, 'low_oct', low_oct,'high_oct', high_oct , 'the_valid_tone_octave', the_valid_tone_octave  )
    the_valid_tone_octave = validated_octave(the_valid_tone_octave)
    # print('get_random_octave: after validated_octave, the_valid_tone_octave', the_valid_tone_octave  )

    return the_valid_tone_octave


def get_valid_tone_octave(tone_prev, tone, desired_octave):
    """
    function that takes a tone octave,
    if not valid then choose a valid tone octave,
    and return the valid tone octave

    if tone in range: des oct
    else:
        if tp 0/None: random oct
        else:
            if tone with tone_prev.octave in range: use tp oct
            else:   if tone with tone_prev.octave+1 in range: use tp oct+1
                    else:   if tone with tone_prev.octave-1 in range: use tp oct-1
                            else: random oct

    N.B. it's generally better to set the name and octave separately
    lowA = pitch.Pitch()
        >>> lowA.name = 'A'
        >>> lowA.octave = -1
        >>> lowA.nameWithOctave
        'A-1'
    """
    # assume good but validate
    # the_input_tone_octave = desired_octave
    desired_octave = validated_octave(desired_octave)

    the_valid_tone_octave = desired_octave
    # a_valid_tone = False
    tone.octave = desired_octave

    # validate tone octave
    if (
        note.Note(TONE_RANGE_BOTTOM)
        <= note.Note(tone.nameWithOctave)
        <= note.Note(TONE_RANGE_TOP)
    ):
        # a_valid_tone = True
        # print('a valid tone octave', tone.nameWithOctave)
        pass
    else:  # tone out of range
        # if tone_prev == 0 or tone_prev.octave == None: # invalid prev_tone
        if tone_prev == 0 or type(tone_prev) == music21.note.Rest:  # invalid prev_tone

            while True:
                the_valid_tone_octave = get_random_octave()
                logger.debug(
                    f"invalid tone_prev 0 or None {tone_prev} new random octave {the_valid_tone_octave}"
                )
                tone.octave = the_valid_tone_octave
                # if note.Note(TONE_RANGE_BOTTOM) <= note.Note(tone.nameWithOctave) <= note.Note(TONE_RANGE_TOP):
                if (
                    note.Note(TONE_RANGE_BOTTOM).octave
                    <= note.Note(tone.nameWithOctave).octave
                    <= note.Note(TONE_RANGE_TOP).octave
                ):
                    break
        else:  # have a prev_tone octave
            tone.octave = tone_prev.octave
            if (
                note.Note(TONE_RANGE_BOTTOM)
                <= note.Note(tone.nameWithOctave)
                <= note.Note(TONE_RANGE_TOP)
            ):
                the_valid_tone_octave = tone.octave
                # print('tone with tone_prev.octave in range: use tp oct, the_valid_tone_octave', the_valid_tone_octave)
            else:
                tone.octave = tone_prev.octave + 1
                if (
                    note.Note(TONE_RANGE_BOTTOM)
                    <= note.Note(tone.nameWithOctave)
                    <= note.Note(TONE_RANGE_TOP)
                ):
                    the_valid_tone_octave = tone.octave
                    # print('tone with tone_prev.octave+1 in range: use tp oct, the_valid_tone_octave', the_valid_tone_octave)
                else:
                    tone.octave = tone_prev.octave - 1
                    if (
                        note.Note(TONE_RANGE_BOTTOM)
                        <= note.Note(tone.nameWithOctave)
                        <= note.Note(TONE_RANGE_TOP)
                    ):
                        the_valid_tone_octave = tone.octave
                        # print('tone with tone_prev.octave-1 in range: use tp oct, the_valid_tone_octave',
                        #      the_valid_tone_octave)
                    else:
                        the_valid_tone_octave = get_random_octave()
                        # print('invalid tone_prev octave', note.Note(tone_prev.nameWithOctave), ' new random octave', the_valid_tone_octave)

    the_valid_tone_octave = validated_octave(the_valid_tone_octave)

    # print('get_valid_tone_octave(tone_prev ', tone_prev,' tone ', tone.nameWithOctave ,' desired_octave ', desired_octave, ' returns ', the_valid_tone_octave )
    return the_valid_tone_octave


def get_tone_octave(tone_prev, tone, note_num):
    """
    function that takes the previous note and a note,
    and the number of the note in the stream starting at 0
    and returns the octave of the note
    """
    if note_num == 0:
        the_tone_octave = get_random_octave()
    else:
        if tone_prev == 0 or type(tone_prev) == music21.note.Rest:
            mid_oct = get_random_octave()
        else:
            mid_oct = tone_prev.octave
        low_oct = mid_oct - 1
        high_oct = mid_oct + 1

        tone.octave = mid_oct
        mid_semis = get_semitone_interval(tone_prev, tone)
        tone.octave = low_oct
        low_semis = get_semitone_interval(tone_prev, tone)
        tone.octave = high_oct
        high_semis = get_semitone_interval(tone_prev, tone)

        if low_semis <= mid_semis and mid_semis <= high_semis:
            smallest_interval_octave = low_oct
            largest_interval_octave = mid_oct
        if low_semis <= high_semis and high_semis <= mid_semis:
            smallest_interval_octave = low_oct
            largest_interval_octave = high_oct
        if mid_semis <= low_semis and low_semis <= high_semis:
            smallest_interval_octave = mid_oct
            largest_interval_octave = low_oct
        if mid_semis <= high_semis and high_semis <= low_semis:
            smallest_interval_octave = mid_oct
            largest_interval_octave = high_oct
        if high_semis <= low_semis and low_semis <= mid_semis:
            smallest_interval_octave = high_oct
            largest_interval_octave = low_oct
        if high_semis <= mid_semis and mid_semis <= low_semis:
            smallest_interval_octave = high_oct
            largest_interval_octave = mid_oct

        if TONE_INTERVAL == "smallest":
            # if new note = prev then use same octave as prev
            if tone_prev == tone:
                the_tone_octave = tone_prev.octave
            else:
                the_tone_octave = smallest_interval_octave

        if TONE_INTERVAL == "largest":
            # if new note = prev then use same octave as prev
            if tone_prev == tone:
                the_tone_octave = tone_prev.octave + 1
            else:
                the_tone_octave = largest_interval_octave

        if TONE_INTERVAL == "random":
            flip = random.randint(0, 1)
            if flip == 0:
                the_tone_octave = smallest_interval_octave
            else:
                the_tone_octave = largest_interval_octave

    the_tone_octave = get_valid_tone_octave(tone_prev, tone, the_tone_octave)

    # print('get_tone_octave(tone_prev', tone_prev,' tone ', tone.nameWithOctave, 'note_num in stream', note_num, ' returns ', the_tone_octave)

    return the_tone_octave


###
def get_dur_to_next_measure_in_stream(stream_offset, beat_count):
    """
    function that takes a stream_offset and beats to the bar count and
    returns the duration to the next measure in the stream
    """
    # prev_measure_offset = int('%.0f' % (stream_offset / beat_count)) # does not truncate, it rounds and truncates
    prev_measure_offset = math.trunc(stream_offset / beat_count)
    next_measure_offset = beat_count * (prev_measure_offset + 1)
    dur_to_next_measure = next_measure_offset - stream_offset

    return dur_to_next_measure


def truncate(f, n):
    """
    function that takes a float f and the number of decimal places n
    and truncates without rounding and
    returns the truncated float
    e.g.
    >>> truncate(3.9, 0)
    3.0
    >>> truncate(4.0, 0)
    4.0
    >>> truncate(4.1, 0)
    4.0
    >>> truncate(4.11, 1)
    4.1
    >>> truncate(4.19, 1)
    4.1
    """
    return math.floor(f * 10**n) / 10**n


# def get_next_measure_end(the_offset, beat_count):
#     """
#     function that takes an offset and the number of beats in the bar and
#     returns the offset of the next measure
#     e.g.    beat_count = 4
#     offset  0   3.9 4.0 7.9 8.0
#     return  4   4   8   8   12
#     """
#     # if the_offset == 0:
#     #     offset_end_bar = beat_count
#     # else:
#         # does not wotk for 4.0 , 4 returns 4, expect 8
#         # bar_last_note_end = int(math.ceil(the_offset / beat_count))
#         # # e.g.    3 = int(math.ceil(8.416666666666668 / 4))
#         # offset_end_bar = bar_last_note_end * beat_count
#         # # e.g.  e.g. 12 = 3 * 4
#     bar_of_offset = (int(truncate(the_offset,0) / beat_count)) + 1
#     next_measure_end_offset = bar_of_offset * beat_count
#
#     return next_measure_end_offset


def countKeySignatureByType(slist):
    # Rachel Stroud https://core.ac.uk/download/pdf/386736181.pdf
    # Function which counts all the key signatures in slist
    # Function counts key signatures by type and movement
    # Note that this function counts by the number of shaps and flats not the major/minor key

    # Uses the first part ([0] in Python) to do this - all parts shouldhave same time signature!
    p = 0  # part p = 0

    # Possible key signatures range from -7 (7 flats: flat = -1) to +7 (7 sharps: sharp = +1)
    # This scoring system of sharps = +1, flats = -1 is the same in the music21 key signature
    # property .sharps
    # Create list of possible key values ("keylist")
    keylist = [-7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7]

    # Initialise an empty count list structure: m movement lists of i key signature types
    count = [[0] * len(keylist) for m in range(len(slist))]

    # Loop through each movement in slist (m)
    for m in range(0, len(slist)):
        # Loop through key signatures in movement m, part p using music getElementsByClass recurse() function(el)
        for el in slist[m].parts[p].recurse().getElementsByClass("KeySignature"):
            # Loop through the known key signatures keylist (i) to search for a match for key signature el
            for i in range(0, len(keylist)):
                # If the el-th key signature matches the ith key signature value in key list,
                # then we have found the position (i) of this key signature el in the keylist;
                # add 1 to the relevant position in the count list structure
                # (m-th movement, i-th type of key signature)
                if el.sharps == keylist[i]:
                    count[m][i] = count[m][i] + 1

        # Print results so easy to copy into e.g. Excel
        # print('countKeySignatureByType results: key signatures in each movement separated by type')
        # print('--> Key signature type')
        # print('v Movement in slist')
        # print('Key signature sharp (+1) and flats (-1):')
        # print(keylist)
        # print2DList(count)  # See print functions below

    return [keylist, count]


def print2DList(list2D):
    # Function which prints out a list within a list as a table
    # Loop through the outer list (i)
    for i in range(0, len(list2D)):
        # Create empty message string "msg"
        msg = str()
        # Loop through the list (j) at position i in the outer list
        # Append the information at each position to the message msg (with a space inbetween each list item)
        for j in range(0, len(list2D[i])):
            msg = msg + str(list2D[i][j]) + " "
        # Print the message at the end of the inner loop
    print(msg)


def get_keys(transition):
    """
    given a transition
    return the keys
    """
    keys = [" ".join(map(str, i)) for i in list(transition.keys())]
    return keys


def get_random_key(keys):
    """
    given keys e.g. keys: ['C D', 'D E', 'E F', 'F G', 'G A', 'A B']
    return a random key e.g. key: ('F', 'G')
    """
    draw = choice(keys)
    key = tuple(draw.split())
    logger.debug(f"get_random_key: keys {keys}, \t return \t {key}")
    return key


# def get_cadence_note(key, cad_transition, dkey, cad_dtransition, lyric_syllable):
#     """
#     function that given the keys for the previous 2 notes and the cadence note and duration transitons and lyric
#     returns the cadence note
#     """
#
#     print('get_cadence_note(key, dkey, lyric_syllable', key, dkey, lyric_syllable)
#
#     # if there is a cadence note key transition for the previous 2 notes use that
#     # if tone_prev_2 != None and tone_prev != None and ((tone_prev_2.name, tone_prev.name) in cad_transition):
#     if tone_prev_2 != 0 and tone_prev != 0 and ((tone_prev_2.name, tone_prev.name) in cad_transition):
#         cad_key = (tone_prev_2.name, tone_prev.name)
#     # else get a random key cadence
#     else:
#         cad_keys = [' '.join(map(str, i)) for i in list(cad_transition.keys())]
#         cad_key = get_random_key(cad_keys)
#
#     # draw and create the note
#     # cad_draw = choice(list(cad_transition[cad_key].keys()), 1, list(cad_transition[cad_key].values()))
#     # n = music21.note.Note(cad_draw[0])
#     cad_draw = get_random_draw(cad_key, cad_transition)
#     n = music21.note.Note(cad_draw)
#
#     # determine the octave for the cadence note
#     octave = get_tone_octave(tone_prev, n, 1)
#     n.octave = octave
#
#     # if there is a cadence duration key transition for the previous 2 notes use that
#     # if tone_prev_2 != None and tone_prev != None and ((tone_prev_2.duration.quarterLength, tone_prev.duration.quarterLength) in cad_dtransition):
#     # if tone_prev_2 != None and tone_prev != None and ((str(tone_prev_2.duration.quarterLength), str(tone_prev.duration.quarterLength)) in cad_dtransition):
#     if tone_prev_2 != 0 and tone_prev != 0 and (
#                 (str(tone_prev_2.duration.quarterLength), str(tone_prev.duration.quarterLength)) in cad_dtransition):
#
#         # cad_dkey = (tone_prev_2.duration.quarterLength, tone_prev.duration.quarterLength)
#         cad_dkey = (str(tone_prev_2.duration.quarterLength), str(tone_prev.duration.quarterLength))
#
#     # else get a random duration cadence
#     else:
#         cad_dkeys = [' '.join(map(str, i)) for i in list(cad_dtransition.keys())]
#         cad_dkey = get_random_key(cad_dkeys)
#     # draw and set the duration
#     # cad_ddraw = choice(list(cad_dtransition[cad_dkey].keys()), 1, list(cad_dtransition[cad_dkey].values()))
#     # n.duration.quarterLength = cad_ddraw[0]
#     cad_ddraw = get_random_draw(cad_dkey, cad_dtransition)
#     n.duration.quarterLength = validated_duration(cad_ddraw, cad_dtransition, 1.0)
#     # n.duration.quarterLength = cad_ddraw
#
#     # add the lyric
#     if lyric_syllable != None:
#         n.lyric = lyric_syllable
#
#     return n


def validated_octave(the_valid_tone_octave):
    """
    function that given an octave
    returns a validated octave
    """
    if the_valid_tone_octave < 0:
        print(
            "validated_octave: tone_octave < 0 is ",
            the_valid_tone_octave,
            "set the_valid_tone_octave = 0",
        )
        the_valid_tone_octave = 0
    if the_valid_tone_octave > 9:
        print(
            "validated_octave: tone_octave > 9 is ",
            the_valid_tone_octave,
            "set the_valid_tone_octave = 9",
        )
        the_valid_tone_octave = 9
    return the_valid_tone_octave


# def validated_note(tone_prev, tone, tone_scale, tone_mode, key, transition, fallback_tone):
#     """
#     function that given a tone information and a fallback_note
#     returns a validated note
#     """
#     call_count = 0
#     while True:  # start repeat until valid note or > CALL_COUNT_MAX
#         call_count = call_count + 1
#         if valid_tone(tone_prev, tone, tone_scale, tone_mode) or call_count > CALL_COUNT_MAX :
#             break
#         else:
#             # keys = get_keys(transition)
#             # key = get_random_key(keys)
#             tone = get_random_draw(key, transition)
#     if call_count > CALL_COUNT_MAX:
#         tone = fallback_tone
#         print('Warning: in validated_note, call_count > CALL_COUNT_MAX, fallback_tone:', fallback_tone, '\n key:', key)
#     return tone


def keys_filter_condition(key, desired_key_ending):
    """
    given a key and the desired_key_ending
    return the key if it has the desired_key_ending
    """
    # return key.endswith('1.0')
    return key.endswith(desired_key_ending)


def get_one_state_key(key, transition):
    """
    given a key (x,y) and a transition,
    use the second value y in the key only to get a random one state key (*,y)
    return the random one state key
    """
    # print('get_one_state_key: key', key)

    keys = get_keys(transition)
    count = 0
    valid = False

    # filter keys on second key
    desired_key_ending = key[1]
    filtered_keys = [d for d in keys if keys_filter_condition(d, desired_key_ending)]
    # print('filtered keys = ',filtered_keys)

    if filtered_keys == []:
        return key
    else:
        # random filtered key
        filtered_key = get_random_key(filtered_keys)
        # print('random filtered key = ',filtered_key)
        return filtered_key


def get_note_with_octave(tone_prev, tone_name):
    """
    Given a previous note and a tone_name
    create a note, give it an octave based on the previous note
    return the note
    """
    tone = music21.note.Note(tone_name)
    # determine the octave for the note
    octave = get_tone_octave(tone_prev, tone, 1)
    tone.octave = octave
    return tone


# def get_next_beat_placement(n_prev, bpm_key, bpm_transition):
#     """
#     Generates the next beat placement in a sequence based on the given parameters.

#     Args:
#         n_prev (music21.note.Note): The previous note in the sequence.
#         bpm_key (str): The key for the bpm transition.
#         bpm_transition (dict): The bpm transition probabilities.

#     Returns:
#         beat_placement (float) where 0 = on the beat and a value > 0 but less than 1 is the off_beat

#     Raises:
#         KeyError: If the key is not found in the transition dictionary.
#         ValueError: If an invalid parameter is provided.

#     Example:
#         >>> n_prev = music21.note.Note()
#         >>> bpm_key =  ('0', '1/2')
#         >>> bpm_transition = {('0', '0'): {Fraction(0, 1): 0.37209302325581395, Fraction(1, 2): 0.16279069767441862}, ('0', '1/2'): {Fraction(0, 1): 0.23255813953488372}, ('1/2', '0'): {Fraction(0, 1): 0.16279069767441862, Fraction(1, 2): 0.06976744186046512}}
#         >>> beat_placement = get_next_beat_placement( n_prev, bpm_key, bpm_transition)
#         >>> print(beat_placement)
#     """

#     valid = False
#     count = 0

#     # attempt a valid with 2 state key
#     while not valid and count < CALL_COUNT_MAX:
#         count += 1
#         if bpm_key not in bpm_transition:
#             break
#         beat_placement = get_random_draw(bpm_key, bpm_transition)
#         if beat_placement >= 0.0 and beat_placement < 1.0:
#             valid = True
#             logger.debug(
#                 f"get_next_beat_placement: 2 state bpm_key {bpm_key} valid bpm_transition {beat_placement}"
#             )
#     if not valid:
#         # use fallback beat_placement
#         beat_placement = 0.0
#         logger.debug(
#             f"get_next_beat_placement: fallback beat_placement used: {beat_placement}"
#         )

#     return beat_placement

# v2 copilot 
def get_next_beat_placement(n_prev, bpm_key, bpm_transition):
    """
    Generates the next beat placement in a sequence based on the given parameters.

    Args:
        n_prev (music21.note.Note): The previous note in the sequence.
        bpm_key (str): The key for the bpm transition.
        bpm_transition (dict): The bpm transition probabilities.

    Returns:
        beat_placement (float) where 0 = on the beat and a value > 0 but less than 1 is the off_beat

    Raises:
        KeyError: If the key is not found in the transition dictionary.
        ValueError: If an invalid parameter is provided.

    Example:
        >>> n_prev = music21.note.Note()
        >>> bpm_key =  ('0', '1/2')
        >>> bpm_transition = {('0', '0'): {Fraction(0, 1): 0.37209302325581395, Fraction(1, 2): 0.16279069767441862}, ('0', '1/2'): {Fraction(0, 1): 0.23255813953488372}, ('1/2', '0'): {Fraction(0, 1): 0.16279069767441862, Fraction(1, 2): 0.06976744186046512}}
        >>> beat_placement = get_next_beat_placement(n_prev, bpm_key, bpm_transition)
        >>> print(beat_placement)
    """
    global DUR_RATIONAL

    valid = False
    count = 0

    # attempt a valid with 2 state key
    while not valid and count < CALL_COUNT_MAX:
        count += 1
        if bpm_key not in bpm_transition:
            break
        beat_placement = get_random_draw(bpm_key, bpm_transition)

        if DUR_RATIONAL:
            # Allow only beat_placement with denominators 1, 2, 4, 8, 16, 32, etc.
            if beat_placement >= 0.0 and beat_placement < 1.0 and (
                beat_placement.denominator & (beat_placement.denominator - 1) == 0
            ):
                valid = True
                logger.debug(
                    f"get_next_beat_placement: DUR_RATIONAL=True, valid bpm_transition {beat_placement}"
                )
        else:
            if beat_placement >= 0.0 and beat_placement < 1.0:
                valid = True
                logger.debug(
                    f"get_next_beat_placement: DUR_RATIONAL=False, valid bpm_transition {beat_placement}"
                )

    if not valid:
        # use fallback beat_placement
        beat_placement = 0.0
        logger.debug(
            f"get_next_beat_placement: fallback beat_placement used: {beat_placement}"
        )

    return beat_placement

def get_next_note(
    note_num,
    n_prev,
    tone_scale,
    tone_mode,
    key,
    transition,
    bpm_key,
    bpm_transition,
    dkey,
    dtransition,
    lyric_syllable,
    ts,
):
    """
    Generates the next note in a sequence based on the given parameters.

    Args:
        note_num (int): The number of the note in the sequence.
        n_prev (music21.note.Note): The previous note in the sequence.
        tone_scale (list): The scale of tones to use.
        tone_mode (str): The mode of the tone scale.
        key (str): The key for the transition.
        transition (dict): The transition probabilities for notes.
        bpm_key (str): The key for the bpm transition.
        bpm_transition (dict): The bpm transition probabilities.
        dkey (str): The key for the duration transition.
        dtransition (dict): The duration transition probabilities.
        lyric_syllable (str): The syllable of the lyric to assign to the note.
        ts (music21.meter.TimeSignature): The time signature of the piece.

    Returns:
        music21.note.Note: The previous note with the appropriate pitch, duration, and lyric.
        music21.note.Note: The generated note with the appropriate pitch, duration, and lyric.

    Raises:
        KeyError: If the key is not found in the transition dictionary.
        ValueError: If an invalid parameter is provided.

    Example:
        >>> n_prev = music21.note.Note()
        >>> tone_scale = 'C'
        >>> tone_mode = 'major'
        >>> key = ('D', 'E')
        >>> transition = {('C', 'C'): {'D': 0.047619047619047616}, ('C', 'D'): {'B': 0.023809523809523808, 'E': 0.047619047619047616, 'C': 0.023809523809523808}, ('D', 'B'): {'C': 0.023809523809523808}, ('B', 'C'): {'D': 0.023809523809523808, 'C': 0.023809523809523808}, ('D', 'E'): {'E': 0.023809523809523808, 'F': 0.047619047619047616}, ('E', 'E'): {'F': 0.023809523809523808}, ('E', 'F'): {'E': 0.047619047619047616, 'G': 0.047619047619047616, 'F': 0.023809523809523808}, ('F', 'E'): {'D': 0.09523809523809523, 'F': 0.023809523809523808}, ('E', 'D'): {'C': 0.047619047619047616, 'E': 0.023809523809523808}, ('D', 'C'): {'D': 0.023809523809523808, 'B': 0.023809523809523808, 'E': 0.023809523809523808}, ('C', 'B'): {'C': 0.023809523809523808}, ('F', 'G'): {'G': 0.023809523809523808, 'A': 0.023809523809523808}, ('G', 'G'): {'G': 0.047619047619047616, 'F': 0.023809523809523808}, ('G', 'F'): {'E': 0.023809523809523808}, ('F', 'F'): {'F': 0.047619047619047616, 'E': 0.023809523809523808}, ('C', 'E'): {'F': 0.023809523809523808}, ('G', 'A'): {'F': 0.023809523809523808}, ('A', 'F'): {'E': 0.023809523809523808}}
        >>> bpm_key =  ('0', '1/2')
        >>> bpm_transition = {('0', '0'): {Fraction(0, 1): 0.37209302325581395, Fraction(1, 2): 0.16279069767441862}, ('0', '1/2'): {Fraction(0, 1): 0.23255813953488372}, ('1/2', '0'): {Fraction(0, 1): 0.16279069767441862, Fraction(1, 2): 0.06976744186046512}}
        >>> dkey = ('1.5', '0.5')
        >>> dtransition = {('1.0', '1.0'): {1.0: 0.21428571428571427, 1.5: 0.09523809523809523, 0.5: 0.047619047619047616}, ('1.0', '1.5'): {0.5: 0.09523809523809523}, ('1.5', '0.5'): {1.0: 0.11904761904761904}, ('0.5', '1.0'): {1.0: 0.14285714285714285, 0.5: 0.023809523809523808}, ('1.0', '0.5'): {0.5: 0.07142857142857142}, ('0.5', '0.5'): {0.5: 0.09523809523809523, 1.0: 0.047619047619047616, 1.5: 0.023809523809523808}, ('0.5', '1.5'): {0.5: 0.023809523809523808}},
        >>> lyric_syllable = 'la'
        >>> ts = music21.meter.TimeSignature('4/4')
        >>> n_prev, note = get_next_note(n_prev, tone_scale, tone_mode, key, transition, bpm_key, bpm_transition, dkey, dtransition, lyric_syllable, ts)
        >>> print(note)
    """

    logger.debug(
        f"get_next_note(note_num {note_num}, n_prev {n_prev}, tone_scale {tone_scale}, tone_mode {tone_mode}, key {key}, bpm_key {bpm_key}, dkey {dkey}, lyric {lyric_syllable}, ts {ts}"
    )

    # input("Press Enter to continue...")

    valid = False
    count = 0

    # Get Duration
    # TBD

    # Get Offset (using beat placement)
    # TBD

    # add get_next_offset function which takes in to account the beat placement
    note_beat_placement = get_next_beat_placement(n_prev, bpm_key, bpm_transition)

    # # convert beat_placement to offset_placement
    # offset_placement = note_beat_placement * ts.beatDuration.quarterLength
    # logger.debug(f"get_next_note: offset_placement {offset_placement} = note_beat_placement {note_beat_placement} * ts.beatDuration.quarterLength {ts.beatDuration.quarterLength}")

    # note_offset = n_prev.offset + n_prev.duration.quarterLength + offset_placement
    # logger.debug(f"get_next_note: note_offset {note_offset} = n_prev.offset {n_prev.offset} + n_prev.duration.quarterLength {n_prev.duration.quarterLength} + offset_placement  {offset_placement}")

    # work out the default_offset 												e.g. 4.25
    default_offset = n_prev.offset + n_prev.duration.quarterLength
    # calculate default_offset_beat_placement									e.g. 0.25	0.25
    default_offset_beat_placement = fractional_part_as_fraction(default_offset, ts)
    # desired_offset_placement 													e.g. 0.5 	0.125
    desired_offset_placement = note_beat_placement * ts.beatDuration.quarterLength

    # calculate note_offset 													e.g. 4.5	5.125
    if default_offset_beat_placement == desired_offset_placement:
        note_offset = default_offset
        logger.debug(
            f"get_next_note: default_offset_beat_placement == desired_offset_placement: note_offset = default_offset:  = {note_offset} "
        )
    if default_offset_beat_placement < desired_offset_placement:
        note_offset = default_offset + (
            desired_offset_placement - default_offset_beat_placement
        )
        logger.debug(
            f"default_offset_beat_placement < desired_offset_placement: note_offset {note_offset} = default_offset {default_offset} + (desired_offset_placement {desired_offset_placement} - default_offset_beat_placement {default_offset_beat_placement}"
        )
    if default_offset_beat_placement > desired_offset_placement:
        note_offset = math.ceil(default_offset) + desired_offset_placement
        logger.debug(
            f"get_next_note: default_offset_beat_placement > desired_offset_placement: note_offset {note_offset} = math.ceil(default_offset) {math.ceil(default_offset)} + desired_offset_placement {desired_offset_placement}"
        )
    if note_num == 0:
        note_offset = default_offset

    # amend n_prev duration to include the offset
    original_n_prev = copy.deepcopy(n_prev)
    logger.debug(
        f"get_next_note: n_prev.duration.quarterLength {n_prev.duration.quarterLength} + ( note_offset {note_offset} - default_offset {default_offset} )"
    )
    n_prev.duration.quarterLength = n_prev.duration.quarterLength + (
        note_offset - default_offset
    )
    logger.debug(
        f"get_next_note: new n_prev.duration.quarterLength {n_prev.duration.quarterLength}"
    )

    dur_on_beat = is_offset_on_beat(note_offset, ts)
    logger.debug(
        f"get_next_note: note_offset {note_offset}, lyric_syllable {lyric_syllable} dur_on_beat {dur_on_beat}"
    )

    # Get Pitch

    # attempt a valid n with 2 state key
    while not valid and count < CALL_COUNT_MAX:
        count += 1
        if key not in transition:
            break
        tone_name = get_random_draw(key, transition)
        n = get_note_with_octave(n_prev, tone_name)
        if valid_pitch(n_prev, n, tone_scale, tone_mode):
            valid = True
            # print('2 state key valid_pitch(n_prev, n, ...) == True. n_prev=', n_prev, 'n=', n,)

    # attempt a valid tone with 1 state key
    count = 0
    while not valid and count < CALL_COUNT_MAX:
        count += 1
        new_key = get_one_state_key(key, transition)
        if new_key not in transition:
            break
        tone_name = get_random_draw(new_key, transition)
        n = get_note_with_octave(n_prev, tone_name)
        if valid_pitch(n_prev, n, tone_scale, tone_mode):
            valid = True
            # print(
            #     "1 state key valid_pitch(n_prev, n, ...) == True. n_prev=",
            #     n_prev,
            #     "n=",
            #     n,
            # )

    # attempt a valid tone with random key
    count = 0
    while not valid and count < CALL_COUNT_MAX:
        count += 1
        keys = get_keys(transition)
        new_key = get_random_key(keys)
        if new_key not in transition:
            continue
        tone_name = get_random_draw(new_key, transition)
        n = get_note_with_octave(n_prev, tone_name)
        if valid_pitch(n_prev, n, tone_scale, tone_mode):
            valid = True
            print(
                "random key valid_pitch(n_prev, n, ...) == True. n_prev=",
                n_prev,
                "n=",
                n,
            )

    if not valid:
        # use fallback tone
        tone_name = "C"
        n = get_note_with_octave(n_prev, tone_name)
        logger.debug(f"Warning: in get_next_note: fallback tone used:{tone_name}")

    # get valid duration
    valid = False
    count = 0

    # attempt a valid duration with 2 state key
    while not valid and count < CALL_COUNT_MAX:
        count += 1
        if dkey not in dtransition:
            break
        dur = get_random_draw(dkey, dtransition)

        if valid_duration(dkey[1], dur, dur_on_beat):
            valid = True
            logger.debug(
                f"2 state key valid_duration(dkey[1], dur) = True, dkey[1]=, {dkey[1]}, dur= {dur}"
            )

    # attempt a valid duration with 1 state key
    count = 0
    while not valid and count < CALL_COUNT_MAX:
        count += 1
        new_dkey = get_one_state_key(dkey, dtransition)
        if new_dkey not in dtransition:
            break
        dur = get_random_draw(new_dkey, dtransition)
        if valid_duration(dkey[1], dur, dur_on_beat):
            valid = True
            # print('1 state key valid_duration(dkey[1], dur) = True','dkey[1]=', dkey[1], 'dur=', dur)

    # attempt a valid duration with random key
    count = 0
    while not valid and count < CALL_COUNT_MAX:
        count += 1
        dkeys = get_keys(dtransition)
        new_dkey = get_random_key(dkeys)
        if new_dkey not in dtransition:
            continue
        dur = get_random_draw(new_dkey, dtransition)
        # print('Attempting random key valid_duration(dkey[1], dur) = True', 'dkey[1]=', dkey[1], 'dur=', dur)
        if valid_duration(dkey[1], dur, dur_on_beat):
            valid = True
            print(
                "random key valid_duration(dkey[1], dur) = True",
                "dkey[1]=",
                dkey[1],
                "dur=",
                dur,
            )

    # attempt a valid duration with DURATION_SET
    if DURATION_SET:
        count = 0
        while not valid and count < CALL_COUNT_MAX:
            count += 1
            # get a random value from list
            dur = random.choice(DURATION_SET)
            if valid_duration(0, dur, dur_on_beat):
                valid = True
                logger.debug(
                    f"get_next_note: fallback dur {dur}, used from DURATION_SET {DURATION_SET}"
                )

    if not valid:
        # use fallback quarterLength duration
        dur = 1.0
        logger.debug(f"get_next_note: fallback quarterLength duration used: {dur}")

    # add offset to note
    n.offset = note_offset

    # add duration to note
    n.duration.quarterLength = dur

    # Get Lyric_Syllable

    # add the lyric
    if lyric_syllable != None:
        n.lyric = lyric_syllable

    if n_prev.duration.quarterLength != original_n_prev.duration.quarterLength:
        logger.debug(
            f"get_next_note: n_prev.duration.quarterLength changed from {original_n_prev.duration.quarterLength} to {n_prev.duration.quarterLength}"
        )
        logger.debug(f"get_next_note: original_n_prev:")
        show_text_of_note(original_n_prev, ts)
        logger.debug(f"get_next_note: changed n_prev:")
        show_text_of_note(n_prev, ts)
        logger.debug(f"get_next_note: next n :")
        show_text_of_note(n, ts)

    logger.debug(f"get_next_note:return \t n_prev = {n_prev} n = {n}")
    return n_prev, n


def get_random_draw(key, transition):
    """
    given a key and a transition
    return a random draw
    """
    draw = random.choices(
        list(transition[key].keys()), weights=transition[key].values(), k=1
    )[0]
    logger.debug(f"get_random_draw: key {key}, \t\t return {draw}")
    return draw


def validated_duration(quarterLength, transition, fallback_quarterLength):
    """
    given a quarterLength and a duration transition and keys
    return a validated rest_note_duration
    """
    call_count = 0
    while True:  # start repeat until valid duration or > CALL_COUNT_MAX
        call_count = call_count + 1
        if valid_duration(0, quarterLength) or call_count > CALL_COUNT_MAX:
            break
        else:
            keys = get_keys(transition)
            key = get_random_key(keys)
            quarterLength = get_random_draw(key, transition)
    if call_count > CALL_COUNT_MAX:
        quarterLength = fallback_quarterLength
        print(
            "Warning: in validated_duration, call_count > CALL_COUNT_MAX, fallback_quarterLength used. quarterLength:",
            quarterLength,
            "\n transition:",
            transition,
            "\n fallback_quarterLength:",
            fallback_quarterLength,
        )
    return quarterLength


def get_nameWithOctave_from_cadence_tones(n_prev):
    """
    given the previous note,
    get random cadence tone
    get the octave using the previous note
    return the nameWithOctave
    """
    if CADENCE_TONE_FREQUENCY == "":
        print(
            "exit: Error get_nameWithOctave_from_cadence_tones called when CADENCE_TONE_FREQUENCY is blank"
        )
        sys.exit()
    else:
        # get random cadence tone
        cadence_tone = random.choice(CADENCE_TONE_SAMPLES)
        # print('cadence_tone=', cadence_tone)
        cadence_note = get_note_with_octave(n_prev, cadence_tone)
        print("cadence_note.nameWithOctave=", cadence_note.nameWithOctave)

    return cadence_note.nameWithOctave


def generate_markov_phrase_with_lyrics(
    sect,
    ts,
    tone_scale,
    tone_mode,
    transition,
    bpm_transition,
    dtransition,
    cad_transition,
    cad_dtransition,
    rest_note_transition,
    lyric_line,
    gmpwl_call_count,
):
    """
    function that uses musical markov chains and a lyric line to
    return a melodic stream with a line of lyrics
    """
    logger.debug(f"gmpwl Duration set: {DURATION_SET} (type: {type(DURATION_SET)})")
    logger.debug(f"gmpwl Duration set (PER_SECTION): {PER_SECTION_DURATION_SET}") 
    
    if gmpwl_call_count == 1:
        logger.debug(
            f"generate_markov_phrase_with_lyrics: sect {sect}, ts {ts}, tone_scale {tone_scale}, tone_mode {tone_mode}, \n---lyric_line--- {lyric_line}"
        )
        log_transition_analysis(transition, "Note transition: transition")
        log_transition_analysis(
            bpm_transition, "Beat placement transition: bpm_transition"
        )
        log_transition_analysis(dtransition, "Duration transition: dtransition")
        log_transition_analysis(
            cad_transition, "Cadence note transition: cad_transition"
        )
        log_transition_analysis(
            cad_dtransition, "Cadence duration transition: cad_dtransition"
        )
        log_transition_analysis(
            rest_note_transition, "Rest note transition: rest_note_transition"
        )

    p_stream = music21.stream.Stream()

    # random rest_note offset, REST_NOTE_LINE_OFFSET == None
    rest_note_key = ("0.0", "0.0")
    rest_note_draw = get_random_draw(rest_note_key, rest_note_transition)

    # following convert not required after fixing the transition matrix to not have string values
    # try:
    #     rest_note_draw = float(rest_note_draw)
    # except ValueError:
    #     rest_note_draw = float(Fraction(rest_note_draw))

    r = music21.note.Rest()
    r.duration.quarterLength = rest_note_draw

    if r.duration.quarterLength > 0:
        r.duration.quarterLength = validated_duration(
            r.duration.quarterLength, rest_note_transition, 0.0
        )
    print("Initial initial rest offset", r.duration.quarterLength)

    # override offset on the first note of each line
    if REST_NOTE_LINE_OFFSET != None:
        r.duration.quarterLength = REST_NOTE_LINE_OFFSET
        logger.debug(
            f"Overriding initial rest offset to REST_NOTE_LINE_OFFSET: {REST_NOTE_LINE_OFFSET}"
        )

    if r.duration.quarterLength > 0:
        p_stream.append(r)

        if is_bad_beat_placement(r.offset, ts):
            logger.debug(
                f"generate_markov_phrase_with_lyrics: is_bad_beat_placement r.offset {r.offset} "
            )

        show_text_of_note(r, ts)
        logger.debug(
            f"rest_note_draw non-zero == {r.duration.quarterLength} so first note of line will start then."
        )
    else:
        logger.debug(
            f"rest_note_draw == 0.0 so first note of line will start at the beginning of the bar."
        )

    # split and count syllables
    syllable_line = split_hyphens(lyric_line)
    # print('syllable_line', syllable_line)

    syllable_list = syllable_line.split()  # Split `a_string` by whitespace.
    # print('syllable_list', syllable_list)

    number_of_syllables = len(syllable_list)  ## counts he-llo as one syllable not two
    # print('number_of_syllables', number_of_syllables)

    # initialise duration_note_phrase length to initial rest (add each note length later)
    duration_note_phrase = r.duration.quarterLength

    # get new key for the new line
    # print("initial key",key)
    keys = get_keys(transition)
    key = get_random_key(keys)

    # get new beat placement matrix key (bpm_key) for the new line
    # print("initial duration key (bpm_key) ", bpm_key)
    bpm_keys = get_keys(bpm_transition)
    bpm_key = get_random_key(bpm_keys)
    logger.debug(
        "new beat placement matrix key (bpm_key) {bpm_key}"
    )  # e.g. ('3/4', '0')

    # get new duration key (dkey) for the new line
    # print("initial duration key (dkey) ", dkey)
    dkeys = get_keys(dtransition)
    dkey = get_random_key(dkeys)
    # print("new duration key (dkey)", dkey)  # e.g. ('1/12', '0.5') / ('1/6', '0.25') ...

    # Initialize variables for the first note:
    #     previous_pitch = None
    #     previous_offset = 0
    #     previous_duration = None

    # set up previous note
    n_prev = music21.note.Note(key[1])
    # determine the octave for the previous note
    octave = get_tone_octave(0, n_prev, 1)
    n_prev.octave = octave
    ddraw = get_random_draw(dkey, dtransition)

    # n_prev.duration.quarterLength = validated_duration(ddraw, dtransition, 1.0)
    # previous note length is the length of the rest
    n_prev.duration.quarterLength = r.duration.quarterLength

    # Append a note or a rest to the score
    # number of notes in phrase determined by the number_of_syllables
    for note_num in range(number_of_syllables):  # if range 6 then for 0 .. 5
        logger.debug(
            f"for {note_num} in range(number_of_syllables) {number_of_syllables} "
        )

        if note_num == number_of_syllables - 1:  # cadence note
            print("cadence note: use cad_transition cad_dtransition")
            n_prev, n = get_next_note(
                note_num,
                n_prev,
                tone_scale,
                tone_mode,
                key,
                cad_transition,
                bpm_key,
                bpm_transition,
                dkey,
                cad_dtransition,
                syllable_list[note_num],
                ts,
            )
        else:
            # use transition dtransition
            n_prev, n = get_next_note(
                note_num,
                n_prev,
                tone_scale,
                tone_mode,
                key,
                transition,
                bpm_key,
                bpm_transition,
                dkey,
                dtransition,
                syllable_list[note_num],
                ts,
            )

        # Determine the offset for the next note
        # next_offset = n_prev.offset + (n.beat - (n_prev.offset % 1))
        # if next_offset <= n_prev.offset:  # Ensure notes move forward
        #    next_offset += 1  # Force to the next beat cycle

        # Calculate the duration for the previous note (beat takes precedence)
        # if previous_duration is not None:
        # if note_num > 0:
        #    n_prev.duration.quarterLength = next_offset - n_prev.offset

        # Add the previous note to the stream if it's not the first iteration
        if note_num > 0:
            # Add a Note to melody_stream with:
            #    pitch = previous_pitch
            #    offset = previous_offset
            #    duration.quarterLength = previous_duration
            p_stream.append(n_prev)

            if is_bad_beat_placement(n_prev.offset, ts):
                logger.debug(
                    f"generate_markov_phrase_with_lyrics: is_bad_beat_placement n_prev.offset {n_prev.offset} lyric {n_prev.lyric} "
                )

            # p_stream.append(copy.deepcopy(n_prev))
            show_text_of_note(n_prev, ts)

        # Update variables for the next iteration
        # previous_pitch = current_pitch
        # previous_offset = next_offset
        # previous_duration = current_duration

        duration_note_phrase = duration_note_phrase + n.duration.quarterLength

        # increment keys for note beat and duration
        key = (key[1], n.name)

        # determine bpm_key
        beat_in_bar = get_beat_in_bar(n, ts)
        bp = fractional_part_as_fraction(beat_in_bar, ts)
        bpm_key = (bpm_key[1], str(bp))
        logger.debug(
            f"gmpwl determine bpm_key bpm_key[1] {bpm_key[1]}  bp {bp} bpm_key {bpm_key}"
        )

        # input("Press Enter to continue...")

        # determine dkey
        dkey = (dkey[1], str(n.duration.quarterLength))

        # change previous note
        n_prev = n
    # end of 'for note_num in range(number_of_syllables)'

    # Add the last note to the stream
    # Add a Note to melody_stream with:
    #    pitch = previous_pitch
    #    offset = previous_offset
    #    duration.quarterLength = previous_duration
    if CADENCE_TONE_FREQUENCY != "":
        n.nameWithOctave = get_nameWithOctave_from_cadence_tones(n_prev)
    p_stream.append(n)

    if is_bad_beat_placement(n.offset, ts):
        logger.debug(
            f"generate_markov_phrase_with_lyrics: is_bad_beat_placement cadence n.offset {n.offset} lyric {n_prev.lyric}"
        )

    show_text_of_note(n, ts)

    # Add rest up to end of bar
    duration_to_end_of_bar = calc_duration_to_end_of_bar(n, ts)
    if duration_to_end_of_bar > DURATION_MIN_MUSIC21:
        r = music21.note.Rest()
        r.duration.quarterLength = duration_to_end_of_bar
        p_stream.append(r)

        if is_bad_beat_placement(r.offset, ts):
            logger.debug(
                f"generate_markov_phrase_with_lyrics: is_bad_beat_placement r.offset {r.offset} "
            )

        show_text_of_note(r, ts)
        print("Added rest duration_to_end_of_bar", duration_to_end_of_bar)

    return p_stream


def parse(d, c):
    def parse_chain(d, c, p=[]):
        if isinstance(d, ast.Name):
            return [d.id] + p
        if isinstance(d, ast.Call):
            for i in d.args:
                parse(i, c)
            return parse_chain(d.func, c, p)
        if isinstance(d, ast.Attribute):
            return parse_chain(d.value, c, [d.attr] + p)

    if isinstance(d, (ast.Call, ast.Attribute)):
        c.append(".".join(parse_chain(d, c)))
    else:
        for i in getattr(d, "_fields", []):
            if isinstance(t := getattr(d, i), list):
                for i in t:
                    parse(i, c)
            else:
                parse(t, c)


def get_name_and_args(a_string):
    a_string = a_string.replace(" ", "")  # remove all spaces from a_string
    index = a_string.find("(")
    if index == -1:
        raise Exception("No '(' found")
    else:
        root_function, a_string = a_string[:index], a_string[index:]
        # print('root_function, a_string ',root_function, a_string)
        data = {}
        data[root_function] = (
            pyparsing.nestedExpr().parseString(a_string).asList()[0][0].split(",")
        )
        return data


def is_post_processing_function(s):
    """
    function that parses a string and
    returns true if it is a python function
    """
    s1 = "copy"
    s2 = "transpose"
    s3 = "invert"
    s4 = "reverse"

    result = True

    try:
        # print(ast.dump(ast.parse(s, mode='eval'), indent=4))
        ast.dump(ast.parse(s, mode="eval"), indent=4)
    except BaseException as err:
        # print(f"Unexpected {err=}, {type(err)=}")
        logger.debug("Not a function call")
        result = False
    # check contains a valid function name
    if result:

        # tree = ast.parse(s, mode='eval')
        # print('tree =', tree)
        results = []
        parse(ast.parse(s), results)
        # print('results = ', results)
        # if not a known post_processing_function call
        if results == []:
            result = False
            print("Cannot parse a function call")
        else:
            if (
                (results[0].casefold() != s1.casefold())
                and (results[0].casefold() != s2.casefold())
                and (results[0].casefold() != s3.casefold())
                and (results[0].casefold() != s4.casefold())
            ):
                print("Not a known function call e.g.", s1, s2, s3, s4)
                result = False
        # else:
        # # get call attributes
        # call_attributes = get_name_and_args(s)
        # print('call_attributes', call_attributes)
    return result


def valid_copy_post_processing_function(v):
    """
    boolean function that checks the copy function arguments
    e.g. copy(verse,1) to copy verse line 1
    returns True if they are valid
    """
    result = True

    # getting length of list
    length = len(v)
    if length != 2:
        print("Checking valid_copy_post_processing_function. # wrong number of args")
        result = False
    else:
        # Iterating the index
        for i in range(length):
            # print('arg_num arg', i, v[i])
            # validate section name
            if i == 0:
                if v[i].casefold() not in _section_name_matches:
                    result = False
            # validate line number to copy is an integer > 1
            if i == 1:
                try:
                    # if not int(v[i]).isnumeric():
                    if not isinstance(int(v[i]), int):
                        print(
                            "Checking valid_copy_post_processing_function arg 2: Expecting integer"
                        )
                        result = False
                        break
                except ValueError:
                    print(
                        "Checking valid_copy_post_processing_function arg 2: Expecting int"
                    )
                    result = False
                    break
                if int(v[i]) < 1:
                    print(
                        "Checking valid_copy_post_processing_function arg 2: Expecting integer > 0"
                    )
                    result = False

    return result


def valid_transpose_post_processing_function(v):
    """
        boolean function that checks the transpose function arguments
        e.g. transpose(verse,1,-4) to transpose verse line 1 down a fourth
        GenericInterval permitted range -32 to 32, Note: 0 illegal.

        Transposition by GenericInterval does what we want.  See the last example here:
        https://web.mit.edu/music21/doc/usersGuide/usersGuide_18_intervals.html

    import music21
    from music21 import *
    s3 = converter.parse("tinyNotation: 4/4 c4 d e f g a b")
    s3.show()

    # key-aware modal transpositions on Streams:
    # negative GenericInterval also in key (tested -32 to 32) Note: 0 illegal
    s4 = s3.transpose(interval.GenericInterval(-3))
    s4.show()

        returns True if they are valid
    """
    result = True

    # getting length of list
    length = len(v)
    if length != 3:
        print(
            "Checking valid_transpose_post_processing_function. # wrong number of args"
        )
        result = False
    else:
        # Iterating the index
        for i in range(length):
            # print('arg_num arg', i, v[i])
            # validate section name
            if i == 0:
                if v[i].casefold() not in _section_name_matches:
                    result = False
            # validate line number to copy is an integer > 1
            if i == 1:
                try:
                    # if not int(v[i]).isnumeric():
                    if not isinstance(int(v[i]), int):
                        print(
                            "Checking valid_transpose_post_processing_function arg 2: Expecting integer"
                        )
                        result = False
                        break
                except ValueError:
                    print(
                        "Checking valid_transpose_post_processing_function arg 2: Expecting int"
                    )
                    result = False
                    break
                if int(v[i]) < 1:
                    print(
                        "Checking valid_transpose_post_processing_function arg 2: Expecting integer > 0"
                    )
                    result = False
            # validate GenericInterval permitted range -32 to 32, Note: 0 illegal.
            if i == 2:
                try:
                    # if not int(v[i]).isnumeric():
                    if not isinstance(int(v[i]), int):
                        print(
                            "Checking valid_transpose_post_processing_function arg 2: Expecting integer"
                        )
                        result = False
                        break
                except ValueError:
                    print(
                        "Checking valid_transpose_post_processing_function arg 2: Expecting int"
                    )
                    result = False
                    break
                if int(v[i]) == 0:
                    print(
                        "Checking valid_transpose_post_processing_function arg 2: Not Expecting integer = 0"
                    )
                    result = False
                if (int(v[i]) < -32) or (int(v[i]) > 32):
                    print(
                        "Checking valid_transpose_post_processing_function arg 2 =",
                        int(v[i]),
                        "# Not Expecting integer < -32 or > 32",
                    )
                    result = False
    return result


def valid_invert_post_processing_function(v):
    """
        boolean function that checks the invert function arguments
        e.g. invert(verse,1,C4) to invert verse line 1 around C4

    import music21
    from music21 import *
    s1 = converter.parse("tinyNotation: 4/4 c4 d e f g a b")
    s2 = s1.invertDiatonic(note.Note('C4'), inPlace=False)
    s2.show()

        returns True if they are valid
    """
    result = True

    # getting length of list
    length = len(v)
    if length != 3:
        print("Checking valid_invert_post_processing_function. # wrong number of args")
        result = False
    else:
        # Iterating the index
        for i in range(length):
            # print('arg_num arg', i, v[i])
            # validate section name
            if i == 0:
                if v[i].casefold() not in _section_name_matches:
                    result = False
            # validate line number to copy is an integer > 1
            if i == 1:
                try:
                    # if not int(v[i]).isnumeric():
                    if not isinstance(int(v[i]), int):
                        print(
                            "Checking valid_invert_post_processing_function arg 2: Expecting integer"
                        )
                        result = False
                        break
                except ValueError:
                    print(
                        "Checking valid_invert_post_processing_function arg 2: Expecting int"
                    )
                    result = False
                    break
                if int(v[i]) < 1:
                    print(
                        "Checking valid_invert_post_processing_function arg 2: Expecting integer > 0"
                    )
                    result = False
            if i == 2:
                try:
                    n = note.Note(str(v[i]))
                    print(
                        "invert around pitch",
                        n,
                        " pitch.nameWithOctave",
                        n.nameWithOctave,
                    )
                except BaseException as err:
                    print(f"Unexpected {err=}, {type(err)=}")
                    print(
                        "Checking valid_invert_post_processing_function arg 2: Expecting pitch e.g. C4"
                    )
                    result = False

    return result


def valid_reverse_post_processing_function(v):
    """
    boolean function that checks the reverse function arguments
    e.g. reverse(verse,1) to reverse verse line 1
    returns True if they are valid
    """
    result = True

    # getting length of list
    length = len(v)
    if length != 2:
        print("Checking valid_reverse_post_processing_function. # wrong number of args")
        result = False
    else:
        # Iterating the index
        for i in range(length):
            # print('arg_num arg', i, v[i])
            # validate section name
            if i == 0:
                if v[i].casefold() not in _section_name_matches:
                    result = False
            # validate line number to reverse is an integer > 1
            if i == 1:
                try:
                    # if not int(v[i]).isnumeric():
                    if not isinstance(int(v[i]), int):
                        print(
                            "Checking valid_reverse_post_processing_function arg 2: Expecting integer"
                        )
                        result = False
                        break
                except ValueError:
                    print(
                        "Checking valid_reverse_post_processing_function arg 2: Expecting int"
                    )
                    result = False
                    break
                if int(v[i]) < 1:
                    print(
                        "Checking valid_reverse_post_processing_function arg 2: Expecting integer > 0"
                    )
                    result = False

    return result


def get_lyrics(qualified_filename):
    """
    function that reads a file and
    returns text
    """
    comment_char = "#"
    call_attributes_list = []
    lines = []

    with open(qualified_filename) as file_in:
        for line in file_in:
            line = line.strip()
            call_attributes = None
            # if line has comment
            if comment_char in line:
                ls = line.split(comment_char, maxsplit=1)
                line = ls[0].strip()
                comment = ls[1].strip()
                logger.debug("")
                logger.debug(f"Lyric = {line}")
                logger.debug(f"Comment = {comment}")
                # try:
                #     result = is_post_processing_function(comment)
                # except BaseException as err:
                #     print(f"Unexpected {err=}, {type(err)=}")
                #     print('exit: invalid post processing function:', comment)
                #     sys.exit()
                if is_post_processing_function(comment):
                    # print('Comment is_post_processing_function.')
                    # validate ppf (correct type and number of args) e.g.
                    # if copy then if not valid_copy_post processing function(s): exit
                    # if transpose then if not valid_transpose_post processing function(s): exit

                    # get call attributes
                    try:
                        call_attributes = get_name_and_args(comment)
                    except BaseException as err:
                        print(f"Unexpected {err=}, {type(err)=}")
                        print("exit: invalid post processing function:", comment)
                        sys.exit()
                    call_attributes = get_name_and_args(comment)

                    # loop on key and value
                    for k, v in call_attributes.items():
                        if k == "copy":
                            # print('found copy')
                            if not valid_copy_post_processing_function(v):
                                print(
                                    "exit: invalid copy, e.g. expect: copy(verse,1) actual parse:",
                                    call_attributes,
                                )
                                sys.exit()
                            else:
                                print(
                                    "valid_copy_post_processing_function: ",
                                    call_attributes,
                                )
                        if k == "transpose":
                            # print('found transpose')
                            if not valid_transpose_post_processing_function(v):
                                print(
                                    "exit: invalid transpose, e.g. expect: transpose(verse,1,-4) actual parse:",
                                    call_attributes,
                                )
                                sys.exit()
                            else:
                                print(
                                    "valid_transpose_post_processing_function: ",
                                    call_attributes,
                                )
                        if k == "invert":
                            # print('found invert')
                            if not valid_invert_post_processing_function(v):
                                print(
                                    "exit: invalid invert, e.g. expect: invert(verse,1,C4) actual parse:",
                                    call_attributes,
                                )
                                sys.exit()
                            else:
                                print(
                                    "valid_invert_post_processing_function: ",
                                    call_attributes,
                                )
                        if k == "reverse":
                            # print('found reverse')
                            if not valid_reverse_post_processing_function(v):
                                print(
                                    "exit: invalid reverse, e.g. expect: reverse(verse,1) actual parse:",
                                    call_attributes,
                                )
                                sys.exit()
                            else:
                                print(
                                    "valid_reverse_post_processing_function: ",
                                    call_attributes,
                                )

            lines.append(line)
            call_attributes_list.append(call_attributes)

    # print('lines', lines)
    # print('call_attributes_list', call_attributes_list)

    return lines, call_attributes_list


# def hyphenate_lyrics(qualified_filename):
# """
# function that reads a file and
# returns a hyphenated text
# """
# # pyphen not good enough at hypenating, so ask user to hypenate input lyrics file e.g
# #  y-ou y-our -though n-a-tion-s -greatest An-d
# # Use an online tool e.g. https://melobytes.com/en/app/syllabication
# #
# # split words into syllables
# # consider looking up the words in a text-to-speech dictionary and count the phonemes that encode vowel sounds.
# #  TeX approach to this problem for the purposes of hyphenation. Especially see Frank Liang's thesis dissertation Word Hy-phen-a-tion by Com-put-er. http://www.tug.org/docs/liang/
# # https://stackoverflow.com/questions/63268786/how-to-get-all-the-syllables-of-a-word-in-python

# matches = ["Verse", "Chorus", "Bridge"]
# a = pyphen.Pyphen(lang='en')
# with open(qualified_filename) as file_in:
# lines = []
# for line in file_in:
# line = line.strip()
# # do not hyphenate section names
# if any(x in line for x in matches):
# lines.append(line)
# else:
# lines.append(a.inserted(line))


# print('lines', lines)

# return lines


def is_number_an_integer(user_number):
    """
    given a user_number
    return True if it is an integer
    """

    is_int = True
    try:
        int(user_number)
    except:
        # print("That's not an integer number.")
        is_int = False
    return is_int


def set_cadence(stream):
    """
    function that takes a stream
    and returns markov chains for the cadences (last three notes of a phrase)
    """
    print("get_cadence")

    cad_transition = {}
    prev_1 = prev = last = None
    total = 0

    # Gather cadence transition-----------------------------------------------------------------
    # for n in stream.flatten().notes: # no rests in flat.notes
    for n in stream.flatten():

        if type(n) == music21.note.Note:
            if (prev_1 == None) and (prev == None) and (last == None):
                last = n
            if (prev_1 == None) and (prev == None) and (last != None):
                prev = last
                last = n
            if (prev_1 == None) and (prev != None) and (last != None):
                prev_1 = prev
                prev = last
                last = n
            if (prev_1 != None) and (prev != None) and (last != None):
                prev_1 = prev
                prev = last
                last = n

        if type(n) == music21.note.Rest:
            # print('prev_1 , prev , last = ', prev_1, prev, last)
            if (prev_1 != None) and (prev != None) and (last != None):
                key = (prev_1.name, prev.name)
                # print(key) # e.g. ('C', 'A')
                if key in cad_transition:
                    if last.name in cad_transition[key]:
                        cad_transition[key][last.name] += 1
                    else:
                        cad_transition[key][last.name] = 1
                else:
                    cad_transition[key] = {last.name: 1}
                total += 1
                prev_1 = prev = last = None

    print("cad_transition with frequencies", total, cad_transition)
    print("total_frequency=", total)

    # if no rests then use a default C major cadence transition
    if cad_transition == {}:
        cad_transition = {
            ("C", "B"): {"C": 1},
            ("C", "D"): {"C": 1},
            ("C", "G"): {"C": 1},
            ("D", "C"): {"B": 2},
            ("E", "D"): {"C": 1},
            ("F", "C"): {"G": 2},
            ("G", "D"): {"E": 2},
        }
        total = 10
        print("No cad_transitions found, using default with frequency=", cad_transition)
        print("total_frequency=", total)
    else:
        cad_transition, total = apply_tone_eq_to_transition_frequency(
            cad_transition, total, True
        )
        print("After apply_tone_eq_to_cad_transition_frequency")
        print("note cad_transition with frequency=", cad_transition)
        print("total_frequency=", total)

    # Compute the probability for each cad_transition
    cad_transition_total_probability = 0.0
    for k, v in cad_transition.items():
        for i, j in v.items():
            cad_transition[k][i] = j / total
            cad_transition_total_probability = (
                cad_transition_total_probability + cad_transition[k][i]
            )
    print("cad_transition_total_probability = ", cad_transition_total_probability)
    print("cad_transition with probability", cad_transition)

    return cad_transition


def is_bad_duration(quarterLength):
    """
    function that takes a duration and
    returns True if it is on the DUR_BLACKLIST
    """
    # print('is_bad_duration(quarterLength)', quarterLength)
    is_bad = False

    # print(quarterLength - int(quarterLength) == 0)  # True if x is a whole number, False if it has decimals.
    if quarterLength - int(quarterLength) == 0:
        # print('quarterLength is a whole number', quarterLength)
        pass
    else:
        if (
            Fraction(quarterLength).numerator == 7
            or Fraction(quarterLength).denominator == 7
        ):
            print("bad fraction", quarterLength)
            is_bad = True

    # print("is_bad ", is_bad)

    return is_bad


def is_cadence(n, flat_stream):
    """
    If the element n in a flat stream is a cadence note then
    return true
    example cadence notes:
    c (end of song)
    n c ... r           # if the next (note or rest) is a rest
    n c ...(end of song) # if there is no other note to the end of the song
    """
    is_cadence_note = False

    # c (end of song)
    if n == len(flat_stream):
        return True  # is_cadence and avoid going off end of list below

    #     n c ... r           # if the next (note or rest) is a rest
    for element_num in range((n + 1), len(flat_stream)):
        if (
            type(flat_stream[element_num]) == music21.note.Rest
            or type(flat_stream[element_num]) == music21.note.Note
        ):
            if type(flat_stream[element_num]) == music21.note.Rest:
                return True  # is_cadence
            if type(flat_stream[element_num]) == music21.note.Note:
                break

    # n c ...(end of song) # if there is no other note to the end of the song
    following_note = False
    for element_num in range((n + 1), len(flat_stream)):
        if type(flat_stream[element_num]) == music21.note.Note:
            following_note = True  # is_cadence
    if following_note == False:
        return True  # is_cadence
    return is_cadence_note


def is_bad_beat_placement(value, time_signature):
    """
    Function that takes a value, converts it to a beat_placement within a beat,
    and returns True if the beat_placement is_bad_beat_placement.

    Args:
        value (float): The value to check.
        time_signature (music21.meter.TimeSignature): The time signature of the piece.

    Returns:
        bool: True if the beat_placement is_bad_beat_placement, False otherwise.
    """
    if value < 0:
        raise ValueError("Negative values are not allowed")

    beat_placement = fractional_part_as_fraction(value, time_signature)

    # Check against BEAT_PLACEMENTS_DENIED_SET
    if beat_placement in BEAT_PLACEMENTS_DENIED_SET:
        logger.debug(
            f"is_bad_beat_placement {value} {time_signature} ,in BEAT_PLACEMENTS_DENIED_SET beat_placement {beat_placement} beat_placement.denominator {beat_placement.denominator} - Time Signature: {time_signature}"
        )
        return True

    # Check against BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET
    if beat_placement.denominator in BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET:
        logger.debug(
            f"is_bad_beat_placement {value} {time_signature} ,in BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET. beat_placement {beat_placement} beat_placement.denominator {beat_placement.denominator} - Time Signature: {time_signature}"
        )
        return True

    # Check against BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED
    if BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED > 0:
        if beat_placement.denominator > BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED:
            logger.debug(
                f"is_bad_beat_placement {value} {time_signature} beat_placement: {beat_placement} beat_placement.denominator: {beat_placement.denominator} > BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED: {BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED} - Time Signature: {time_signature}"
            )
            return True

    return False


def set_bpm_transition(song, time_signature):
    """
    function that takes a song and
    returns bpm_transition -the beat placement matrix transition
    """
    logger.info(f"set_bpm_transition(song) {song} ")

    bpm_transition = {}

    prev = None
    last = None
    bpm_total = 0
    bad_beat = False
    number_of_rests = 0
    number_of_notes = 0
    number_of_elements = len(song.flatten())
    element_num = 0

    # Gather the beat transitions
    # for n in song.flatten().notes:
    for n in song.flatten():
        if type(n) == music21.note.Rest:
            number_of_rests = number_of_rests + 1
        if type(n) == music21.note.Note:
            if (n.tie is None) or (n.tie is not None and n.tie.type == "start"):
                number_of_notes = number_of_notes + 1

                # calculate beat placement where 0 is on beat, and > 0 but less than 1 is off beat
                bp = fractional_part_as_fraction(n.beat, time_signature)
                logger.debug(
                    f"n.duration.quarterLength  {n.duration.quarterLength} n.beat {n.beat} bp {bp} \t {n.pitch}"
                )

                if prev:
                    if last:
                        if (
                            is_bad_beat_placement(prev.beat, time_signature)
                            or is_bad_beat_placement(last.beat, time_signature)
                            or is_bad_beat_placement(n.beat, time_signature)
                            # or is_cadence(element_num, song.flatten())
                        ):
                            bad_beat = True
                            logger.debug(
                                f"Skipping bad beat. prev last current n beat: {prev.beat} , {last.beat} , {n.beat}"
                            )
                        else:
                            dkey = (
                                str(
                                    fractional_part_as_fraction(
                                        prev.beat, time_signature
                                    )
                                ),
                                str(
                                    fractional_part_as_fraction(
                                        last.beat, time_signature
                                    )
                                ),
                            )

                            # print(dkey) # e.g. (0.25, Fraction(1, 3))
                            # in python how to find if a key contains a Fraction with a particular number ?
                            # print(x - int(x) == 0)  # True if x is a whole number, False if it has decimals.
                            if dkey in bpm_transition:
                                if (
                                    fractional_part_as_fraction(n.beat, time_signature)
                                    in bpm_transition[dkey]
                                ):
                                    # if str(fractional_part_as_fraction(n.beat, time_signature)) in bpm_transition[dkey]: # does not match 0.5 etc
                                    # if float(fractional_part_as_fraction(n.beat, time_signature)) in bpm_transition[dkey]: # works but float() not required
                                    bpm_transition[dkey][
                                        fractional_part_as_fraction(
                                            n.beat, time_signature
                                        )
                                    ] += 1
                                else:
                                    bpm_transition[dkey][
                                        fractional_part_as_fraction(
                                            n.beat, time_signature
                                        )
                                    ] = 1
                            else:
                                bpm_transition[dkey] = {
                                    fractional_part_as_fraction(
                                        n.beat, time_signature
                                    ): 1
                                }
                        prev = last
                        if bad_beat == False:
                            bpm_total += 1
                        bad_beat = False
                    last = n
                else:
                    prev = n
            element_num = element_num + 1

    logger.debug(
        f"input music: number_of_rests = {number_of_rests}, number_of_notes = {number_of_notes}, number_of_elements = {number_of_elements}"
    )
    logger.debug(f"bpm transitions with frequency {bpm_transition}")
    logger.debug(f"bpm total_frequency = {bpm_total}")

    # Compute the probability for each bpm_transition
    bpm_transition_bpm_total_probability = 0.0
    for k, v in bpm_transition.items():
        for i, j in v.items():
            bpm_transition[k][i] = j / bpm_total
            bpm_transition_bpm_total_probability = (
                bpm_transition_bpm_total_probability + bpm_transition[k][i]
            )
    logger.debug(
        f"bpm_transition_bpm_total_probability = {bpm_transition_bpm_total_probability}"
    )
    # print('bpm_total durations = ',bpm_total)
    # print(' ')
    logger.debug(f"bpm transitions with probability {bpm_transition}")

    # input("Press Enter to continue... end of set_bpm_transition")

    return bpm_transition


def set_duration_transition(song):
    """
    function that takes a song and
    returns the markov duration transition
    (not including the cadence durations - the last notes of phrases).
    """
    dtransition = {}

    prev = None
    last = None
    dtotal = 0
    bad_duration = False
    number_of_rests = 0
    number_of_notes = 0
    number_of_elements = len(song.flatten())
    element_num = 0

    # Gather the duration transitions
    # for n in song.flatten().notes:
    for n in song.flatten():
        if type(n) == music21.note.Rest:
            number_of_rests = number_of_rests + 1
        if type(n) == music21.note.Note:
            number_of_notes = number_of_notes + 1
            if prev:
                if last:
                    if (
                        is_bad_duration(prev.duration.quarterLength)
                        or is_bad_duration(last.duration.quarterLength)
                        or is_cadence(element_num, song.flatten())
                    ):
                        bad_duration = True
                        # print('Skipping cadence or bad duration. prev last current:', prev.duration.quarterLength, last.duration.quarterLength, n.duration.quarterLength)
                    else:  #
                        # dkey = (prev.duration.quarterLength, last.duration.quarterLength)
                        dkey = (
                            str(prev.duration.quarterLength),
                            str(last.duration.quarterLength),
                        )

                        # print(dkey) # e.g. (0.25, Fraction(1, 3))
                        # in python how to find if a key contains a Fraction with a particular number ?
                        # print(x - int(x) == 0)  # True if x is a whole number, False if it has decimals.
                        if dkey in dtransition:
                            if n.duration.quarterLength in dtransition[dkey]:
                                # if str(n.duration.quarterLength) in dtransition[dkey]: # does not match 0.5 etc
                                # if float(n.duration.quarterLength) in dtransition[dkey]: # works but float() not required
                                dtransition[dkey][n.duration.quarterLength] += 1
                            else:
                                dtransition[dkey][n.duration.quarterLength] = 1
                        else:
                            dtransition[dkey] = {n.duration.quarterLength: 1}
                    prev = last
                    if bad_duration == False:
                        dtotal += 1
                    bad_duration = False
                last = n
            else:
                prev = n
        element_num = element_num + 1

    # print(' ')
    print(
        "input music: number_of_rests = ",
        number_of_rests,
        " number_of_notes = ",
        number_of_notes,
        "number_of_elements =",
        number_of_elements,
    )
    print("duration transitions with frequency", dtransition)
    print("dtotal_frequency=", dtotal)

    # # Compute the probability for each transition -----------------------------------------------------------
    # ptotal = 0
    # for k, v in dtransition.items():
    #     for i, j in v.items():
    #         dtransition[k][i] = j / dtotal
    #         ptotal = ptotal + dtransition[k][i]
    #
    # # print('dtotal Notes = ',dtotal) # eg 360
    # # print('ptotal duration = ',ptotal) # e.g. 0.99
    # # print(' ')
    # print('duration transitions with probability', dtransition)

    dtransition, dtotal = apply_duration_eq_to_dtransition_frequency(
        dtransition, dtotal, False
    )

    print("After apply_duration_eq_to_dtransition_frequency")
    print("duration transition with frequency=", dtransition)
    print("dtotal_frequency=", dtotal)

    # Compute the probability for each dtransition
    dtransition_dtotal_probability = 0.0
    for k, v in dtransition.items():
        for i, j in v.items():
            dtransition[k][i] = j / dtotal
            dtransition_dtotal_probability = (
                dtransition_dtotal_probability + dtransition[k][i]
            )
    print("dtransition_dtotal_probability = ", dtransition_dtotal_probability)
    # print('dtotal durations = ',dtotal)
    # print(' ')
    print("duration transitions with probability", dtransition)

    # input('Press Enter to continue... end of set_duration_transition')

    return dtransition


def get_frequency_total(transition):
    """
    given a transition with frequencies
    calculate and return the total frequency
    """
    total = 0
    for k, v in transition.items():
        for i, j in v.items():
            total = total + j
            # transition[k][i] = j / total
    # print('get_frequency_total =', total)
    return total


def apply_tone_eq_to_transition_frequency(transition, total, is_cadence):
    """
    given a transition and a total, and if it is a cadence transition
    apply TONE_EQ to the transition
    recalculate the total frequency
    return the transition, total
    """
    print("Apply_tone_eq_to_transition_frequency...")

    cadence_factor = 100.0

    if TONE_EQ == "":
        return transition, total
    else:
        # alter transition frequencies
        for tone_eq_num in range(0, len(TONE_EQ)):
            tone_name = TONE_EQ[tone_eq_num][0]
            tone_factor = TONE_EQ[tone_eq_num][1]
            print(
                "tone_eq_num=",
                tone_eq_num,
                "tone_name=",
                tone_name,
                "tone_factor=",
                tone_factor,
            )
            for k, v in transition.items():
                for i, j in v.items():
                    # print('if i == tone_name', i, ' == ', tone_name)
                    if i == tone_name:
                        # print('before transition[k][i]=',transition[k][i])
                        if is_cadence:
                            transition[k][i] = int(
                                math.ceil(
                                    transition[k][i] * tone_factor * cadence_factor
                                )
                            )
                        else:
                            transition[k][i] = int(
                                math.ceil(transition[k][i] * tone_factor)
                            )
                        # print('after transition[k][i]=',transition[k][i])

        # recalculate total frequency
        total = get_frequency_total(transition)

        return transition, total


def apply_duration_eq_to_dtransition_frequency(dtransition, dtotal, is_cadence):
    """
    given a duration transition and a dtotal, and if it is a cadence duration transition
    apply DURATION_EQ to the transition
    recalculate the dtotal frequency
    return the transition, dtotal
    """
    print("apply_duration_eq_to_dtransition_frequency...")

    cadence_factor = 100.0

    if DURATION_EQ == "":
        return dtransition, dtotal
    else:
        # alter dtransition frequencies
        for duration_eq_num in range(0, len(DURATION_EQ)):
            duration_name = DURATION_EQ[duration_eq_num][0]
            duration_factor = DURATION_EQ[duration_eq_num][1]
            # print('duration_eq_num=',duration_eq_num,'duration_name=', duration_name,'duration_factor=', duration_factor)
            for k, v in dtransition.items():
                for i, j in v.items():
                    # make a string fraction of the duration
                    istring = (
                        "Fraction("
                        + str(Fraction(i).numerator)
                        + ", "
                        + str(Fraction(i).denominator)
                        + ")"
                    )
                    # print('type(istring) =', type(istring) )
                    # print('type(i) =', type(i), 'type(duration_name) =', type(duration_name) )
                    # print('if i == duration_name', i, ' == ', duration_name)
                    # if i == duration_name:
                    # if float(i) == float(duration_name):
                    # if str(i) in duration_name:
                    if (str(i) in duration_name) or (istring == duration_name):
                        print(
                            "(istring == duration_name):",
                            istring,
                            " == ",
                            duration_name,
                        )
                        print("before dtransition[k][i]=", dtransition[k][i])
                        if is_cadence:
                            dtransition[k][i] = int(
                                math.ceil(
                                    dtransition[k][i] * duration_factor * cadence_factor
                                )
                            )
                        else:
                            dtransition[k][i] = int(
                                math.ceil(dtransition[k][i] * duration_factor)
                            )
                        print("after dtransition[k][i]=", dtransition[k][i])

        # recalculate dtotal frequency
        dtotal = get_frequency_total(dtransition)

        return dtransition, dtotal


def set_note_transition(song):
    """
    function that takes a song and
    returns the markov note transition
    (not including the cadence notes - the last notes of phrases).
    """

    transition = {}

    prev = None
    last = None
    total = 0
    cadence_note = False
    element_num = 0

    # Gather the pitch transitions -----------------------------------------------------------------
    # flat returns a new Stream that has all sub-containers “flattened” within it, that is, it returns a new Stream where no elements nest within other elements.
    # The notes property of a Stream returns an iterator that consists only of the notes (that is, Note, Chord, etc.) found in the stream.
    # This excludes Rest objects.

    for n in song.flatten():
        if type(n) == music21.note.Note:
            if prev:
                if last:
                    if is_cadence(element_num, song.flatten()):
                        cadence_note = True
                        # print('Skipping cadence note. prev last current:', prev.nameWithOctave,
                        #       last.nameWithOctave, n.nameWithOctave)
                    else:
                        key = (prev.name, last.name)
                        # print(key) # e.g. ('C', 'A')
                        if key in transition:
                            if n.name in transition[key]:
                                transition[key][n.name] += 1
                            else:
                                transition[key][n.name] = 1
                        else:
                            transition[key] = {n.name: 1}
                    prev = last
                    if cadence_note == False:
                        total += 1
                    cadence_note = False
                last = n
            else:
                prev = n
        element_num = element_num + 1

    print(
        "note transitions with frequency=", transition
    )  # e.g. {('A', 'A'): {'G': 15, 'D': 4, 'B-': 1, 'A': 2, 'B': 1, 'F': 1, 'C': 1}, ('A', 'G'): {'F': 10, 'G': 6, 'F#': 2}, ...
    print("total_frequency=", total)

    transition, total = apply_tone_eq_to_transition_frequency(transition, total, False)

    print("After apply_tone_eq_to_transition_frequency")
    print("note transition with frequency=", transition)
    print("total_frequency=", total)

    # input('Press Enter to continue...')

    # Compute the probability for each transition
    transition_total_probability = 0.0
    for k, v in transition.items():
        for i, j in v.items():
            transition[k][i] = j / total
            transition_total_probability = (
                transition_total_probability + transition[k][i]
            )
    print("transition_total_probability = ", transition_total_probability)
    # print('total Notes = ',total)
    # print(' ')
    print("note transitions with probability", transition)
    return transition


#
# def set_rest_phrase_lengths(stream):
#     """
#     function that takes a stream
#     and returns markov chains for rest phrase lengths
#     If the phrase starts immediately after a bar then the initial rest = 0 and
#     the rest_phrase_transition will be ('prev', 'last'): {0.0: f} where 0.0 means no rest at the beginning and f is the frequency is added.
#
#     """
#     # print('rest_phrase_lengths')
#     # stream.show() # xml fragment hangs python on MuseScore
#     rest_phrase_transition = {}
#
#     # Gather the rest phrase length transitions.
#     # Ignore rests longer than MAX_PHRASE_REST e.g. first rest, instrumental solo rest, last rest
#     prev = None
#     last = None
#     dtotal = 0
#     for n in stream.flatten():
#         if type(n) == music21.note.Rest:
#             if n.duration.quarterLength < MAX_PHRASE_REST:
#                 # print('rest between phrases found. duration.quarterLength ', n, n.duration.quarterLength)
#                 if prev:
#                     if last:
#                         # dkey = (prev.duration.quarterLength, last.duration.quarterLength)
#                         dkey = (str(prev.duration.quarterLength), str(last.duration.quarterLength))
#                         # print(dkey) # e.g. (0.25, Fraction(1, 3))
#                         if dkey in rest_phrase_transition:
#                             if str(n.duration.quarterLength) in rest_phrase_transition[dkey]:
#                                 rest_phrase_transition[dkey][n.duration.quarterLength] += 1
#                             else:
#                                 rest_phrase_transition[dkey][n.duration.quarterLength] = 1
#                         else:
#                             rest_phrase_transition[dkey] = {n.duration.quarterLength: 1}
#                             # print('Using rest phrase . prev last current:', prev.duration.quarterLength,
#                             #       last.duration.quarterLength, n.duration.quarterLength)
#                         prev = last
#                         dtotal += 1
#                     last = n
#                 else:
#                     prev = n
#
#     # print('dtotal, rest_phrase_transition 1 ', dtotal, rest_phrase_transition)
#
#     # if no rests then use a default
#     if rest_phrase_transition == {}:
#         # rest_phrase_transition = {(1.0, 1.0): {2.0: 1, 3.0: 1}, (1.0, 2.0): {2.0: 1, 3.0: 1}, (2.0, 3.0): {2.0: 1, 3.0: 1}}
#         rest_phrase_transition = {('1.0', '1.0'): {2.0: 1, 3.0: 1}, ('1.0', '2.0'): {2.0: 1, 3.0: 1}, ('2.0', '3.0'): {2.0: 1, 3.0: 1}}
#         dtotal = 6
#
#     # Compute the probability for each transition -----------------------------------------------------------
#     ptotal = 0
#     for k, v in rest_phrase_transition.items():
#         for i, j in v.items():
#             rest_phrase_transition[k][i] = j / dtotal
#             ptotal = ptotal + rest_phrase_transition[k][i]
#
#     # print('dtotal Notes = ',dtotal) # eg 360
#     # print('ptotal duration = ',ptotal) # e.g. 0.99
#     # print('rest_phrase_transition 2', rest_phrase_transition)
#     # print(rest_phrase_transition) # e.g. {(Fraction(2, 3), 1.25): {1.5: 0.03225806451612903}, (1.25, 1.5): {1.25: 0.03225806451612903}, (1.5, 1.25): {2.0: 0.03225806451612903, 1.25: 0.03225806451612903}, (1.25, 2.0): {Fraction(5, 3): 0.03225806451612903}, (2.0, Fraction(5, 3)): {Fraction(5, 3): 0.03225806451612903}, (Fraction(5, 3), Fraction(5, 3)): {1.5: 0.03225806451612903}, (Fraction(5, 3), 1.5): {1.25: 0.03225806451612903}, (1.25, 1.25): {7.75: 0.03225806451612903, 1.75: 0.03225806451612903, Fraction(1, 3): 0.03225806451612903}, (1.25, 7.75): {Fraction(1, 3): 0.03225806451612903}, (7.75, Fraction(1, 3)): {5.5: 0.03225806451612903}, (Fraction(1, 3), 5.5): {Fraction(1, 3): 0.16129032258064516, 5.75: 0.03225806451612903}, (5.5, Fraction(1, 3)): {5.5: 0.12903225806451613, 7.0: 0.03225806451612903}, (Fraction(1, 3), 7.0): {1.25: 0.03225806451612903}, (7.0, 1.25): {1.25: 0.03225806451612903}, (1.25, 1.75): {0.5: 0.03225806451612903}, (1.75, 0.5): {1.25: 0.03225806451612903}, (0.5, 1.25): {1.25: 0.03225806451612903}, (1.25, Fraction(1, 3)): {5.5: 0.03225806451612903}, (5.5, 5.75): {5.75: 0.03225806451612903}}{(Fraction(2, 3), 1.25): {1.5: 0.03225806451612903}, (1.25, 1.5): {1.25: 0.03225806451612903}, (1.5, 1.25): {2.0: 0.03225806451612903, 1.25: 0.03225806451612903}, (1.25, 2.0): {Fraction(5, 3): 0.03225806451612903}, (2.0, Fraction(5, 3)): {Fraction(5, 3): 0.03225806451612903}, (Fraction(5, 3), Fraction(5, 3)): {1.5: 0.03225806451612903}, (Fraction(5, 3), 1.5): {1.25: 0.03225806451612903}, (1.25, 1.25): {7.75: 0.03225806451612903, 1.75: 0.03225806451612903, Fraction(1, 3): 0.03225806451612903}, (1.25, 7.75): {Fraction(1, 3): 0.03225806451612903}, (7.75, Fraction(1, 3)): {5.5: 0.03225806451612903}, (Fraction(1, 3), 5.5): {Fraction(1, 3): 0.16129032258064516, 5.75: 0.03225806451612903}, (5.5, Fraction(1, 3)): {5.5: 0.12903225806451613, 7.0: 0.03225806451612903}, (Fraction(1, 3), 7.0): {1.25: 0.03225806451612903}, (7.0, 1.25): {1.25: 0.03225806451612903}, (1.25, 1.75): {0.5: 0.03225806451612903}, (1.75, 0.5): {1.25: 0.03225806451612903}, (0.5, 1.25): {1.25: 0.03225806451612903}, (1.25, Fraction(1, 3)): {5.5: 0.03225806451612903}, (5.5, 5.75): {5.75: 0.03225806451612903}}
#
#
#     return rest_phrase_transition
#


def split_hyphens(lyric_line):
    """
    function that takes a line with hyphenated syllables  e.g.      Oh, now eve-ry-bod-y sing, hel-lll-lo -ooo-eek-
    and returns a line of space separated hyphenated syllables e.g. Oh, now eve- -ry- -bod- -y sing, hel- -lll- -lo -ooo- -eek-
    """

    # print('split_hyphens ( lyric_line )', lyric_line)
    syllable_line = ""

    # split into words on space
    syllable_list = lyric_line.split()  # Split string by whitespace
    # print('syllable_list',syllable_list)
    # for each word:
    for w in range(0, len(syllable_list)):
        # remove first and last characters of string
        truncated_w = syllable_list[w][1:]
        truncated_w = truncated_w[:-1]

        # if word has a hyphen:
        if "-" in truncated_w:
            # print('     found - in ', truncated_w)
            # subword list = split on hyphens inserting space
            subwords = syllable_list[w].split("-")
            # print('subword list = split on hyphens',subwords)
            # for each subword 1 .. n
            for sw in range(0, len(subwords)):
                # print('sw',sw)
                if sw == 0:  # append hyphen to subword
                    new_subword = subwords[sw] + "-"
                elif sw == (len(subwords) - 1):  # prepend hyphen to subword
                    new_subword = "-" + subwords[sw]
                else:  # prepend and append hyphen to subword
                    new_subword = "-" + subwords[sw] + "-"
                # output = output + new_subword
                syllable_line = syllable_line + " " + new_subword
        # else:
        else:
            # output = output + word
            syllable_line = syllable_line + " " + syllable_list[w]

    # print('split_hyphens return syllable_line', syllable_line)
    return syllable_line

# v1
# def valid_duration(dur_prev, dur, dur_on_beat=False):
#     """
#     function that takes a duration and
#     returns false if not a valid duration and true otherwise

#     if dur_prev == 0: do not compare with previous duration,
#     if DUR_PREV_DIFF 0  0 # where 0, do not compare with previous duration, 2 is duration is >= 1/2 previous and <= 2 x previous etc

#     if DUR_RATIONAL == False and DUR_TUPLET == False and DUR_LEAST == 0 and DUR_LONGEST == 0 then all durations are valid
#     if DUR_RATIONAL == True and DUR_TUPLET == False and DUR_LEAST == 0 and DUR_LONGEST == 0 then any simple (beat divides into 2) duration is valid
#     if DUR_RATIONAL == False and DUR_TUPLET == True and DUR_LEAST == 0 and DUR_LONGEST == 0 then any complex (beat divides into 3) duration is valid
#     if DUR_RATIONAL == False and DUR_TUPLET == False and DUR_LEAST != 0 and DUR_LONGEST == 0 then any duration >= DUR_LEAST is valid
#     if DUR_RATIONAL == False and DUR_TUPLET == False and DUR_LEAST == 0 and DUR_LONGEST != 0 then any duration <= DUR_LONGEST is valid
#     if DUR_RATIONAL == False and DUR_TUPLET == False and DUR_LEAST != 0 and DUR_LONGEST != 0 then any duration >= DUR_LEAST and <= DUR_LONGEST is valid
#     if DUR_RATIONAL == True and DUR_TUPLET == False and DUR_LEAST != 0 and DUR_LONGEST != 0 then any simple duration >= DUR_LEAST and <= DUR_LONGEST is valid
#     if DUR_RATIONAL == False and DUR_TUPLET == True and DUR_LEAST != 0 and DUR_LONGEST != 0 then any complex duration >= DUR_LEAST and <= DUR_LONGEST is valid

#     if dur is a tuplet and NOT dur_on_beat and dur_prev is not a tuplet then result = False

#     Note: in music21 Float values will be converted to fractions if they are inexpressible exactly as floats:
#     b = duration.Duration()
#     b.quarterLength = 1/3
#     b.quarterLength
#     Fraction(1, 3)

#     """
#     logger.debug(
#         f"valid_duration: dur_prev {dur_prev}, dur {dur}, dur_on_beat {dur_on_beat}, DURATION_SET {DURATION_SET}\t\t start #########################################"
#     )

#     if DUR_LEAST > DUR_LONGEST:
#         print("exit: Error DUR_LEAST > DUR_LONGEST")
#         sys.exit()
#     # duration is valid until proved invalid
#     result = True
#     reason = ""

#     # DUR_PREV_DIFF - compare duration with previous duration, e.g. where 2, duration is >= 1/2 previous and <= 2 x previous etc ,
#     # where 0 and <= 1, do not compare with previous duration.
#     if (
#         (DUR_PREV_DIFF != 0)
#         and (DUR_PREV_DIFF > 1)
#         and (float(Fraction(dur_prev) != 0.0))
#     ):
#         min_dur = float(Fraction(dur_prev)) / float(DUR_PREV_DIFF)
#         max_dur = float(Fraction(dur_prev)) * float(DUR_PREV_DIFF)
#         if (float(Fraction(dur)) < min_dur) or (float(Fraction(dur)) > max_dur):
#             result = False
#             reason = (
#                 "min_dur= ",
#                 str(min_dur)
#                 + " max_dur= "
#                 + str(max_dur)
#                 + "float(Fraction(dur)) < min_dur) or (float(Fraction(dur)) > max_dur)",
#             )
#             # if float(Fraction(dur)) < min_dur:
#             #     print('DUR_PREV_DIFF=', DUR_PREV_DIFF, 'dur_prev=', float(Fraction(dur_prev)),'invalid dur=', float(Fraction(dur)), 'lt min_dur', min_dur)
#             # if float(Fraction(dur)) > max_dur:
#             #     print('DUR_PREV_DIFF=', DUR_PREV_DIFF, 'dur_prev=', float(Fraction(dur_prev)),'invalid dur=', float(Fraction(dur)), 'gt max_dur', max_dur)

#     # simple durations
#     s0_25 = Fraction(0.25)
#     s0_5 = Fraction(0.5)
#     s0_75 = Fraction(0.75)
#     s1_0 = Fraction(1.0)
#     s1_25 = Fraction(1.25)
#     s1_5 = Fraction(1.5)
#     s1_75 = Fraction(1.75)
#     s2_0 = Fraction(2.0)
#     s2_5 = Fraction(2.5)
#     s3_0 = Fraction(3.0)
#     s3_5 = Fraction(3.5)
#     s4_0 = Fraction(4.0)

#     # complex durations
#     c1_6 = Fraction(1, 6)
#     c1_3 = Fraction(1, 3)
#     c2_3 = Fraction(2, 3)
#     c4_3 = Fraction(4, 3)
#     c8_3 = Fraction(8, 3)

#     if DUR_RATIONAL == True:
#         # if not (
#         #     (dur == s0_25)
#         #     or (dur == s0_5)
#         #     or (dur == s1_0)
#         #     or (dur == s1_5)
#         #     or (dur == s2_0)
#         #     or (dur == s4_0)
#         # ):
#         if is_tuplet(dur):
#             result = False
#             reason = "DUR_RATIONAL == True: is_tuplet(dur)"

#     if DUR_TUPLET == True:
#         pass  # any duration is valid, rational or tuplet.
#         # if not (
#         #     (dur == c1_6)
#         #     or (dur == c1_3)
#         #     or (dur == c2_3)
#         #     or (dur == s1_0)
#         #     or (dur == s2_0)
#         #     or (dur == s3_0)

#         # ):
#         #     result = False
#         #     reason = "DUR_TUPLET == True:  not ((dur == c1_6) or (dur == c1_3) or (dur == c2_3) or (dur == s1_0) or (dur == s2_0) or (dur == s3_0)"
#     if DUR_LEAST != 0:  # any duration < DUR_LEAST is invalid
#         if dur < DUR_LEAST:
#             result = False
#             reason = "DUR_LEAST= " + str(DUR_LEAST) + " DUR_LEAST != 0: dur < DUR_LEAST"
#     if DUR_LONGEST != 0:  # any duration > DUR_LONGEST is invalid
#         if dur > DUR_LONGEST:
#             result = False
#             reason = (
#                 "DUR_LONGEST= "
#                 + str(DUR_LONGEST)
#                 + " DUR_LONGEST != 0, dur > DUR_LONGEST"
#             )

#     # print('DUR_RATIONAL, DUR_TUPLET, DUR_LEAST, DUR_LONGEST, DUR_PREV_DIFF, dur_prev, dur, result =', DUR_RATIONAL,
#     #       DUR_TUPLET, DUR_LEAST, DUR_LONGEST, DUR_PREV_DIFF, dur_prev, dur, result)

#     # zero or very small durations not allowed
#     # print('L 1308 if (dur < DURATION_MIN_MUSIC21 ', dur , DURATION_MIN_MUSIC21)
#     if dur < DURATION_MIN_MUSIC21:
#         result = False
#         reason = (
#             "DURATION_MIN_MUSIC21= ",
#             str(DURATION_MIN_MUSIC21) + " dur < DURATION_MIN_MUSIC21",
#         )
#         # print('L 1310 result', result)

#     if DURATION_SET:  # if duration is NOT in duration set then the tone is invalid
#         duration_found = False
#         for dur_from_set in DURATION_SET:
#             if Fraction(dur) == Fraction(dur_from_set):
#                 duration_found = True
#         if not duration_found:
#             result = False
#             reason = (
#                 "DURATION_SET "
#                 + str(DURATION_SET)
#                 + " if DURATION_SET: not duration_found"
#             )

#     # Invalid tuplets

#     # if dur is a tuplet and NOT dur_on_beat and dur_prev is not a tuplet then result = False
#     # if is_tuplet(Fraction(dur)) :
#     # if (dur_on_beat == False) :
#     # if (is_tuplet(Fraction(dur_prev)) == False)  :
#     # if is_tuplet(Fraction(dur)) and (dur_on_beat == False) and (is_tuplet(Fraction(dur_prev)) == False)  :
#     #     print('dur_prev, dur, dur_on_beat', dur_prev, dur, dur_on_beat)
#     #     print('is_tuplet(Fraction(dur)) and (dur_on_beat == False) and (is_tuplet(Fraction(dur_prev))',
#     #           is_tuplet(Fraction(dur)), (dur_on_beat == False), (is_tuplet(Fraction(dur_prev)) ) )

#     # If dur is tuplet:
#     if is_tuplet(Fraction(dur)):
#         # If dur not on beat
#         if dur_on_beat == False:
#             # If prev_dur != dur
#             if Fraction(dur_prev) != Fraction(dur) or (dur_prev == 0):
#                 # Invalid
#                 logger.debug(
#                     f"is_tuplet(Fraction(dur)) and (dur_on_beat == False) and ((Fraction(dur_prev) != Fraction(dur)) or (dur_prev == 0) {is_tuplet(Fraction(dur))} {(dur_on_beat == False)} {(Fraction(dur_prev) != Fraction(dur))} {(dur_prev == 0)}"
#                 )
#                 # print_call_chain()
#                 # input('Press Enter to continue...')
#                 result = False
#                 reason = "is_tuplet(Fraction(dur)) & dur_on_beat == False &  Fraction(dur_prev) != Fraction(dur) or (dur_prev == 0)"

#     logger.debug(
#         f"valid_duration: dur_prev {dur_prev}, dur {dur}, dur_on_beat {dur_on_beat} \t\t return {result} #########################################"
#     )

#     logger.debug(f"valid_duration result reason {reason} ")

#     return result

# # v2 copilot rewrite
# def valid_duration(dur_prev, dur, dur_on_beat=False):
#     """
#     Function that takes a duration and returns False if not a valid duration and True otherwise.

#     Parameters:
#     dur_prev (float): Previous duration.
#     dur (float): Current duration.
#     dur_on_beat (bool): Whether the duration is on beat.

#     Returns:
#     bool: True if the duration is valid, False otherwise.
#     """
#     logger.debug(
#         f"valid_duration: dur_prev {dur_prev}, dur {dur}, dur_on_beat {dur_on_beat}, DURATION_SET {DURATION_SET}\t\t start #########################################"
#     )

#     if DUR_LEAST > DUR_LONGEST:
#         print("exit: Error DUR_LEAST > DUR_LONGEST")
#         sys.exit()

#     result = True
#     reason = ""

#     # Check DUR_PREV_DIFF
#     if DUR_PREV_DIFF != 0 and DUR_PREV_DIFF > 1 and float(Fraction(dur_prev)) != 0.0:
#         min_dur = float(Fraction(dur_prev)) / float(DUR_PREV_DIFF)
#         max_dur = float(Fraction(dur_prev)) * float(DUR_PREV_DIFF)
#         if float(Fraction(dur)) < min_dur or float(Fraction(dur)) > max_dur:
#             result = False
#             reason = f"min_dur= {min_dur}, max_dur= {max_dur}, dur= {dur}"

#     # Simple durations
#     simple_durations = {Fraction(0.25), Fraction(0.5), Fraction(1.0), Fraction(1.5), Fraction(2.0), Fraction(4.0)}

#     # Complex durations
#     complex_durations = {Fraction(1, 6), Fraction(1, 3), Fraction(2, 3), Fraction(4, 3), Fraction(8, 3)}

#     # Check DUR_RATIONAL
#     if DUR_RATIONAL and is_tuplet(dur):
#         result = False
#         reason = "DUR_RATIONAL == True: is_tuplet(dur)"

#     # Check DUR_TUPLET
#     if DUR_TUPLET:
#         pass  # Any duration is valid, rational or tuplet.

#     # Check DUR_LEAST
#     if DUR_LEAST != 0 and dur < DUR_LEAST:
#         result = False
#         reason = f"DUR_LEAST= {DUR_LEAST}, dur < DUR_LEAST"

#     # Check DUR_LONGEST
#     if DUR_LONGEST != 0 and dur > DUR_LONGEST:
#         result = False
#         reason = f"DUR_LONGEST= {DUR_LONGEST}, dur > DUR_LONGEST"

#     # Check minimum duration
#     if dur < DURATION_MIN_MUSIC21:
#         result = False
#         reason = f"DURATION_MIN_MUSIC21= {DURATION_MIN_MUSIC21}, dur < DURATION_MIN_MUSIC21"

#     # Check DURATION_SET
#     if DURATION_SET and Fraction(dur) not in map(Fraction, DURATION_SET):
#         result = False
#         reason = f"DURATION_SET= {DURATION_SET}, dur not in DURATION_SET"

#     # Check tuplets
#     if is_tuplet(Fraction(dur)) and not dur_on_beat and (Fraction(dur_prev) != Fraction(dur) or dur_prev == 0):
#         result = False
#         reason = "is_tuplet(Fraction(dur)) & dur_on_beat == False & Fraction(dur_prev) != Fraction(dur) or dur_prev == 0"

#     logger.debug(f"valid_duration: dur_prev {dur_prev}, dur {dur}, dur_on_beat {dur_on_beat} \t\t return {result}")
#     logger.debug(f"valid_duration result reason {reason}")

#     return result

#v3 rewrite Gemini
def valid_duration(dur_prev, dur, dur_on_beat=False):
    """
    function that takes a duration and
    returns false if not a valid duration and true otherwise

    if dur_prev == 0: do not compare with previous duration,
    if DUR_PREV_DIFF 0  0 # where 0, do not compare with previous duration, 2 is duration is >= 1/2 previous and <= 2 x previous etc

    if DUR_RATIONAL == False and DUR_TUPLET == False and DUR_LEAST == 0 and DUR_LONGEST == 0 then all durations are valid
    if DUR_RATIONAL == True and DUR_TUPLET == False and DUR_LEAST == 0 and DUR_LONGEST == 0 then any simple (beat divides into 2) duration is valid
    if DUR_RATIONAL == False and DUR_TUPLET == True and DUR_LEAST == 0 and DUR_LONGEST == 0 then any complex (beat divides into 3) duration is valid
    if DUR_RATIONAL == False and DUR_TUPLET == False and DUR_LEAST != 0 and DUR_LONGEST == 0 then any duration >= DUR_LEAST is valid
    if DUR_RATIONAL == False and DUR_TUPLET == False and DUR_LEAST == 0 and DUR_LONGEST != 0 then any duration <= DUR_LONGEST is valid
    if DUR_RATIONAL == False and DUR_TUPLET == False and DUR_LEAST != 0 and DUR_LONGEST != 0 then any duration >= DUR_LEAST and <= DUR_LONGEST is valid
    if DUR_RATIONAL == True and DUR_TUPLET == False and DUR_LEAST != 0 and DUR_LONGEST != 0 then any simple duration >= DUR_LEAST and <= DUR_LONGEST is valid
    if DUR_RATIONAL == False and DUR_TUPLET == True and DUR_LEAST != 0 and DUR_LONGEST != 0 then any complex duration >= DUR_LEAST and <= DUR_LONGEST is valid

    if dur is a tuplet and NOT dur_on_beat and dur_prev is not a tuplet then result = False

    """

    global DURATION_SET  # Ensure DURATION_SET is accessed as a global variable
    
    logger.debug(f"valid_duration: dur_prev {dur_prev}, dur {dur}, dur_on_beat {dur_on_beat}, DURATION_SET {DURATION_SET}\t\t start #########################################")      

    if DUR_LEAST > DUR_LONGEST:
        print("exit: Error DUR_LEAST > DUR_LONGEST")
        sys.exit()
    # duration is valid until proved invalid
    result = True
    reason = ""

    # DUR_PREV_DIFF - compare duration with previous duration, e.g. where 2, duration is >= 1/2 previous and <= 2 x previous etc ,
    # where 0 and <= 1, do not compare with previous duration.
    if (
        (DUR_PREV_DIFF != 0)
        and (DUR_PREV_DIFF > 1)
        and (float(Fraction(dur_prev) != 0.0))
    ):
        min_dur = float(Fraction(dur_prev)) / float(DUR_PREV_DIFF)
        max_dur = float(Fraction(dur_prev)) * float(DUR_PREV_DIFF)
        if (float(Fraction(dur)) < min_dur) or (float(Fraction(dur)) > max_dur):
            result = False
            reason = (
                "min_dur= ",
                str(min_dur)
                + " max_dur= "
                + str(max_dur)
                + "float(Fraction(dur)) < min_dur) or (float(Fraction(dur)) > max_dur)",
            )

    # simple durations
    s0_25 = Fraction(0.25)
    s0_5 = Fraction(0.5)
    s0_75 = Fraction(0.75)
    s1_0 = Fraction(1.0)
    s1_25 = Fraction(1.25)
    s1_5 = Fraction(1.5)
    s1_75 = Fraction(1.75)
    s2_0 = Fraction(2.0)
    s2_5 = Fraction(2.5)
    s3_0 = Fraction(3.0)
    s3_5 = Fraction(3.5)
    s4_0 = Fraction(4.0)

    # complex durations
    c1_6 = Fraction(1, 6)
    c1_3 = Fraction(1, 3)
    c2_3 = Fraction(2, 3)
    c4_3 = Fraction(4, 3)
    c8_3 = Fraction(8, 3)

    if DUR_RATIONAL == True:
        if is_tuplet(dur):
            result = False
            reason = "DUR_RATIONAL == True: is_tuplet(dur)"

    if DUR_TUPLET == True:
        pass  # any duration is valid, rational or tuplet.

    if DUR_LEAST != 0:  # any duration < DUR_LEAST is invalid
        if dur < DUR_LEAST:
            result = False
            reason = "DUR_LEAST= " + str(DUR_LEAST) + " DUR_LEAST != 0: dur < DUR_LEAST"
    if DUR_LONGEST != 0:  # any duration > DUR_LONGEST is invalid
        if dur > DUR_LONGEST:
            result = False
            reason = (
                "DUR_LONGEST= "
                + str(DUR_LONGEST)
                + " DUR_LONGEST != 0, dur > DUR_LONGEST"
            )

    # zero or very small durations not allowed
    if dur < DURATION_MIN_MUSIC21:
        result = False
        reason = (
            "DURATION_MIN_MUSIC21= ",
            str(DURATION_MIN_MUSIC21) + " dur < DURATION_MIN_MUSIC21",
        )

    if DURATION_SET:  # if duration is NOT in duration set then the tone is invalid
        duration_found = False
        for dur_from_set in DURATION_SET:
            if Fraction(dur) == Fraction(dur_from_set):
                duration_found = True
                break # Exit the loop once a match is found
        if not duration_found:
            result = False
            reason = (
                "DURATION_SET "
                + str(DURATION_SET)
                + " if DURATION_SET: not duration_found"
            )

    # Invalid tuplets

    # If dur is tuplet:
    if is_tuplet(Fraction(dur)):
        # If dur not on beat
        if dur_on_beat == False:
            # If prev_dur != dur
            if Fraction(dur_prev) != Fraction(dur) or (dur_prev == 0):
                # Invalid
                logger.debug(
                    f"is_tuplet(Fraction(dur)) and (dur_on_beat == False) and ((Fraction(dur_prev) != Fraction(dur)) or (dur_prev == 0) {is_tuplet(Fraction(dur))} {(dur_on_beat == False)} {(Fraction(dur_prev) != Fraction(dur))} {(dur_prev == 0)}"
                )
                result = False
                reason = "is_tuplet(Fraction(dur)) & dur_on_beat == False &  Fraction(dur_prev) != Fraction(dur) or (dur_prev == 0)"

    logger.debug(
        f"valid_duration: dur_prev {dur_prev}, dur {dur}, dur_on_beat {dur_on_beat} \t\t return {result} #########################################"
    )

    logger.debug(f"valid_duration result reason {reason} ")

    return result

def valid_pitch(n_prev, n, tone_scale, tone_mode):
    """
    function that takes a note and
    returns false if not a valid note and true otherwise

    if note is less than TONE_RANGE_BOTTOM or greater than TONE_RANGE_TOP then note is note valid.
    if TONES_ON_KEY == True: # if tone is in scale then tone is valid
    if TONES_OFF_KEY == True: # if tone is not in scale then tone is valid
    if TONE_SCALE_ON_ANHEMITONIC == True: # if tone is in scale [1, 2, 4, 5, 6] then the tone is valid
    if TONE_SCALE_ON_HEMITONIC == True # if tone is in scale = [1, 3, 4, 5, 7] then the tone is valid e.g., c–e–f–g–b–c pentatonic scale with semitones
    # if TONE_SCALE_SET is not empty list then use it to filter tones e.g. TONE_SCALE_SET =  ['A', 'C', 'D', 'D#', 'E', 'G']

    if n_prev == 0: do not compare with previous tone,
    if TONE_PREV_INTERVAL 0  # where 0, do not compare with previous tone,
    if TONE_PREV_INTERVAL > 0 # maximum number of semitones between notes

    """
    result = True

    if TONES_ON_KEY == True and TONES_OFF_KEY == True:
        print("exit: Error TONES_ON_KEY == True and TONES_OFF_KEY == True")
        sys.exit()
    if TONE_SCALE_ON_ANHEMITONIC == True and (
        TONES_ON_KEY == True or TONES_OFF_KEY == True
    ):
        print(
            "exit: Error TONE_SCALE_ON_ANHEMITONIC == True and (TONES_ON_KEY == True or TONES_OFF_KEY == True)"
        )
        sys.exit()
    if TONE_SCALE_ON_ANHEMITONIC == True and TONE_SCALE_ON_HEMITONIC == True:
        print(
            "exit: Error TONE_SCALE_ON_ANHEMITONIC == True and TONE_SCALE_ON_HEMITONIC == True"
        )
        sys.exit()
    if (TONE_SCALE_SET != [] and TONE_SCALE_ON_ANHEMITONIC == True) or (
        TONE_SCALE_SET != [] and TONE_SCALE_ON_HEMITONIC == True
    ):
        print(
            "exit: Error TONE_SCALE_SET not empty list and TONE_SCALE_ON_ANHEMITONIC == True) or (TONE_SCALE_SET not empty list and TONE_SCALE_ON_HEMITONIC == True) "
        )
        sys.exit()

    # if note is less than TONE_RANGE_BOTTOM or greater than TONE_RANGE_TOP then note is note valid.
    min_note = note.Note()
    max_note = note.Note()
    min_note.nameWithOctave = TONE_RANGE_BOTTOM
    max_note.nameWithOctave = TONE_RANGE_TOP
    if note.Note(n.nameWithOctave) < note.Note(min_note.nameWithOctave):
        result = False
    if note.Note(n.nameWithOctave) > note.Note(max_note.nameWithOctave):
        result = False

    # print('tone_scale = ', tone_scale)
    if tone_mode == "major":
        sc = scale.MajorScale(tone_scale)
    else:
        sc = scale.MinorScale(tone_scale)
    scale_degree = sc.getScaleDegreeFromPitch(n)

    if TONES_ON_KEY == True:  # if tone is in scale then tone is valid
        scale_degree = sc.getScaleDegreeFromPitch(n)
        if scale_degree == None:
            result = False

    if TONES_OFF_KEY == True:  # if tone is not in scale then tone is valid
        if scale_degree != None:
            result = False

    if (
        TONE_SCALE_ON_ANHEMITONIC == True
    ):  # if tone is in scale [1, 2, 4, 5, 6] then the tone is valid
        if scale_degree not in TONE_SCALE_ANHEMITONIC:
            result = False
        print(
            "TONE_SCALE_ANHEMITONIC, scale_degree, result =",
            TONE_SCALE_ANHEMITONIC,
            scale_degree,
            result,
        )

    if (
        TONE_SCALE_ON_HEMITONIC == True
    ):  # if tone is in scale = [1, 3, 4, 5, 7] then the tone is valid e.g., c–e–f–g–b–c pentatonic scale with semitones
        if scale_degree not in TONE_SCALE_HEMITONIC:
            result = False
        print(
            "TONE_SCALE_HEMITONIC, scale_degree, result =",
            TONE_SCALE_HEMITONIC,
            scale_degree,
            result,
        )

    # if TONE_SCALE_ON_NEW == True:  # if tone is in scale [2, 3, 4, 6, 7] then the tone is valid
    #     if scale_degree not in TONE_SCALE_NEW:
    #         result = False
    #     print('TONE_SCALE_ON_NEW, scale_degree, result =', TONE_SCALE_NEW, scale_degree, result)

    if TONE_SCALE_SET:  # if tone is NOT in tone scale set then the tone is invalid
        # TBD enharmonic comparison
        # if n.name not in TONE_SCALE_SET:
        scale_tone_found = False
        for scale_tone in TONE_SCALE_SET:
            if pitch.Pitch(n.name).ps == pitch.Pitch(scale_tone).ps:
                scale_tone_found = True
        if not scale_tone_found:
            result = False

    if (
        TONE_PREV_INTERVAL and TONE_PREV_INTERVAL > 0
    ):  # maximum number of semitones between notes
        aInterval = interval.Interval(n_prev, n)
        AIntSemi = abs(aInterval.semitones)
        if AIntSemi > TONE_PREV_INTERVAL:
            result = False
            # print('TONE_PREV_INTERVAL, n_prev, n, aInterval.semitones, AIntSemi, result = ', TONE_PREV_INTERVAL, n_prev, n,
            #       aInterval.semitones, AIntSemi, result)

    # n1 = note.Note('f')
    # n2 = note.Note('e')
    # aInterval = interval.Interval(noteStart=n1, noteEnd=n2)
    # aInterval.semitones
    # -1

    # TONE_ASCENT
    global TONE_ASCENT_TRIGGER
    global TONE_ASCENT_TRIGGERED
    global TONE_ASCENT_COUNT
    global TONE_ASCENT_TRIGGER_COUNT

    if TONE_ASCENT == True and TONE_ASCENT_TRIGGER != None:

        if TONE_ASCENT_TRIGGERED and (n_prev != None):
            aInterval = interval.Interval(noteStart=n_prev, noteEnd=n)
            AIntSemi = abs(aInterval.semitones)

            # valid
            if (int(AIntSemi) >= int(TONE_ASCENT_MIN_INTERVAL)) and n > n_prev:
                TONE_ASCENT_COUNT = TONE_ASCENT_COUNT + 1
                print("TONE_ASCENT_COUNT =", TONE_ASCENT_COUNT)
                print(
                    "TONE_ASCENT valid",
                    AIntSemi,
                    ">= TONE_ASCENT_MIN_INTERVAL",
                    TONE_ASCENT_MIN_INTERVAL,
                    "and tone",
                    n.nameWithOctave,
                    "> n_prev",
                    n_prev.nameWithOctave,
                )
            else:  # invalid
                # print('TONE_ASCENT invalid interval', AIntSemi ,'TONE_ASCENT_MIN_INTERVAL', TONE_ASCENT_MIN_INTERVAL, 'and tone', n.nameWithOctave, ' n_prev', n_prev.nameWithOctave)
                result = False

            if n_prev >= note.Note(TONE_RANGE_MID):
                print(n_prev, ">= TONE_RANGE_MID : TONE_ASCENT CLEARED", TONE_RANGE_MID)
                TONE_ASCENT_COUNT = 0
                TONE_ASCENT_TRIGGERED = False

        lowest_note = note.Note(TONE_ASCENT_TRIGGER)
        if lowest_note >= n and TONE_ASCENT_COUNT == 0:
            TONE_ASCENT_TRIGGER_COUNT = TONE_ASCENT_TRIGGER_COUNT + 1
            print("TONE_ASCENT_TRIGGER_COUNT =", TONE_ASCENT_TRIGGER_COUNT)
            if TONE_ASCENT_TRIGGER_COUNT % TONE_ASCENT_TRIGGER_EVERY_N_TIMES == 0:
                TONE_ASCENT_COUNT = TONE_ASCENT_COUNT + 1
                TONE_ASCENT_TRIGGERED = True
                print("TONE_ASCENT_TRIGGERED, n_prev, n =", n_prev, n)

    # TONE_DESCENT
    global TONE_DESCENT_TRIGGER
    global TONE_DESCENT_TRIGGERED
    global TONE_DESCENT_COUNT
    global TONE_DESCENT_TRIGGER_COUNT

    if TONE_DESCENT == True and TONE_DESCENT_TRIGGER != None:

        if TONE_DESCENT_TRIGGERED and (n_prev != None):
            aInterval = interval.Interval(noteStart=n_prev, noteEnd=n)
            AIntSemi = abs(aInterval.semitones)

            # valid
            if (int(AIntSemi) <= int(TONE_DESCENT_MAX_INTERVAL)) and n < n_prev:
                TONE_DESCENT_COUNT = TONE_DESCENT_COUNT + 1
                # print('TONE_DESCENT_COUNT =', TONE_DESCENT_COUNT)
                # print('TONE_DESCENT valid', AIntSemi ,'<= TONE_DESCENT_MAX_INTERVAL', TONE_DESCENT_MAX_INTERVAL, 'and note', n.nameWithOctave, '< n_prev', n_prev.nameWithOctave)
            else:  # invalid
                # print('TONE_DESCENT invalid interval', AIntSemi ,'TONE_DESCENT_MAX_INTERVAL', TONE_DESCENT_MAX_INTERVAL, 'and note', n.nameWithOctave, ' n_prev', n_prev.nameWithOctave)
                result = False

            if n_prev <= note.Note(TONE_RANGE_MID):
                print(
                    n_prev, "<= TONE_RANGE_MID : TONE_DESCENT CLEARED", TONE_RANGE_MID
                )
                TONE_DESCENT_COUNT = 0
                TONE_DESCENT_TRIGGERED = False
        highest_note = note.Note(TONE_DESCENT_TRIGGER)
        if highest_note <= n and TONE_DESCENT_COUNT == 0:
            TONE_DESCENT_TRIGGER_COUNT = TONE_DESCENT_TRIGGER_COUNT + 1
            print("TONE_DESCENT_TRIGGER_COUNT =", TONE_DESCENT_TRIGGER_COUNT)
            if TONE_DESCENT_TRIGGER_COUNT % TONE_DESCENT_TRIGGER_EVERY_N_TIMES == 0:
                TONE_DESCENT_COUNT = TONE_DESCENT_COUNT + 1
                TONE_DESCENT_TRIGGERED = True
                print("TONE_DESCENT_TRIGGERED, n_prev, n =", n_prev, n)

    return result


def calc_duration_to_end_of_bar(last_note, ts):
    """
    function takes last_note (of a phrase e.g. note on offset 2.0 of duration 1.0)
    and the time signature
    and returns the duration to the end of the bar (e.g. 1.0)
    Note: beat_count = numerator / (denominator / 4)
    """
    logger.debug(
        f"calc_duration_to_end_of_bar: last_note.offset, last_note.duration.quarterLength, ts {last_note.offset} {last_note.duration.quarterLength} {ts}"
    )
    beat_count = ts.numerator / (ts.denominator / 4)
    offset_last_note_end = last_note.offset + last_note.duration.quarterLength
    # print ('offset_last_note_end = n.offset + n.duration.quarterLength', offset_last_note_end, n.offset, n.duration.quarterLength)
    bar_last_note_end = int(math.ceil(offset_last_note_end / beat_count))
    # print('bar_last_note_end       = int(math.ceil(offset_last_note_end / beat_count))', bar_last_note_end, offset_last_note_end, beat_count)
    offset_end_bar = bar_last_note_end * beat_count
    # print('offset_end_bar          = bar_last_note_end * beat_count', offset_end_bar, bar_last_note_end, beat_count )
    duration_to_end_of_bar = offset_end_bar - offset_last_note_end
    logger.debug(
        f"duration_to_end_of_bar  = offset_end_bar - offset_last_note_end {duration_to_end_of_bar} {offset_end_bar} {offset_last_note_end}"
    )
    logger.debug(
        "common.addFloatPrecision(duration_to_end_of_bar) {common.addFloatPrecision(duration_to_end_of_bar)}"
    )
    return duration_to_end_of_bar


def amend_cadence(a_phrase, the_tonic, ts):
    """
    function that takes a phrase of notes,
    amends the cadence,
    and returns the new stream
    """
    # change last note to the_tonic
    # print('amend_cadence: a_phrase[-1].nameWithOctave = ', a_phrase[-1].nameWithOctave)

    print("phrase before amend cadence")
    # a_phrase.show('text')
    show_text_in_stream(a_phrase, ts)

    print("len(a_phrase) = ", len(a_phrase))
    new_phrase = music21.stream.Stream()
    last_index = len(a_phrase.flatten()) - 1

    last_note_cadence = False
    # if last note is note then cadence it
    if type(a_phrase.flatten()[last_index]) == music21.note.Note:
        note_to_cadence = last_index
        last_note_cadence = True
        # else if note before last is a note then cadence it
    elif type(a_phrase.flatten()[last_index - 1]) == music21.note.Note:
        note_to_cadence = last_index - 1
    # else if 2nd note before last is a note then cadence it
    elif type(a_phrase.flatten()[last_index - 2]) == music21.note.Note:
        note_to_cadence = last_index - 2

    for n in range(0, len(a_phrase.flatten())):
        if n < note_to_cadence:
            new_phrase.append(a_phrase.flatten()[n])
        elif n == note_to_cadence:  # create new note with cadence pitch and append
            new_note = music21.note.Note(the_tonic)
            # Ensure the minimum duration of the last note of a cadence
            if a_phrase.flatten()[n].duration.quarterLength >= CADENCE_DUR_MIN:
                new_note.duration.quarterLength = a_phrase.flatten()[
                    n
                ].duration.quarterLength
            else:
                new_note.duration.quarterLength = CADENCE_DUR_MIN
                print(
                    "changed cadence final note duration from x to CADENCE_DUR_MIN:",
                    a_phrase.flatten()[n].duration.quarterLength,
                    CADENCE_DUR_MIN,
                )
            octave = get_tone_octave(a_phrase.flatten()[n - 1], new_note, 1)
            new_note.octave = octave
            # if lyrics then copy too
            if a_phrase.flatten()[n].lyric != None:
                new_note.lyric = a_phrase.flatten()[n].lyric
            new_phrase.append(new_note)
        elif n > note_to_cadence:  # create new note with cadence pitch and append
            # copy rest and amend duration to duration_to_end_of_bar
            r = music21.note.Rest()
            r.duration.quarterLength = calc_duration_to_end_of_bar(
                new_phrase.flatten()[n - 1], ts
            )
            if r.duration.quarterLength != 0.0:
                new_phrase.append(r)

    if last_note_cadence == True:
        rl = music21.note.Rest()
        rl.duration.quarterLength = calc_duration_to_end_of_bar(
            new_phrase.flatten()[n], ts
        )
        if rl.duration.quarterLength != 0.0:
            new_phrase.append(rl)

    print("new cadence text:")
    # new_phrase.show('text')
    show_text_in_stream(new_phrase, ts)

    return new_phrase


def is_last_line(section_line_num, sect, lines_per_section):
    """
    function that takes a section_line_num,
    sect,
    lines_per_section [Intro / Verse / PreChorus / Chorus / Solo / Bridge / Outro] and
    returns true if section_line_num is the last of the sect and false otherwise
    """
    last_line = False
    number_of_lines_in_section = 0
    if sect == Section.INTRO:
        number_of_lines_in_section = lines_per_section[0]
    elif sect == Section.VERSE:
        number_of_lines_in_section = lines_per_section[1]
    elif sect == Section.PRECHORUS:
        number_of_lines_in_section = lines_per_section[2]
    elif sect == Section.CHORUS:
        number_of_lines_in_section = lines_per_section[3]
    elif sect == Section.SOLO:
        number_of_lines_in_section = lines_per_section[4]
    elif sect == Section.BRIDGE:
        number_of_lines_in_section = lines_per_section[5]
    elif sect == Section.OUTRO:
        number_of_lines_in_section = lines_per_section[6]

    if (section_line_num == number_of_lines_in_section) and (
        number_of_lines_in_section != 0
    ):
        last_line = True
    return last_line


def section_line_count_mismatch(sect, lines_per_section, section_line_num):
    """
    takes section name and lines data
    if
    returns true
    """
    logger.debug(
        f"section_line_count_mismatch: sect, lines_per_section, section_line_num: {sect}  {lines_per_section} {section_line_num} "
    )
    mismatch = False

    if sect == Section.INTRO:
        i = 0
    if sect == Section.VERSE:
        i = 1
    if sect == Section.PRECHORUS:
        i = 2
    if sect == Section.CHORUS:
        i = 3
    if sect == Section.SOLO:
        i = 4
    if sect == Section.BRIDGE:
        i = 5
    if sect == Section.OUTRO:
        i = 6

    if (
        section_line_num < lines_per_section[i]
        or section_line_num > lines_per_section[i]
    ):
        logger.warning(
            "Warning:Lyric-First %s has %d lines, but later section repeat has %d lines.",
            sect,
            lines_per_section[i],
            section_line_num,
        )
        mismatch = True
    else:
        # print('section_line_count_matches')
        pass
    return mismatch


def get_lines_per_section(lyrics, section_name_matches):
    """
    function that takes lyrics and
    returns the number of lines per section
    """
    lines_per_section = [0, 0, 0, 0, 0, 0, 0]

    print("get_lines_per_section:")

    first_intro = False
    later_intro = False
    first_verse = False
    later_verse = False
    first_prechorus = False
    later_prechorus = False
    first_chorus = False
    later_chorus = False
    first_solo = False
    later_solo = False
    first_bridge = False
    later_bridge = False
    first_outro = False
    later_outro = False
    section_line_num = 0
    sect = None

    for p in range(0, len(lyrics)):
        # print('                                           ', lyrics[p])
        # if section_name_matches:
        if any(x in lyrics[p].casefold() for x in section_name_matches):
            # print('found a section name')
            section_line_num = 0

            if lyrics[p].casefold().startswith(("intro")):
                sect = Section.INTRO
                if first_intro == False:
                    # print(' found first Intro')
                    first_intro = True
                else:
                    # print(' found later Intro')
                    later_intro = True
            elif lyrics[p].casefold().startswith(("verse")):
                sect = Section.VERSE
                if first_verse == False:
                    # print(' found first Verse')
                    first_verse = True
                else:
                    # print(' found later Verse')
                    later_verse = True
            elif lyrics[p].casefold().startswith("prechorus"):
                sect = Section.PRECHORUS
                if first_prechorus == False:
                    # print(' found first Prechorus')
                    first_prechorus = True
                else:
                    # print(' found later Prechorus')
                    later_prechorus = True
            elif lyrics[p].casefold().startswith(("chorus")):
                sect = Section.CHORUS
                if first_chorus == False:
                    # print(' found first Chorus')
                    first_chorus = True
                else:
                    # print(' found later Chorus')
                    later_chorus = True
            elif lyrics[p].casefold().startswith(("solo")):
                sect = Section.SOLO
                if first_solo == False:
                    # print(' found first Solo')
                    first_solo = True
                else:
                    # print(' found later Solo')
                    later_solo = True
            elif lyrics[p].casefold().startswith(("bridge")):
                sect = Section.BRIDGE
                if first_bridge == False:
                    # print(' found first Bridge')
                    first_bridge = True
                else:
                    # print(' found later Bridge')
                    later_bridge = True
            elif lyrics[p].casefold().startswith(("outro")):
                sect = Section.OUTRO
                if first_outro == False:
                    # print(' found first Outro')
                    first_outro = True
                else:
                    # print(' found later Outro')
                    later_outro = True
        elif lyrics[p] != "" and (
            (sect == Section.INTRO and not later_intro)
            or (sect == Section.VERSE and not later_verse)
            or (sect == Section.PRECHORUS and not later_prechorus)
            or (sect == Section.CHORUS and not later_chorus)
            or (sect == Section.SOLO and not later_solo)
            or (sect == Section.BRIDGE and not later_bridge)
            or (sect == Section.OUTRO and not later_outro)
        ):
            # print('found first section line')
            section_line_num = section_line_num + 1
            # print('section_line_num', section_line_num)

            if sect == Section.INTRO:
                lines_per_section[0] = lines_per_section[0] + 1
            if sect == Section.VERSE:
                lines_per_section[1] = lines_per_section[1] + 1
            if sect == Section.PRECHORUS:
                lines_per_section[2] = lines_per_section[2] + 1
            if sect == Section.CHORUS:
                lines_per_section[3] = lines_per_section[3] + 1
            if sect == Section.SOLO:
                lines_per_section[4] = lines_per_section[4] + 1
            if sect == Section.BRIDGE:
                lines_per_section[5] = lines_per_section[5] + 1
            if sect == Section.OUTRO:
                lines_per_section[6] = lines_per_section[6] + 1

    return lines_per_section


def save_text_of_note(n, ts, f, num_notes, num_rests):
    """
    takes a note and the beats to the bar
    and print the text to file f

    Note: I tried adding n.sites.getSiteCount(), but it wasn't very useful e.g. first stream all notes and rests had sites 2,
    later on a copy of the stream all notes and rests had sites 8
    """
    beat_count = ts.numerator / (ts.denominator / 4)
    # print('beat_count = ts.numerator / (ts.denominator / 4)', beat_count, ts.numerator, ts.denominator)

    offset_end = n.offset + n.duration.quarterLength
    # calculate offset_bar_end = beat_count * ( truncated (n.offset / beat_count) + 1)
    truncated_bar = int("%.0f" % (n.offset / beat_count))
    offset_bar_end = beat_count * (truncated_bar + 1)
    # print('offset_bar_end = beat_count * (truncated_bar + 1)', offset_bar_end, beat_count, truncated_bar)
    if offset_end > offset_bar_end:
        # print('WARNING next duration: \t\t\t\t  offset_end', offset_end, '>', 'offset_bar_end', offset_bar_end,'- Replace with tied note or rest to end of bar and rest at beginning of next bar.')
        pass
    # print("Note: %s%d %0.1f" % (n.pitch.name, n.pitch.octave, n.duration.quarterLength))

    if type(n) == music21.note.Note:
        try:
            print(
                "offset %.4f" % n.offset,
                "\t bar %.4f" % ((n.offset / beat_count) + 1),
                "\t o \t",
                n.offset,
                "\t\t + ql",
                n.duration.quarterLength,
                "\t = o_end %.4f" % offset_end,
                "\t note qLen lyric:\t",
                n.nameWithOctave,
                "\t",
                n.duration.quarterLength,
                "\t",
                n.lyric,
                n.duration.tuplets,
                "type",
                n.duration.tuplets[0].type,
                "tie",
                n.tie,
                file=f,
            )
        except IndexError:
            print(
                "offset %.4f" % n.offset,
                "\t bar %.4f" % ((n.offset / beat_count) + 1),
                "\t o \t",
                n.offset,
                "\t\t + ql",
                n.duration.quarterLength,
                "\t = o_end %.4f" % offset_end,
                "\t note qLen lyric:\t",
                n.nameWithOctave,
                "\t",
                n.duration.quarterLength,
                "\t",
                n.lyric,
                n.duration.tuplets,
                "tie",
                n.tie,
                file=f,
            )
        try:
            print("nested tuplets[1].type", n.duration.tuplets[1].type, file=f)
        except IndexError:
            pass

        num_notes = num_notes + 1

    if type(n) == music21.note.Rest:
        # print('offset_float %.4f' % n.offset, 'bar %.4f'% (n.offset / beat_count), 'rest quarterLength, offset_fraction, offset_end:', n.duration.quarterLength, n.offset, '%.4f' %offset_end )
        # print('offset %.4f' % n.offset, '\t bar %.4f' % ((n.offset / beat_count)+1), '\t o \t', n.offset, '\t\t + ql',
        #       n.duration.quarterLength, '\t = o_end %.4f' % offset_end, '\t rest quarterLength:', n.duration.quarterLength, n.duration.tuplets, file=f)
        try:
            print(
                "offset %.4f" % n.offset,
                "\t bar %.4f" % ((n.offset / beat_count) + 1),
                "\t o \t",
                n.offset,
                "\t\t + ql",
                n.duration.quarterLength,
                "\t = o_end %.4f" % offset_end,
                "\t rest quarterLength:",
                n.duration.quarterLength,
                n.duration.tuplets,
                "type",
                n.duration.tuplets[0].type,
                "tie",
                n.tie,
                file=f,
            )
        except IndexError:
            print(
                "offset %.4f" % n.offset,
                "\t bar %.4f" % ((n.offset / beat_count) + 1),
                "\t o \t",
                n.offset,
                "\t\t + ql",
                n.duration.quarterLength,
                "\t = o_end %.4f" % offset_end,
                "\t rest quarterLength:",
                n.duration.quarterLength,
                n.duration.tuplets,
                "tie",
                n.tie,
                file=f,
            )
        try:
            print("nested rest tuplets[1].type", n.duration.tuplets[1].type, file=f)
        except IndexError:
            pass

        num_rests = num_rests + 1

    return num_notes, num_rests


def show_to_file(the_stream, the_file):
    """
    takes a stream and print it to a file
    """
    from contextlib import redirect_stdout

    with open(the_file, "w") as f:
        with redirect_stdout(f):
            the_stream.show("text", addEndTimes=True)
    # print('this is goes back to stdout')


# def save_text_in_stream(song, ts, filename):
#     """
#     given a song stream, ts time signature,
#     write a text version of the song to the filename
#     """
#     with open(filename, "w") as f:

#         # print('show_text_in_stream ------------------------------------------------- stream.id = decimal, hex', song.id, hex(song.id))
#         print(
#             "show_text_in_stream ------------------------------------------------- stream.id f'{song}",
#             song.id,
#             file=f,
#         )

#         # song.show('text')

#         # if not song.isWellFormedNotation():
#         #     print("show_text_in_stream WARNING f'{song} is not well-formed; see isWellFormedNotation()")

#         offset_end = 0.0
#         num_notes = 0
#         num_rests = 0
#         # for n in song.flatten().notes:
#         for n in song.flatten():
#             # print('type(n) ', type(n) )
#             if type(n) == music21.clef.TrebleClef:
#                 print("music21.clef.TrebleClef", file=f)

#             if type(n) == music21.expressions.TextExpression:
#                 # print('music21.expressions.TextExpression')
#                 print("TextExpression =", n.content, file=f)

#             if type(n) == music21.key.KeySignature:
#                 # print('music21.key.KeySignature', song.tonic.name, song.mode)
#                 print("music21.key.KeySignature", song.keySignature, file=f)  # None
#                 first = True
#                 for sKS in song.flatten().getElementsByClass("KeySignature"):
#                     if first:
#                         songKeySignature = sKS
#                         print(
#                             "First KeySignature:", songKeySignature, file=f
#                         )  # e.g. <music21.key.KeySignature of 1 flat>
#                         print(".sharps:", songKeySignature.sharps, file=f)  # e.g. -1
#                         print(
#                             ".getScale(major):",
#                             songKeySignature.getScale("major"),
#                             file=f,
#                         )  # e.g. <music21.scale.MajorScale F major>
#                         first = False
#                     else:
#                         print("other KeySignature:", sKS, file=f)

#             if type(n) == music21.metadata.Metadata:
#                 # Metadata represent data for a work or fragment, including
#                 # title, composer, dates, and other relevant information.
#                 print("music21.metadata.Metadata", file=f)
#                 print("all =", song.metadata.all(), file=f)
#                 # print('title =', song.metadata.title) # crash if none
#                 # print('composer =', song.metadata.composer)
#                 # print('date = ', song.metadata.date)
#                 # print('lyricist = ', song.metadata.lyricist)

#             if type(n) == music21.meter.TimeSignature:
#                 # get the timesignatures
#                 first = True
#                 for (
#                     tSig
#                 ) in (
#                     song.getTimeSignatures()
#                 ):  # may not be required, .cf song_section_values missed n=3/4 as tsig=4/4 on God_Save_The_Queen.mxl
#                     if first:
#                         songTimeSig = tSig
#                         print(
#                             "First Time Signature:", songTimeSig, file=f
#                         )  # eg First Time Signature: <music21.meter.TimeSignature 4/4>
#                         first = False
#                     else:
#                         print("Other Time Signature:", tSig, file=f)

#             if type(n) == music21.note.Note or type(n) == music21.note.Rest:
#                 # print('TBD show_text_of_note', file=f)
#                 num_notes, num_rests = save_text_of_note(n, ts, f, num_notes, num_rests)

#             if type(n) == music21.tempo.MetronomeMark:
#                 print("music21.tempo.MetronomeMark", n.number, file=f)

#         min_note, max_note = calc_the_note_range(song)
#         print("min_note, max_note", min_note, max_note, file=f)
#         print("num_notes, num_rests", num_notes, num_rests, file=f)


def show_histograms(score, label):
    """
    function that shows histograms of the score with the supplied label
    """

    # show a histogram of output pitch space.
    p = graph.plot.HistogramPitchSpace(score)
    p.title = label + " - histogram"
    p.run()  # with defaults and proper configuration, will open graph

    # show a histogram of pitch class
    p = graph.plot.HistogramPitchClass(score)
    # p.title = label + ' - histogram-pitchClass-count'
    p.title = label + " - histogram"
    p.run()  # with defaults and proper configuration, will open graph

    # show a histogram of quarter lengths
    p = graph.plot.HistogramQuarterLength(score)
    p.title = label + " - histogram"
    p.run()  # with defaults and proper configuration, will open graph

    # show a A graph of events, sorted by pitch space, over time
    p = graph.plot.HorizontalBarPitchSpaceOffset(score)
    p.title = label + " - graph"
    p.run()  # with defaults and proper configuration, will open graph


def set_cadence_duration_transition(song):
    """
    function that takes a song and
    returns the markov cadence duration transition
    (not including the non-cadence durations - the notes leading up to the last notes of the phrases).
    """
    # print(' ')
    print("set_cadence_duration_transition")
    cdtransition = {}

    prev = None
    last = None
    cdtotal = 0
    bad_duration = False
    number_of_rests = 0
    number_of_notes = 0
    number_of_elements = len(song.flatten())
    element_num = 0
    # Gather the duration transitions
    # for n in song.flatten().notes:
    for n in song.flatten():
        if type(n) == music21.note.Rest:
            number_of_rests = number_of_rests + 1
        if type(n) == music21.note.Note:
            number_of_notes = number_of_notes + 1
            if prev:
                if last:
                    if not is_cadence(element_num, song.flatten()):
                        bad_duration = True
                        # print('Skipping non cadence duration. prev last current:', prev.duration.quarterLength, last.duration.quarterLength, n.duration.quarterLength)
                    else:  #
                        # cdkey = (prev.duration.quarterLength, last.duration.quarterLength)
                        cdkey = (
                            str(prev.duration.quarterLength),
                            str(last.duration.quarterLength),
                        )

                        # print(dkey) # e.g. (0.25, Fraction(1, 3))
                        # in python how to find if a key contains a Fraction with a particular number ?
                        # print(x - int(x) == 0)  # True if x is a whole number, False if it has decimals.
                        if cdkey in cdtransition:
                            # if n.duration.quarterLength in cdtransition[cdkey]:
                            if str(n.duration.quarterLength) in cdtransition[cdkey]:
                                cdtransition[cdkey][n.duration.quarterLength] += 1
                            else:
                                cdtransition[cdkey][n.duration.quarterLength] = 1
                                # print('Using cadence duration. prev last current:', prev.duration.quarterLength,
                                #       last.duration.quarterLength, n.duration.quarterLength)
                        else:
                            cdtransition[cdkey] = {n.duration.quarterLength: 1}
                            # print('Using cadence duration. prev last current:', prev.duration.quarterLength,
                            #       last.duration.quarterLength, n.duration.quarterLength)
                    prev = last
                    if bad_duration == False:
                        cdtotal += 1
                    bad_duration = False
                last = n
            else:
                prev = n
        element_num = element_num + 1

    # print(' ')
    print(
        "input music: number_of_rests = ",
        number_of_rests,
        " number_of_notes = ",
        number_of_notes,
        "number_of_elements =",
        number_of_elements,
    )
    print("cadence duration transitions with frequency", cdtransition)

    cdtransition, cdtotal = apply_duration_eq_to_dtransition_frequency(
        cdtransition, cdtotal, True
    )

    print("After apply_duration_eq_to_dtransition_frequency for cadence True")
    print("cadence duration transition with frequency=", cdtransition)
    print("cdtotal_frequency=", cdtotal)

    # Compute the probability for each cdtransition
    cdtransition_cdtotal_probability = 0.0
    for k, v in cdtransition.items():
        for i, j in v.items():
            cdtransition[k][i] = j / cdtotal
            cdtransition_cdtotal_probability = (
                cdtransition_cdtotal_probability + cdtransition[k][i]
            )
    print("cdtransition_cdtotal_probability = ", cdtransition_cdtotal_probability)
    # print('cdtotal durations = ',cdtotal)
    # print(' ')
    print("cadence duration transitions with probability", cdtransition)

    # Compute the probability for each transition -----------------------------------------------------------
    ptotal = 0
    for k, v in cdtransition.items():
        for i, j in v.items():
            cdtransition[k][i] = j / cdtotal
            ptotal = ptotal + cdtransition[k][i]

    print("cadence duration total Notes = ", cdtotal)  # eg 10
    # print('ptotal duration = ',ptotal) # e.g. 0.99
    # print(' ')
    print("cadence duration transitions with probability", cdtransition)
    # print(' ')

    # No default cadence usually required,
    # as all input music (with at least 3 notes) should have a final note.

    return cdtransition


def append_rest_note_transition(rest_note_transition, a_song):
    """
    Given a rest_note_transition and a_song stream
    calculate the rest_note_transition frequencies and append to and
    return the rest_note_transition
    """

    songTimeSig = a_song.recurse().getElementsByClass(meter.TimeSignature)[0]
    ts1 = songTimeSig
    # print('append_rest_note_transition(rest_note_transition, a_song), beat_count',rest_note_transition, a_song)
    rn_key = ("0.0", "0.0")
    measure_ends_on_rest = False
    no_rests_found_in_song = True

    for p in a_song.parts:

        # foreach measure
        for i, m in enumerate(p.getElementsByClass("Measure")):
            # print('part', p,'measure', m,'measureIndex', i )
            ##            show_text_in_stream(m, ts1)
            rest_found = False
            prev_measure_ended_on_rest = measure_ends_on_rest
            first_el_a_note = False

            # foreach element
            for count_el, el in enumerate(m.flatten()):
                #     if element = rest:
                if type(el) == music21.note.Rest:
                    rest_found = True
                    no_rests_found_in_song = False
                    measure_ends_on_rest = True
                if type(el) == music21.note.Note:
                    measure_ends_on_rest = False
                    if rest_found == True:
                        # print('rest_found and following_note_found_in_same_bar: update_rest_note_transition count_el el.nameWithOctave, el.offset ',count_el, el.nameWithOctave, el.offset)
                        update_transition(rest_note_transition, rn_key, el.offset)
                        rest_found = False
                    if el.offset == 0.0:
                        first_el_a_note = True
                if prev_measure_ended_on_rest and first_el_a_note:
                    # print('prev_measure_ended_on_rest and first_el_a_note: update_rest_note_transition count_el el.nameWithOctave, el.offset ', count_el, el.nameWithOctave, el.offset)
                    update_transition(rest_note_transition, rn_key, el.offset)
                    first_el_a_note = False

    if no_rests_found_in_song or rest_note_transition == {}:
        update_transition(rest_note_transition, rn_key, 0.0)

    return rest_note_transition


def validate_later_lines_per_section(lyrics, section_name_matches, lines_per_section):
    """
    given the lyrics, section_name_matches, lines_per_section
    check each section lines matches lines per section
    exit if not
    """
    lines_per_section_repeat = [0, 0, 0, 0, 0, 0, 0]

    print("validate_later_lines_per_section: lines_per_section", lines_per_section)

    first_intro = False
    later_intro = False
    first_verse = False
    later_verse = False
    first_prechorus = False
    later_prechorus = False
    first_chorus = False
    later_chorus = False
    first_solo = False
    later_solo = False
    first_bridge = False
    later_bridge = False
    first_outro = False
    later_outro = False
    section_line_num = 0
    previous_section_line_num = 0
    sect = None
    wrong_number_of_lines_in_section = False
    too_many_lines_in_section_repeat = False
    later_section_lines_counted = False

    for p in range(0, len(lyrics)):
        # print('                                           ', lyrics[p])
        # if section_name_matches:
        if any(x in lyrics[p].casefold() for x in _section_name_matches):
            # print('found a section name')
            previous_section_line_num = section_line_num
            section_line_num = 0
            previous_sect = sect
            if previous_sect != None:
                logger.debug(
                    f"previous_sect={previous_sect} previous_section_line_num {previous_section_line_num}"
                )
                if section_line_count_mismatch(
                    previous_sect, lines_per_section, previous_section_line_num
                ):
                    wrong_number_of_lines_in_section = True

            if lyrics[p].casefold().startswith(("intro")):
                sect = Section.INTRO
                if first_intro == False:
                    # print(' found first Intro')
                    first_intro = True
                else:
                    # print(' found later Intro')
                    later_intro = True
                    lines_per_section_repeat[0] = 0
            elif lyrics[p].casefold().startswith(("verse")):
                sect = Section.VERSE
                if first_verse == False:
                    # print(' found first Verse')
                    first_verse = True
                else:
                    # print(' found later Verse')
                    later_verse = True
                    lines_per_section_repeat[1] = 0
            elif lyrics[p].casefold().startswith("prechorus"):
                sect = Section.PRECHORUS
                if first_prechorus == False:
                    # print(' found first Prechorus')
                    first_prechorus = True
                else:
                    # print(' found later Prechorus')
                    later_prechorus = True
                    lines_per_section_repeat[2] = 0
            elif lyrics[p].casefold().startswith(("chorus")):
                sect = Section.CHORUS
                if first_chorus == False:
                    # print(' found first Chorus')
                    first_chorus = True
                else:
                    # print(' found later Chorus')
                    later_chorus = True
                    lines_per_section_repeat[3] = 0
            elif lyrics[p].casefold().startswith(("solo")):
                sect = Section.SOLO
                if first_solo == False:
                    # print(' found first Solo')
                    first_solo = True
                else:
                    # print(' found later Solo')
                    later_solo = True
                    lines_per_section_repeat[4] = 0
            elif lyrics[p].casefold().startswith(("bridge")):
                sect = Section.BRIDGE
                if first_bridge == False:
                    # print(' found first Bridge')
                    first_bridge = True
                else:
                    # print(' found later Bridge')
                    later_bridge = True
                    lines_per_section_repeat[5] = 0
            elif lyrics[p].casefold().startswith(("outro")):
                sect = Section.OUTRO
                if first_outro == False:
                    # print(' found first Outro')
                    first_outro = True
                else:
                    # print(' found later Outro')
                    later_outro = True
                    lines_per_section_repeat[6] = 0
        elif lyrics[p] != "" and (
            (sect == Section.INTRO and not later_intro)
            or (sect == Section.VERSE and not later_verse)
            or (sect == Section.PRECHORUS and not later_prechorus)
            or (sect == Section.CHORUS and not later_chorus)
            or (sect == Section.SOLO and not later_solo)
            or (sect == Section.BRIDGE and not later_bridge)
            or (sect == Section.OUTRO and not later_outro)
        ):
            # print('found first section line')
            section_line_num = section_line_num + 1
            # print('section_line_num', section_line_num)

        elif lyrics[p] != "" and (
            (sect == Section.INTRO and later_intro)
            or (sect == Section.VERSE and later_verse)
            or (sect == Section.PRECHORUS and later_prechorus)
            or (sect == Section.CHORUS and later_chorus)
            or (sect == Section.SOLO and later_solo)
            or (sect == Section.BRIDGE and later_bridge)
            or (sect == Section.OUTRO and later_outro)
        ):
            # print('found later section line')
            section_line_num = section_line_num + 1
            # print('section_line_num', section_line_num)
            if sect == Section.INTRO:
                i = 0
            if sect == Section.VERSE:
                i = 1
            if sect == Section.PRECHORUS:
                i = 2
            if sect == Section.CHORUS:
                i = 3
            if sect == Section.SOLO:
                i = 4
            if sect == Section.BRIDGE:
                i = 5
            if sect == Section.OUTRO:
                i = 6
            lines_per_section_repeat[i] = lines_per_section_repeat[i] + 1
            if lines_per_section_repeat[i] > lines_per_section[i]:
                logger.warning(
                    "Warning:Lyric-First %s has %d lines, but later section repeat has at least %d lines.",
                    sect,
                    lines_per_section[i],
                    lines_per_section_repeat[0],
                )
                too_many_lines_in_section_repeat = True
        elif lyrics[p] == "":
            pass
            # print('found blank line')
        # print('sect', sect)

    if too_many_lines_in_section_repeat:
        print("exit: Error too_many_lines_in_section_repeat. See Warning(s).")
        sys.exit()

    if wrong_number_of_lines_in_section:
        print("exit: Error wrong_number_of_lines_in_section. See Warning(s).")
        sys.exit()

    return


def get_section_values(sect):
    """
    for the given section
    load the key values relevant to the new section
    into the section global variables
    """
    global BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED
    global BEAT_PLACEMENTS_DENIED_SET
    global BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET
    global DURATION_SET
    global DUR_LEAST
    global DUR_LONGEST
    global DUR_PREV_DIFF
    global DUR_RATIONAL
    global DUR_TUPLET
    global REST_NOTE_LINE_OFFSET
    global TONES_ON_KEY
    global TONE_PREV_INTERVAL
    global TONE_RANGE_BOTTOM
    global TONE_RANGE_TOP
    global TONE_SCALE_SET

    DURATION_SET = PER_SECTION_DURATION_SET[sect.value]
    DUR_LEAST = PER_SECTION_DUR_LEAST[sect.value]
    DUR_LONGEST = PER_SECTION_DUR_LONGEST[sect.value]
    DUR_PREV_DIFF = PER_SECTION_DUR_PREV_DIFF[sect.value]
    DUR_RATIONAL = PER_SECTION_DUR_RATIONAL[sect.value]
    DUR_TUPLET = PER_SECTION_DUR_TUPLET[sect.value]
    REST_NOTE_LINE_OFFSET = PER_SECTION_REST_NOTE_LINE_OFFSET[sect.value]
    TONES_ON_KEY = PER_SECTION_TONES_ON_KEY[sect.value]
    TONE_PREV_INTERVAL = PER_SECTION_TONE_PREV_INTERVAL[sect.value]
    TONE_RANGE_BOTTOM = PER_SECTION_TONE_RANGE_BOTTOM[sect.value]
    TONE_RANGE_TOP = PER_SECTION_TONE_RANGE_TOP[sect.value]
    TONE_SCALE_SET = PER_SECTION_TONE_SCALE_SET[sect.value]

    return


# reverse function from https://github.com/cuthbertLab/music21-tools/blob/bb2d78b6ad18d68ac77418b41fd995f74de6afb4/trecento/quodJactatur.py#L267
def reverse(
    self,
    *,
    inPlace=False,
    classesToMove=(
        key.KeySignature,
        meter.TimeSignature,
        clef.Clef,
        metadata.Metadata,
        instrument.Instrument,
        layout.SystemLayout,
    ),
    makeNotation=False,
):
    """
    reverse the order of stream members
    """
    highestTime = self.highestTime

    if inPlace is True:
        returnObj = self
        raise Exception("Whoops haven't written inPlace=True yet for reverse")
    else:
        returnObj = stream.Part()

    sf = self.flatten()
    for myEl in sf:
        if isinstance(myEl, classesToMove):
            continue

        if myEl.duration is not None:
            releaseTime = myEl.getOffsetBySite(sf) + myEl.duration.quarterLength
        else:
            releaseTime = myEl.getOffsetBySite(sf)
        newOffset = highestTime - releaseTime

        returnObj.insert(newOffset, myEl)

    for thisP in returnObj.flatten().pitches:
        if thisP.accidental is not None:
            thisP.accidental.displayStatus = None

    if makeNotation is True:
        return returnObj.makeNotation()
    else:
        return returnObj


def has_tuplet(the_stream):
    """
    if the stream has a tuplet return True
    """
    has_tuplet = False

    sf = the_stream.flatten()

    for myEl in sf:
        if type(myEl) == music21.note.Note or type(myEl) == music21.note.Rest:
            try:
                if myEl.duration.tuplets != ():
                    has_tuplet = True
            except IndexError:
                pass

    return has_tuplet


def filter_output_stream_for_MuseScore(
    a_stream,
    ts,
    *,
    classesToMove=(
        note.Note,
        note.Rest,
        expressions.TextExpression,
        tempo.MetronomeMark,
        key.KeySignature,
        meter.TimeSignature,
        clef.TrebleClef,
        metadata.Metadata,
        instrument.Instrument,
        layout.SystemLayout,
    ),
    makeNotation=False,
):
    """
    filter a stream for MuseScore 3.6.2
    the elements are filtered in the current stream.
    if inPlace is False then a new stream is returned.

    all elements of class classesToMove get moved.
    This puts the clefs, TimeSignatures, etc. in their proper locations.
    """

    returnObj = stream.Part()

    # strip ties, flatten, make measures, make ties
    stripped = a_stream.stripTies().flatten()
    # out1 = stripped.makeVoices()
    out2 = stripped.makeNotation()
    returnObj = out2.makeTies()

    return returnObj


def process_lyrics(
    INPUT_LYRICS_FULLY_QUALIFIED,
    _section_name_matches,
    p0,
    ts,
    song_key,
    transition,
    bpm_transition,
    dtransition,
    cad_transition,
    cad_dtransition,
    rest_note_transition,
    gmpwl_call_count,
    score,
    mxl_files,
    style,
):

    global TIME_SIG_WANTED
    logger.debug(f"")
    logger.debug(f"process_lyrics Duration set: {DURATION_SET} (type: {type(DURATION_SET)})")
    logger.debug(f"process_lyrics Duration set (PER_SECTION): {PER_SECTION_DURATION_SET}") 
   

    print("process_lyrics USE_STYLES", USE_STYLES, "Current style", style)
    # input("Press Enter to continue...")

    print("INPUT_LYRICS_FULLY_QUALIFIED", INPUT_LYRICS_FULLY_QUALIFIED)
    lyrics, call_attributes_list = get_lyrics(INPUT_LYRICS_FULLY_QUALIFIED)

    lines_per_section = get_lines_per_section(lyrics, _section_name_matches)
    print(
        "lines_per_section [intro, verse, prechorus, chorus, solo, bridge, outro]",
        lines_per_section,
    )
    validate_later_lines_per_section(lyrics, _section_name_matches, lines_per_section)

    first_intro = False
    later_intro = False
    first_verse = False
    later_verse = False
    first_prechorus = False
    later_prechorus = False
    first_chorus = False
    later_chorus = False
    first_solo = False
    later_solo = False
    first_bridge = False
    later_bridge = False
    first_outro = False
    later_outro = False

    section_line_num = 0
    sect = None  # Initialize sect to avoid UnboundLocalError


    for p in range(0, len(lyrics)):
        print("                                           ", lyrics[p])
        if any(x in lyrics[p].casefold() for x in _section_name_matches):
            section_name_text = lyrics[p]
            section_line_num = 0

            te = expressions.TextExpression(lyrics[p].upper())
            te.placement = "above"
            p0.append(te)

            if lyrics[p].casefold().startswith(("intro")):
                sect = Section.INTRO
                if first_intro == False:
                    print(" found first Intro")
                    first_intro = True
                else:
                    print(" found later Intro")
                    later_intro = True
            elif lyrics[p].casefold().startswith(("verse")):
                sect = Section.VERSE
                if first_verse == False:
                    print(" found first Verse")
                    first_verse = True
                else:
                    print(" found later Verse")
                    later_verse = True
            elif lyrics[p].casefold().startswith("prechorus"):
                sect = Section.PRECHORUS
                if first_prechorus == False:
                    print(" found first Prechorus")
                    first_prechorus = True
                else:
                    print(" found later Prechorus")
                    later_prechorus = True
            elif lyrics[p].casefold().startswith(("chorus")):
                sect = Section.CHORUS
                if first_chorus == False:
                    print(" found first Chorus")
                    first_chorus = True
                else:
                    print(" found later Chorus")
                    later_chorus = True
            elif lyrics[p].casefold().startswith(("solo")):
                sect = Section.SOLO
                if first_solo == False:
                    print(" found first Solo")
                    first_solo = True
                else:
                    print(" found later Solo")
                    later_solo = True
            elif lyrics[p].casefold().startswith(("bridge")):
                sect = Section.BRIDGE
                if first_bridge == False:
                    print(" found first Bridge")
                    first_bridge = True
                else:
                    print(" found later Bridge")
                    later_bridge = True
            elif lyrics[p].casefold().startswith(("outro")):
                sect = Section.OUTRO
                if first_outro == False:
                    print(" found first Outro")
                    first_outro = True
                else:
                    print(" found later Outro")
                    later_outro = True
            get_section_values(sect)
        elif lyrics[p] != "" and (
            (sect == Section.INTRO and not later_intro)
            or (sect == Section.VERSE and not later_verse)
            or (sect == Section.PRECHORUS and not later_prechorus)
            or (sect == Section.CHORUS and not later_chorus)
            or (sect == Section.SOLO and not later_solo)
            or (sect == Section.BRIDGE and not later_bridge)
            or (sect == Section.OUTRO and not later_outro)
        ):
            print("found first section line")
            section_line_num = section_line_num + 1
            print("section_line_num", section_line_num)
            print("input lyrics line num (p)", p)
            print("lyrics[p]", lyrics[p])
            print("call_attributes_list[p]", call_attributes_list[p])
            if call_attributes_list[p] != None:
                for k, v in call_attributes_list[p].items():
                    if (
                        k == "copy"
                        or k == "transpose"
                        or k == "invert"
                        or k == "reverse"
                    ):
                        print(
                            "a_phrase = copy_phrase_with_lyrics from",
                            v[0].casefold(),
                            "line",
                            int(v[1]),
                        )
                        try:
                            if v[0].casefold() == "intro":
                                new_section_stream = copy.deepcopy(
                                    intro_line_stream_list[int(v[1]) - 1]
                                )
                            if v[0].casefold() == "verse":
                                new_section_stream = copy.deepcopy(
                                    verse_line_stream_list[int(v[1]) - 1]
                                )
                            if v[0].casefold() == "prechorus":
                                new_section_stream = copy.deepcopy(
                                    prechorus_line_stream_list[int(v[1]) - 1]
                                )
                            if v[0].casefold() == "chorus":
                                new_section_stream = copy.deepcopy(
                                    chorus_line_stream_list[int(v[1]) - 1]
                                )
                            if v[0].casefold() == "solo":
                                new_section_stream = copy.deepcopy(
                                    solo_line_stream_list[int(v[1]) - 1]
                                )
                            if v[0].casefold() == "outro":
                                new_section_stream = copy.deepcopy(
                                    outro_line_stream_list[int(v[1]) - 1]
                                )
                            if v[0].casefold() == "bridge":
                                new_section_stream = copy.deepcopy(
                                    bridge_line_stream_list[int(v[1]) - 1]
                                )
                        except BaseException as err:
                            print(f"Unexpected {err=}, {type(err)=}")
                            print(
                                "exit: invalid post processing function:",
                                call_attributes_list[p],
                            )
                            sys.exit()
                        a_phrase = add_new_lyrics_to_old_phrase(
                            sect,
                            section_name_text,
                            section_line_num,
                            lyrics[p],
                            new_section_stream,
                        )
                    if k == "transpose":
                        print("a_phrase = transpose_phrase_with_lyrics")
                        transpose_phrase = add_new_lyrics_to_old_phrase(
                            sect,
                            section_name_text,
                            section_line_num,
                            lyrics[p],
                            new_section_stream,
                        )
                        a_phrase = transpose_phrase.transpose(
                            interval.GenericInterval(int(v[2]))
                        )
                        # a_phrase = add_new_lyrics_to_old_phrase(sect, section_name_text, section_line_num,
                        #                                     lyrics[p], new_section_stream)
                    if k == "invert":
                        print("a_phrase = invert_phrase_with_lyrics")
                        invert_phrase = add_new_lyrics_to_old_phrase(
                            sect,
                            section_name_text,
                            section_line_num,
                            lyrics[p],
                            new_section_stream,
                        )
                        a_phrase = invert_phrase.invertDiatonic(
                            note.Note(str(v[2])), inPlace=False
                        )

                    if k == "reverse":
                        print("a_phrase = reverse_phrase_with_lyrics")
                        # # notes and rests reversed as desired, but also lyrics which should not be reversed
                        # reverse_phrase = add_new_lyrics_to_old_phrase(sect, section_name_text, section_line_num,
                        #                                                 lyrics[p], new_section_stream)
                        # a_phrase = reverse(reverse_phrase, makeNotation = False)
                        new_section_stream_without_lyrics = remove_lyrics_from_phrase(
                            new_section_stream
                        )
                        reverse_phrase = reverse(
                            new_section_stream_without_lyrics, makeNotation=False
                        )
                        a_phrase = add_new_lyrics_to_old_phrase(
                            sect,
                            section_name_text,
                            section_line_num,
                            lyrics[p],
                            reverse_phrase,
                        )
                # input('Press Enter to continue...')
            else:
                # generate phrase with lyrics
                gmpwl_call_count = gmpwl_call_count + 1
                a_phrase = generate_markov_phrase_with_lyrics(
                    sect,
                    ts,
                    song_key.tonic.name,
                    song_key.mode,
                    transition,
                    bpm_transition,
                    dtransition,
                    cad_transition,
                    cad_dtransition,
                    rest_note_transition,
                    lyrics[p],
                    gmpwl_call_count,
                )

                # if an alternating line cadence is desired and the line is an even number then amend cadence
                if CADENCE_ALTERNATE_PHRASE_END == True and (
                    (section_line_num % 2) == 0
                ):
                    a_phrase = amend_cadence(a_phrase, song_key.tonic.name, ts)

                last_section_line_num = is_last_line(
                    section_line_num, sect, lines_per_section
                )
                # if an end section cadence is desired and this is the last section line then amend cadence
                if CADENCE_SECTION_END == True and last_section_line_num == True:
                    a_phrase = amend_cadence(a_phrase, song_key.tonic.name, ts)

            p0.append(a_phrase)

            # save the melody for later section repeats
            line_stream = stream.Stream()

            if sect == Section.INTRO:
                if section_line_num == 1:  # declare list
                    intro_line_stream_list = [line_stream]
                    # print("intro_line_stream_list 1", intro_line_stream_list)
                else:  # append list
                    intro_line_stream_list.append(line_stream)
                    print("intro_line_stream_list", intro_line_stream_list)
                intro_line_stream_list[section_line_num - 1].append(a_phrase)
                # intro_line_stream_list[section_line_num - 1].show('text')
                show_text_in_stream(intro_line_stream_list[section_line_num - 1], ts)

            if sect == Section.VERSE:
                if section_line_num == 1:  # declare list
                    verse_line_stream_list = [line_stream]
                    # print("verse_line_stream_list 1", verse_line_stream_list)
                else:  # append list
                    verse_line_stream_list.append(line_stream)
                    # print("verse_line_stream_list", verse_line_stream_list)
                verse_line_stream_list[section_line_num - 1].append(a_phrase)
                # verse_line_stream_list[section_line_num - 1].show('text')
                show_text_in_stream(verse_line_stream_list[section_line_num - 1], ts)

            if sect == Section.PRECHORUS:
                if section_line_num == 1:  # declare list
                    prechorus_line_stream_list = [line_stream]
                    # print("prechorus_line_stream_list 1", prechorus_line_stream_list)
                else:  # append list
                    prechorus_line_stream_list.append(line_stream)
                    print("prechorus_line_stream_list", prechorus_line_stream_list)
                prechorus_line_stream_list[section_line_num - 1].append(a_phrase)
                # prechorus_line_stream_list[section_line_num - 1].show('text')
                show_text_in_stream(
                    prechorus_line_stream_list[section_line_num - 1], ts
                )

            if sect == Section.CHORUS:
                if section_line_num == 1:  # declare list
                    chorus_line_stream_list = [line_stream]
                    # print("chorus_line_stream_list 1", chorus_line_stream_list)
                else:  # append list
                    chorus_line_stream_list.append(line_stream)
                    # print("chorus_line_stream_list", chorus_line_stream_list)

                chorus_line_stream_list[section_line_num - 1].append(a_phrase)
                # chorus_line_stream_list[section_line_num - 1].show('text')
                show_text_in_stream(chorus_line_stream_list[section_line_num - 1], ts)

            if sect == Section.SOLO:
                if section_line_num == 1:  # declare list
                    solo_line_stream_list = [line_stream]
                    # print("solo_line_stream_list 1", solo_line_stream_list)
                else:  # append list
                    solo_line_stream_list.append(line_stream)
                    print("solo_line_stream_list", solo_line_stream_list)
                solo_line_stream_list[section_line_num - 1].append(a_phrase)
                # solo_line_stream_list[section_line_num - 1].show('text')
                show_text_in_stream(solo_line_stream_list[section_line_num - 1], ts)

            if sect == Section.BRIDGE:
                if section_line_num == 1:  # declare list
                    bridge_line_stream_list = [line_stream]
                    # print("bridge_line_stream_list 1", bridge_line_stream_list)
                else:  # append list
                    bridge_line_stream_list.append(line_stream)
                    # print("bridge_line_stream_list", bridge_line_stream_list)
                bridge_line_stream_list[section_line_num - 1].append(a_phrase)
                # bridge_line_stream_list[section_line_num - 1].show('text')
                show_text_in_stream(bridge_line_stream_list[section_line_num - 1], ts)

            if sect == Section.OUTRO:
                if section_line_num == 1:  # declare list
                    outro_line_stream_list = [line_stream]
                    # print("outro_line_stream_list 1", outro_line_stream_list)
                else:  # append list
                    outro_line_stream_list.append(line_stream)
                    print("outro_line_stream_list", outro_line_stream_list)
                outro_line_stream_list[section_line_num - 1].append(a_phrase)
                # outro_line_stream_list[section_line_num - 1].show('text')
                show_text_in_stream(outro_line_stream_list[section_line_num - 1], ts)

            # change keys between generate # 20210821: only needed if key not in transition? Comment out next 8 lines.
            # draw = choice(list(transition[key].keys()), 1, list(transition[key].values()))
            # key = (key[1], draw[0])
            # ddraw = choice(list(dtransition[dkey].keys()), 1, list(dtransition[dkey].values())) # 20210821:  KeyError: (1.0, 4.0)
            # dkey = (dkey[1], ddraw[0])
            # rest_phrase_draw = choice(list(rest_phrase_transition[rest_note_key].keys()), 1, list(rest_phrase_transition[rest_note_key].values()))
            # rest_note_key = (rest_note_key[1], rest_phrase_draw[0])

        elif lyrics[p] != "" and (
            (sect == Section.INTRO and later_intro)
            or (sect == Section.VERSE and later_verse)
            or (sect == Section.PRECHORUS and later_prechorus)
            or (sect == Section.CHORUS and later_chorus)
            or (sect == Section.SOLO and later_solo)
            or (sect == Section.BRIDGE and later_bridge)
            or (sect == Section.OUTRO and later_outro)
        ):
            print("found later section line")
            section_line_num = section_line_num + 1
            print("section_line_num", section_line_num)

            # add new lyrics to old phrase. Need deepcopy of stream to avoid corrupting the initial copy
            if sect == Section.INTRO:
                later_section_stream = copy.deepcopy(
                    intro_line_stream_list[section_line_num - 1]
                )
                later_phrase = add_new_lyrics_to_old_phrase(
                    sect,
                    section_name_text,
                    section_line_num,
                    lyrics[p],
                    later_section_stream,
                )
                p0.append(later_phrase)

            if sect == Section.VERSE:
                later_section_stream = copy.deepcopy(
                    verse_line_stream_list[section_line_num - 1]
                )
                later_phrase = add_new_lyrics_to_old_phrase(
                    sect,
                    section_name_text,
                    section_line_num,
                    lyrics[p],
                    later_section_stream,
                )
                p0.append(later_phrase)

            if sect == Section.PRECHORUS:
                later_section_stream = copy.deepcopy(
                    prechorus_line_stream_list[section_line_num - 1]
                )
                later_phrase = add_new_lyrics_to_old_phrase(
                    sect,
                    section_name_text,
                    section_line_num,
                    lyrics[p],
                    later_section_stream,
                )
                p0.append(later_phrase)

            if sect == Section.CHORUS:
                later_section_stream = copy.deepcopy(
                    chorus_line_stream_list[section_line_num - 1]
                )
                later_phrase = add_new_lyrics_to_old_phrase(
                    sect,
                    section_name_text,
                    section_line_num,
                    lyrics[p],
                    later_section_stream,
                )
                p0.append(later_phrase)

            if sect == Section.SOLO:
                later_section_stream = copy.deepcopy(
                    solo_line_stream_list[section_line_num - 1]
                )
                later_phrase = add_new_lyrics_to_old_phrase(
                    sect,
                    section_name_text,
                    section_line_num,
                    lyrics[p],
                    later_section_stream,
                )
                p0.append(later_phrase)

            if sect == Section.BRIDGE:
                later_section_stream = copy.deepcopy(
                    bridge_line_stream_list[section_line_num - 1]
                )
                later_phrase = add_new_lyrics_to_old_phrase(
                    sect,
                    section_name_text,
                    section_line_num,
                    lyrics[p],
                    later_section_stream,
                )
                p0.append(later_phrase)

            if sect == Section.OUTRO:
                later_section_stream = copy.deepcopy(
                    outro_line_stream_list[section_line_num - 1]
                )
                later_phrase = add_new_lyrics_to_old_phrase(
                    sect,
                    section_name_text,
                    section_line_num,
                    lyrics[p],
                    later_section_stream,
                )
                p0.append(later_phrase)

        elif lyrics[p] == "":
            # print('found blank line')
            pass
        print("sect", sect)

        #   first_time:
        #       for each line
        #           count syllables,
        #           generate phrase for line
        #       Save verse/chorus/Prechorus/Bridge phrase
        #   else
        #       fit lyrics to verse/chorus/Prechorus/Bridge phrase

    # insert tempo

    # if TEMPO_BPM == 0.0:
    #   elsewhere tempo is taken from INPUT_MUSIC. If INPUT_MUSIC has no tempo, default to 120.0
    # if TEMPO_BPM != 0.0:
    #   use TEMPO_BPM
    if TEMPO_BPM != 0.0:
        songTempo = tempo.MetronomeMark(number=TEMPO_BPM)
    else:
        songTempo = tempo.MetronomeMark(number=120)  # Default tempo

    mm = tempo.MetronomeMark(number=songTempo.number)
    # place MetronomeMark above the stave
    mm.placement = "above"

    p0.insert([0, mm])

    print("Part 0, Set MetronomeMark:", songTempo.number)

    # insert instrument
    # p.getElementsByClass('Measure')[0].insert(0, instrument.Clarinet())
    print("Insert instrument")
    # p0.insert(0, instrument.Clarinet())

    # the_instrument_name = 'Electric Piano'
    the_instrument = music21.instrument.Instrument(instrumentName=INSTRUMENT)
    p0.insert(0, the_instrument)

    d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    # dt = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f")
    # end at the whole seconds not the milliseconds
    dt = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")

    score.insert(0, metadata.Metadata())
    score.metadata.title = (
        os.path.splitext(INPUT_MUSIC_FILENAME)[0]
        + "\n"
        + os.path.splitext(INPUT_LYRICS_FILENAME)[0]
    )
    if len(mxl_files) == 1:
        score.metadata.title = (
            os.path.splitext(mxl_files[0])[0]
            + "\n"
            + os.path.splitext(INPUT_LYRICS_FILENAME)[0]
        )
        output_filename = (
            os.path.splitext(CONF_FILENAME)[0]
            + "-"
            + os.path.splitext(INPUT_LYRICS_FILENAME)[0]
            + "-"
            + os.path.splitext(INPUT_MUSIC_FILENAME)[0]
            + "-"
            + dt
        )
    elif len(mxl_files) > 1:
        score.metadata.title = (
            os.path.splitext(mxl_files[0])[0]
            + "..."
            + os.path.splitext(mxl_files[len(mxl_files) - 1])[0]
            + "\n"
            + os.path.splitext(INPUT_LYRICS_FILENAME)[0]
        )
        output_filename = (
            os.path.splitext(CONF_FILENAME)[0]
            + "-"
            + os.path.splitext(INPUT_LYRICS_FILENAME)[0]
            + "-"
            + os.path.splitext(mxl_files[0])[0]
            + "-"
            + os.path.splitext(mxl_files[len(mxl_files) - 1])[0]
            + "-"
            + dt
        )
    elif style != "":
        score.metadata.title = os.path.splitext(INPUT_LYRICS_FILENAME)[0] + "\n" + style
        output_filename = (
            os.path.splitext(CONF_FILENAME)[0]
            + "-"
            + os.path.splitext(INPUT_LYRICS_FILENAME)[0]
            + "-"
            + style
            + "-"
            + dt
        )
    score.metadata.composer = (
        "MarkMelGen " + MARKMELGEN_VERSION + "\n" + CONF_FILENAME + "\n" + d
    )

    # replace any . with _ in output_filename
    output_filename = output_filename.replace(".", "_")

    # logger.info(
    #     f"\n show_text_in_stream(score, ts) before Save the stream as a MIDI file "
    # )
    # show_text_in_stream(score, ts)

    # Save the stream as a MIDI file. Note filtered and split midis look the same.
    # output_path = OUTPUT_PATH + output_filename + ".mid"
    # score.write("midi", fp=output_path)

    # logger.info(
    #     f"\n show_text_in_stream(score, ts) before Save the stream as a .kar file. "
    # )
    # show_text_in_stream(score, ts)

    # Save the stream as a .kar file. v1
    output_path = OUTPUT_PATH + output_filename + "_[k].kar"
    # output_path = OUTPUT_PATH + output_filename + "_[k].mid"
    stream_to_midi_with_lyrics(score, output_path)
    kar_filename = output_path

    # Save the MIDI file as a musicxml file #  most still have musescore tuple bar errors
    # midi_file_path = output_path
    # musicxml_file_path = OUTPUT_PATH + output_filename + "-midi_to_musicxml.mxl"
    # midi_to_musicxml(midi_file_path, musicxml_file_path)

    logger.info(f"check_stream_structure score ")
    structure_report = check_stream_structure(score)
    if "Error" in structure_report:
        print(structure_report["Error"])
    else:
        print("Stream Structure Report:")
    for key, value in structure_report.items():
        print(f"{key}: {value}")
        # logger.info(f"\fscore well_formed = {well_formed} ")

    well_formed = check_score_well_formedness(score)
    logger.info(f"check 1 : score well_formed = {well_formed} ")

    # Prepare the score for XML
    # prepared_score = prepare_stream_for_xml(score)

    # # write compressed musicxml output
    # with contextlib.redirect_stderr(open(os.devnull, "w")):
    #     score.write("xml", OUTPUT_PATH + output_filename + "_prepared.xml")
    #     compressXML(OUTPUT_PATH + output_filename + "_prepared.xml", deleteOriginal=True)

    # filter score
    filtered_score = filter_output_stream_for_MuseScore(score, ts, makeNotation=True)

    logger.debug(f"\n check_stream_structure filtered_score ")
    structure_report = check_stream_structure(filtered_score)
    if "Error" in structure_report:
        logger.debug(structure_report["Error"])
    else:
        logger.debug("Stream Structure Report:")
    for key, value in structure_report.items():
        logger.debug(f"{key}: {value}")

    # filtered_score.show() # triplet bad beats

    # write serialized form of stream
    # freezer_file_path = converter_freezer_save_stream(
    #     filtered_score
    # )  # Save the stream to a file
    # logger.debug(f"\nfreezer_file_path = {freezer_file_path} ")
    # # filtered_score.show("text", addEndTimes=True)
    # logger.debug(f"\nloaded_stream")
    # loaded_stream = converter_freezer_load_stream(freezer_file_path)
    # loaded_stream.show("text", addEndTimes=True)

    # well_formed = check_score_well_formedness(filtered_score)
    # logger.info(f"Check 2: filtered_score well_formed = {well_formed} ")

    # print ('write musicxml')
    # filtered_score.write('musicxml', OUTPUT_PATH + output_filename + ".musicxml")
    # print ('end of writing musicxml')

    # write compressed musicxml output
    with contextlib.redirect_stderr(open(os.devnull, "w")):
        filtered_score.write("xml", OUTPUT_PATH + output_filename + ".xml")
        compressXML(OUTPUT_PATH + output_filename + ".xml", deleteOriginal=True)

    show_text_in_stream(filtered_score, ts)

    # # Analyze the melody
    # analysis_results = analyze_melody_beats(filtered_score)

    # # Print analysis results
    # for key, value in analysis_results.items():
    #     print(f"{key}: {value}")

    log_analyze_melody_beats(filtered_score, "filtered_score")
    log_analyze_melody_notes(filtered_score, "filtered_score")

    print(
        "Final output =================================================================="
    )
    logger.info(f"Logging to {log_filename}")
    logger.info(f"Score to {OUTPUT_PATH}{output_filename}.mxl")
    # print(OUTPUT_PATH + output_filename + ".mxl")

    if DISPLAY_GRAPHS == True:
        label = "Output " + INPUT_MUSIC_FILENAME
        show_histograms(filtered_score, label)

    if DISPLAY_HTML == True:

        # show score with showscore. e.g.
        # Just remember when using it to remove MetronomeMarks to avoid a bug in OSMD:
        # score = corpus.parse('bwv66.6')
        # for el in score[tempo.MetronomeMark]:
        #     el.activeSite.remove(el)
        # show(score)
        show(filtered_score)

    if DISPLAY_MXL == True:
        print(
            "Close this score show subprocess to continue ",
            environment.UserSettings()["musicxmlPath"],
        )
        with contextlib.redirect_stderr(open(os.devnull, "w")):
            filtered_score.show()  # hangs python on musicxml viewer e.g. MuseScore

    if DISPLAY_KAR == True:
        print(
            "Close this score show subprocess to exit: ",
            environment.UserSettings()["musicxmlPath"],
            kar_filename,
        )
        subprocess.run([environment.UserSettings()["musicxmlPath"], kar_filename])

    print("MarkMelGen version " + MARKMELGEN_VERSION)

    return


def create_score_and_part(songTimeSig, song_key, TIME_SIG_WANTED):
    """
    Creates a music21 score with a part, measure, time signature, clef, and key signature.

    Args:
        songTimeSig (music21.meter.TimeSignature): The time signature from the input song.
        song_key (music21.key.Key): The key signature from the input song.
        TIME_SIG_WANTED (str): An optional desired time signature (e.g., '4/4').

    Returns:
        tuple: A tuple containing the created score (music21.stream.Score),
               the part (music21.stream.Part), and the time signature
               (music21.meter.TimeSignature).
    """

    # Create a score, part, and measure
    score = stream.Score()
    p0 = stream.Part()
    m1 = stream.Measure()

    # Determine the time signature
    ts = songTimeSig
    if TIME_SIG_WANTED is not None:
        ts = meter.TimeSignature(TIME_SIG_WANTED)  # Force desired time signature
        print("ts = TIME_SIG_WANTED ", ts, TIME_SIG_WANTED)

    print(
        "TIME_SIG numerator =",
        ts.numerator,
        " denominator =",
        ts.denominator,
        " beatCount",
        ts.beatCount,
    )

    # Insert the time signature into the measure
    m1.insert(0, ts)
    p0.insert(0, m1)

    # Check and log if the part is well-formed
    well_formed = check_score_well_formedness(p0)
    logger.info(f"check 0  : part p0 well_formed = {well_formed} ")

    # Insert the part into the score
    score.insert(0, p0)

    # Insert a treble clef
    score.insert(0, clef.TrebleClef())

    # Determine the key signature
    if song_key.mode == "major":
        the_Key = key.Key(song_key.tonic.name)
    else:
        the_Key = key.Key(song_key.tonic.name.lower())

    # Insert the key signature
    score.keySignature = key.KeySignature(the_Key.sharps)

    return score, p0, ts


def main():

    # Capture and log the command line arguments
    command_line = " ".join(sys.argv)
    logger.debug(f"Command line: {command_line}")

    global TIME_SIG_WANTED
    global USE_STYLES
    global INPUT_MUSIC_FULLY_QUALIFIED

    gmpwl_call_count = 0
    songTimeSig = meter.TimeSignature("4/4")  # default time signature
    song_key = music21.key.Key("C")  # default key signature

    if not USE_STYLES:

        if INPUT_MUSIC_FILENAME != "":  # only one mxl file to process
            mxl_files = [INPUT_MUSIC_FILENAME]
        else:  # process all .mxl files in INPUT_MUSIC_PATH
            mxl_files = [f for f in os.listdir(INPUT_MUSIC_PATH) if f.endswith(".mxl")]

        print("INPUT_MUSIC_PATH, mxl_files", INPUT_MUSIC_PATH, mxl_files)

        if mxl_files == []:
            print("exit: Error no mxl_files in INPUT_MUSIC_PATH", INPUT_MUSIC_PATH)
            sys.exit()

        # append each normalised mxl file to form one long "song"
        # song = music21.stream.Stream()
        song = music21.stream.Stream()

        # Initialize "slist" as list
        slist = []
        rest_note_transition = {}

        for mxl_file in mxl_files:
            # print('mxl_file ',mxl_file )
            INPUT_MUSIC_FULLY_QUALIFIED = INPUT_MUSIC_PATH + mxl_file
            print("Processing INPUT_MUSIC_FULLY_QUALIFIED", INPUT_MUSIC_FULLY_QUALIFIED)
            a_song = music21.converter.parse(INPUT_MUSIC_FULLY_QUALIFIED)
            rest_note_transition = append_rest_note_transition(
                rest_note_transition, a_song
            )
            print(
                "after parse mxl_file resulting rest_note_transition",
                mxl_file,
                rest_note_transition,
            )
            slist.append(a_song)

            # analyze the key of the input song
            song_key = a_song.analyze(
                "key"
            )  # music21 generic algorithm for key finding
            # print('Input song raw song_key.tonic.name, song_key.mode = ', song_key.tonic.name,
            #       song_key.mode)  # # e.g. song_key.tonic.name, song_key.mode =  B major or D minor

            if (song_key.tonic.name == "C" and song_key.mode == "major") or (
                song_key.tonic.name == "A" and song_key.mode == "minor"
            ):
                # print('No need to normalise as already normal C major or A minor.')
                song_transpose_interval = 0
            else:
                # print('Need to normalise to C major or A minor.')
                # if minor find interval to A
                if song_key.mode == "minor":
                    song_transpose_interval = interval.Interval(
                        song_key.tonic, pitch.Pitch("A")
                    )
                else:  # song is major, find interval to C
                    song_transpose_interval = interval.Interval(
                        song_key.tonic, pitch.Pitch("C")
                    )
                a_song = a_song.transpose(song_transpose_interval)

            # analyze the key of the transposed input song
            song_key = a_song.analyze(
                "key"
            )  # music21 generic algorithm for key finding
            # print('Transposed (if required) input song interval song_key.tonic.name, song_key.mode = ',
            #       song_transpose_interval, song_key.tonic.name,
            #       song_key.mode)  # # e.g. song_key.tonic.name, song_key.mode =  C major or A minor

            song.append(a_song)

        rest_note_transition = transition_frequency_to_probability(rest_note_transition)
        log_transition_analysis(
            rest_note_transition, "Rest note transition: rest_note_transition"
        )

        # print()
        # print('countKeySignatureByType',slist)
        # keycount = countKeySignatureByType(slist)
        # print('keycount',keycount)
        # print('')

        if DISPLAY_GRAPHS == True:
            label = "Input " + INPUT_MUSIC_FILENAME
            show_histograms(song, label)

        # get the timesignatures
        first = True
        for tSig in song.getTimeSignatures():
            if first:
                songTimeSig = tSig
                print(
                    "First Time Signature:", songTimeSig
                )  # eg First Time Signature: <music21.meter.TimeSignature 4/4>
                first = False
            else:
                print("Other Time Signature:", tSig)

        # Replace above with recurse
        songTimeSig = song.recurse().getElementsByClass(meter.TimeSignature)[0]
        print(
            "Using song.recurse().getElementsByClass(meter.TimeSignature)[0] =",
            songTimeSig,
        )

        # Get the tempo from the music21 converter.parse .mid
        first = True
        for sT in song.flatten().getElementsByClass("MetronomeMark"):
            if first:
                songTempo = sT
                print("First Tempo:", songTempo)
                first = False
            else:
                print("other Tempo:", sT)
        if first == True:
            songTempo = tempo.MetronomeMark(number=120)

        first = True
        for sKS in song.flatten().getElementsByClass("KeySignature"):
            if first:
                songKeySignature = sKS
                print(
                    "First KeySignature:", songKeySignature
                )  # e.g. <music21.key.KeySignature of 1 flat>
                print(".sharps:", songKeySignature.sharps)  # e.g. -1
                print(
                    ".getScale(major):", songKeySignature.getScale("major")
                )  # e.g. <music21.scale.MajorScale F major>
                first = False
            else:
                print("other KeySignature:", sKS)

        for k in song.flatten().getElementsByClass("key.Key"):
            print("key.Key:", k)

        for k in song.flatten().getElementsByClass("key"):
            print("key:", k)

        # Remove ties and merge tied notes
        song = song.stripTies()

        # Gather the note transitions
        transition = set_note_transition(song)
        log_transition_analysis(transition, "Note transition: transition")

        # Gather the beat placement matrix transitions
        bpm_transition = set_bpm_transition(song, songTimeSig)
        log_transition_analysis(
            bpm_transition, "Beat placement transition: bpm_transition"
        )

        # Gather the duration transitions
        dtransition = set_duration_transition(song)
        log_transition_analysis(dtransition, "Duration transition: dtransition")

        # Gather the note cadence transitions
        cad_transition = set_cadence(song)
        # print('cad_transition:', cad_transition)
        cad_transition_key = list(cad_transition.keys())[0]
        # print('cad_transition_key:', cad_transition_key) # e.g.

        # Analyze the transition and print results
        transition_analysis = analyze_transition(cad_transition)
        log_transition_analysis(
            cad_transition, "Cadence note transition: cad_transition"
        )

        # Gather the cadence duration transitions
        cad_dtransition = set_cadence_duration_transition(song)
        log_transition_analysis(
            cad_dtransition, "Cadence duration transition: cad_dtransition"
        )

        # # Create a score based on the transition probabilities --------------------------------------------------------------------------------------
        # #
        # # A common arrangement of nested Streams is a
        # # Score Stream containing one or more Part Streams,
        # # each Part Stream in turn containing one or more Measure Streams.
        # #
        # # i.e. need score - part - measure (- note) hierarchy
        # score = stream.Score()
        # p0 = stream.Part()
        # m1 = stream.Measure()

        # ts = songTimeSig
        # if TIME_SIG_WANTED != None:
        #     ts = meter.TimeSignature(TIME_SIG_WANTED)  # force desired time signature
        #     print("ts = TIME_SIG_WANTED ", ts, TIME_SIG_WANTED)

        # print(
        #     "TIME_SIG numerator =",
        #     ts.numerator,
        #     " denominator =",
        #     ts.denominator,
        #     " beatCount",
        #     ts.beatCount,
        # )
        # # print('duration.Duration whole, half, quarter, eighth, 16th ', duration.Duration('whole'), duration.Duration('half'), duration.Duration('quarter'), duration.Duration('eighth'), duration.Duration('half'), duration.Duration('16th'))

        # # beat_count = ts.beatCount
        # m1.insert(0, ts)
        # p0.insert(0, m1)

        # well_formed = check_score_well_formedness(p0)
        # logger.info(f"check 0  : part p0 well_formed = {well_formed} ")

        # score.insert(0, p0)

        # # score.show()

        # # c1 = clef.TrebleClef()
        # score.insert(0, clef.TrebleClef())

        # # use key from musi21 analysis of input music file
        # if song_key.mode == "major":
        #     the_Key = music21.key.Key(song_key.tonic.name)
        # else:
        #     the_Key = music21.key.Key(
        #         song_key.tonic.name.lower()
        #     )  # python convert uppercase to lowercase

        # # print('the_Key.sharps =', the_Key.sharps)  # eg .sharps: -1

        # score.keySignature = music21.key.KeySignature(the_Key.sharps)

        score, p0, ts = create_score_and_part(songTimeSig, song_key, TIME_SIG_WANTED)

        key = list(transition.keys())[0]
        print("key:", key)  # e.g. key: ('C', 'A')

        bpm_key = list(bpm_transition.keys())[0]
        print("bpm_key:", bpm_key)  # e.g. bpm_key: ('0', '1/2')

        dkey = list(dtransition.keys())[0]  # temporary variable dkey for printing

        # print('dkey:', dkey) # e.g. dkey: (1.0, 2.0)
        # print('transition.keys():', transition.keys())   # eg dict_keys([('C', 'A'), ('A', 'A'), ('A', 'C'), ('C', 'D'), ('D', 'G'), ('G', 'G'), ('G', 'A'), ('A', 'B-'), ('B-', 'F'), ('F', 'F'), ('F', 'E'), ('E', 'C'), ('D', 'C'), ('C', 'B-'), ('B-', 'A'), ('D', 'D'), ('G', 'F'), ('E', 'F'), ('F', 'D'), ('C', 'F'), ('F', 'G'), ('A', 'D'), ('C', 'C'), ('A', 'E'), ('F', 'C'), ('A', 'F'), ('B-', 'D'), ('D', 'F'), ('F', 'B-'), ('B-', 'C'), ('A', 'G'), ('D', 'E-'), ('E-', 'D'), ('E-', 'E'), ('G', 'C'), ('C', 'G'), ('F', 'G#'), ('G#', 'A'), ('A', 'B'), ('B', 'C'), ('C', 'E'), ('F', 'A'), ('F', 'E-')])
        # print('list(transition.keys()):', list(transition.keys())) # eg [('C', 'A'), ('A', 'A'), ('A', 'C'), ('C', 'D'), ('D', 'G'), ('G', 'G'), ('G', 'A'), ('A', 'B-'), ('B-', 'F'), ('F', 'F'), ('F', 'E'), ('E', 'C'), ('D', 'C'), ('C', 'B-'), ('B-', 'A'), ('D', 'D'), ('G', 'F'), ('E', 'F'), ('F', 'D'), ('C', 'F'), ('F', 'G'), ('A', 'D'), ('C', 'C'), ('A', 'E'), ('F', 'C'), ('A', 'F'), ('B-', 'D'), ('D', 'F'), ('F', 'B-'), ('B-', 'C'), ('A', 'G'), ('D', 'E-'), ('E-', 'D'), ('E-', 'E'), ('G', 'C'), ('C', 'G'), ('F', 'G#'), ('G#', 'A'), ('A', 'B'), ('B', 'C'), ('C', 'E'), ('F', 'A'), ('F', 'E-')]
        keys = [" ".join(i) for i in list(transition.keys())]
        print(
            "keys:", keys
        )  # keys: ['C A', 'A A', 'A C', 'C D', 'D G', 'G G', 'G A', 'A B-', 'B- F', 'F F', 'F E', 'E C', 'D C', 'C B-', 'B- A', 'D D', 'G F', 'E F', 'F D', 'C F', 'F G', 'A D', 'C C', 'A E', 'F C', 'A F', 'B- D', 'D F', 'F B-', 'B- C', 'A G', 'D E-', 'E- D', 'E- E', 'G C', 'C G', 'F G#', 'G# A', 'A B', 'B C', 'C E', 'F A', 'F E-']

        bpm_keys = [" ".join(map(str, i)) for i in list(bpm_transition.keys())]
        print(
            "bpm_keys:", bpm_keys
        )  # e.g. bpm_keys: ['0 1/2', '1/2 0', '0 0', '0 1/3', '1/2 1/4', '1/4 3/4', '3/4 0', '1/3 0', '0 1/4', '1/4 0', '1/2 1/8', '1/8 0', '0 2/3', '2/3 1/3', '1/2 1/2', '0 1/8', '1/8 1/2', '1/2 2/3', '2/3 0', '1/4 1/2', '1/2 3/4', '1/3 2/3', '2/3 1/2', '1/8 2/3', '0 3/4', '2/3 3/4', '1/3 1/4', '2/3 1/4', '3/4 1/4', '3/4 1/2', '1/2 1/3']

        # print('dtransition.keys():',dtransition.keys()) # eg          dtransition.keys(): dict_keys([(1.0, 2.0), (2.0, 0.5), (0.5, 0.5), (0.5, 2.0), (0.5, 1.0), (1.0, 1.5), (1.5, 0.5), (0.5, 0.25), (0.25, 0.25), (0.25, 2.0), (0.25, 0.5), (1.0, 1.0), (1.0, 0.5), (0.5, 3.0), (3.0, 1.0), (0.25, Fraction(1, 3)), (Fraction(1, 3), 0.5), (2.0, 0.25), (Fraction(1, 3), 0.25), (0.25, 0.75), (0.75, 0.5), (0.5, 1.5), (1.0, 1.25), (1.25, 0.25), (0.25, 1.5), (0.5, 0.75), (0.75, 0.25), (0.25, 1.0), (2.0, 1.0), (1.0, 0.25), (2.0, 2.0), (3.0, 0.25), (0.5, 4.0), (4.0, 2.0)])
        # print('list(dtransition.keys()):', list(dtransition.keys())) # eg list(dtransition.keys()): [(1.0, 2.0), (2.0, 0.5), (0.5, 0.5), (0.5, 2.0), (0.5, 1.0), (1.0, 1.5), (1.5, 0.5), (0.5, 0.25), (0.25, 0.25), (0.25, 2.0), (0.25, 0.5), (1.0, 1.0), (1.0, 0.5), (0.5, 3.0), (3.0, 1.0), (0.25, Fraction(1, 3)), (Fraction(1, 3), 0.5), (2.0, 0.25), (Fraction(1, 3), 0.25), (0.25, 0.75), (0.75, 0.5), (0.5, 1.5), (1.0, 1.25), (1.25, 0.25), (0.25, 1.5), (0.5, 0.75), (0.75, 0.25), (0.25, 1.0), (2.0, 1.0), (1.0, 0.25), (2.0, 2.0), (3.0, 0.25), (0.5, 4.0), (4.0, 2.0)]
        # dkeys = [' '.join(i) for i in list(dtransition.keys())] # TypeError: sequence item 0: expected str instance, float found
        # Convert the list into a string, that is, traverse the elements of the list and convert it into a string e.g. print('##'.join(map(str,li)))
        dkeys = [" ".join(map(str, i)) for i in list(dtransition.keys())]
        # print('dkeys:', dkeys) # e.g.                                                        dkeys: ['1.0 2.0', '2.0 0.5', '0.5 0.5', '0.5 2.0', '0.5 1.0', '1.0 1.5', '1.5 0.5', '0.5 0.25', '0.25 0.25', '0.25 2.0', '0.25 0.5', '1.0 1.0', '1.0 0.5', '0.5 3.0', '3.0 1.0', '0.25 1/3', '1/3 0.5', '2.0 0.25', '1/3 0.25', '0.25 0.75', '0.75 0.5', '0.5 1.5', '1.0 1.25', '1.25 0.25', '0.25 1.5', '0.5 0.75', '0.75 0.25', '0.25 1.0', '2.0 1.0', '1.0 0.25', '2.0 2.0', '3.0 0.25', '0.5 4.0', '4.0 2.0']

        # have lyrics (see https://en.wikipedia.org/wiki/Syllabic_verse )

        process_lyrics(
            INPUT_LYRICS_FULLY_QUALIFIED,
            _section_name_matches,
            p0,
            ts,
            song_key,
            transition,
            bpm_transition,
            dtransition,
            cad_transition,
            cad_dtransition,
            rest_note_transition,
            gmpwl_call_count,
            score,
            mxl_files,
            "",
        )

    else:  # USE_STYLES

        for style in USE_STYLES:
            # print("using", style)
            # # # Load the style files for the style in USE_STYLES
            # # style_path = os.path.join(INPUT_STYLE_PATH, style)
            # # if not os.path.isdir(style_path):
            # #     print(f"Error: Style directory not found at {style_path}")
            # #     sys.exit()

            # style_path = INPUT_STYLE_PATH  # Assumes you have a variable defined like this in your main script

            # transition, bpm_transition, dtransition, cad_transition, cad_dtransition, rest_note_transition = load_transitions_from_style(
            #     style_path
            # )

            # # Check if transitions not loaded successfully
            # if not (
            #     transition is not None
            #     and bpm_transition is not None
            #     and dtransition is not None
            #     and cad_transition is not None
            #     and cad_dtransition is not None
            #     and rest_note_transition is not None
            # ):
            #     # Handle the case where the files were not found or an error occurred
            #     print("Failed to load all transition files. Check the error log for details.")
            #     sys.exit()
            print("using", style)
            style_path = os.path.join(INPUT_STYLE_PATH, style)
            (
                transition,
                bpm_transition,
                dtransition,
                cad_transition,
                cad_dtransition,
                rest_note_transition,
            ) = load_transition_files(style_path)

            # Check if transitions not loaded successfully
            if not (
                transition is not None
                and bpm_transition is not None
                and dtransition is not None
                and cad_transition is not None
                and cad_dtransition is not None
                and rest_note_transition is not None
            ):
                print(
                    "Failed to load all transition files. Check the error log for details."
                )
                sys.exit()

            # Set other parameters for process_lyrics
            # song_key = music21.key.Key('C')  # Example key, set appropriately
            # ts = music21.meter.TimeSignature('4/4')  # Example time signature, set appropriately
            # p0 = music21.stream.Part()
            # score = music21.stream.Score()

            score, p0, ts = create_score_and_part(
                songTimeSig, song_key, TIME_SIG_WANTED
            )

            mxl_files = []  # Example list of mxl files, set appropriately
            gmpwl_call_count = 0

            # input('USE_STYLES Press Enter to continue...')
            process_lyrics(
                INPUT_LYRICS_FULLY_QUALIFIED,
                _section_name_matches,
                p0,
                ts,
                song_key,
                transition,
                bpm_transition,
                dtransition,
                cad_transition,
                cad_dtransition,
                rest_note_transition,
                gmpwl_call_count,
                score,
                mxl_files,
                style,
            )

    return  # end of main


def parse_configuration_file(config):
    """
    given a config
    check sections and options are valid
    exit if not
    """
    sections_expected = [
        "paths",
        "filenames",
        "markmelgen",
        "song_intro",
        "song_verse",
        "song_prechorus",
        "song_chorus",
        "song_solo",
        "song_bridge",
        "song_outro",
    ]
    paths_options_expected = [
        "input_lyrics_path",
        "input_music_path",
        "input_style_path",
        "output_path",
    ]
    filenames_options_expected = ["input_lyrics_filename", "input_music_filename"]
    markmelgen_options_expected = [
        "beat_placements_denied_set",
        "beat_placements_denominator_denied_set",
        "beat_placement_denominator_maximum_allowed",
        "cadence_alternate_phrase_end",
        "cadence_dur_min",
        "cadence_section_end",
        "cadence_tone_frequency",
        "display_graphs",
        "display_html",
        "display_mxl",
        "display_kar",
        "duration_eq",
        "duration_set",
        "dur_least",
        "dur_longest",
        "dur_prev_diff",
        "dur_rational",
        "dur_tuplet",
        "instrument",
        "max_phrase_rest",
        "rest_note_line_offset",
        "tempo_bpm",
        "time_sig_wanted",
        "tone_ascent",
        "tone_ascent_min_interval",
        "tone_ascent_trigger_every_n_times",
        "tone_descent",
        "tone_descent_max_interval",
        "tone_descent_trigger_every_n_times",
        "tone_eq",
        "tone_interval",
        "tones_on_key",
        "tones_off_key",
        "tone_prev_interval",
        "tone_range_bottom",
        "tone_range_top",
        "tone_scale_set",
        "tone_scale_on_anhemitonic",
        "tone_scale_on_hemitonic",
        "use_styles",
    ]
    song_section_options_expected = [
        "duration_set",
        "dur_least",
        "dur_longest",
        "dur_prev_diff",
        "dur_rational",
        "dur_tuplet",
        "rest_note_line_offset",
        "tones_on_key",
        "tone_prev_interval",
        "tone_range_bottom",
        "tone_range_top",
        "tone_scale_set",
    ]

    print("Checking configuration file structure...")

    # sections
    sections_actual = config.sections()
    # print('sections_expected:', sections_expected)
    # print('sections_actual  :', sections_actual)
    if sections_actual == sections_expected:
        print("Configuration file sections as expected.")
    else:
        print(
            "exit: Error in configuration file. Actual sections does not equal expected sections."
        )
        print("sections_expected:", sections_expected)
        print("sections_actual  :", sections_actual)
        sys.exit()

    # paths
    paths_options_actual = config.options("paths")
    # print('paths_options_expected:', paths_options_expected)
    # print('paths_options_actual  :', paths_options_actual)
    if paths_options_actual == paths_options_expected:
        print("Configuration file paths options as expected.")
    else:
        print(
            "exit: Error in configuration file. Actual paths options does not equal expected paths options."
        )
        print("paths_options_expected:", paths_options_expected)
        print("paths_options_actual  :", paths_options_actual)
        sys.exit()

    # filenames
    filenames_options_actual = config.options("filenames")
    # print('filenames_options_expected:', filenames_options_expected)
    # print('filenames_options_actual  :', filenames_options_actual)
    if filenames_options_actual == filenames_options_expected:
        print("Configuration file filenames options as expected.")
    else:
        print(
            "exit: Error in configuration file. Actual filenames options does not equal expected filenames options."
        )
        print("filenames_options_expected:", filenames_options_expected)
        print("filenames_options_actual  :", filenames_options_actual)
        sys.exit()

    # markmelgen
    markmelgen_options_actual = config.options("markmelgen")
    # print('markmelgen_options_expected:', markmelgen_options_expected)
    # print('markmelgen_options_actual  :', markmelgen_options_actual)
    if markmelgen_options_actual == markmelgen_options_expected:
        print("Configuration file markmelgen options as expected.")
    else:
        print(
            "exit: Error in configuration file. Actual markmelgen options does not equal expected markmelgen options."
        )
        print("markmelgen_options_expected:", markmelgen_options_expected)
        print("markmelgen_options_actual  :", markmelgen_options_actual)
        sys.exit()

    # song_intro
    song_intro_options_actual = config.options("song_intro")
    # print('song_intro_options_potentially:      ', song_section_options_expected)
    # print('song_intro_options_actual     :      ', song_intro_options_actual)
    # if song_intro_options_actual == song_section_options_expected:
    #     print('Configuration file song_intro options as expected.')
    # else:
    #     print('exit: Error in configuration file. Actual song_intro options does not equal expected song_intro options.')
    #     sys.exit()

    # song_verse
    song_verse_options_actual = config.options("song_verse")
    # print('song_verse_options_potentially:      ', song_section_options_expected)
    # print('song_verse_options_actual     :      ', song_verse_options_actual)
    # if song_verse_options_actual == song_section_options_expected:
    #     print('Configuration file song_verse options as expected.')
    # else:
    #     print('exit: Error in configuration file. Actual song_verse options does not equal expected song_verse options.')
    #     sys.exit()

    # song_prechorus
    song_prechorus_options_actual = config.options("song_prechorus")
    # print('song_prechorus_options_potentially:  ', song_section_options_expected)
    # print('song_prechorus_options_actual     :  ', song_prechorus_options_actual)
    # if song_prechorus_options_actual == song_section_options_expected:
    #     print('Configuration file song_prechorus options as expected.')
    # else:
    #     print('exit: Error in configuration file. Actual song_prechorus options does not equal expected song_prechorus options.')
    #     sys.exit()

    # song_chorus
    song_chorus_options_actual = config.options("song_chorus")
    # print('song_chorus_options_potentially:     ', song_section_options_expected)
    # print('song_chorus_options_actual     :     ', song_chorus_options_actual)
    # if song_chorus_options_actual == song_section_options_expected:
    #     print('Configuration file song_chorus options as expected.')
    # else:
    #     print('exit: Error in configuration file. Actual song_chorus options does not equal expected song_chorus options.')
    #     sys.exit()

    # song_solo
    song_solo_options_actual = config.options("song_solo")
    # print('song_solo_options_potentially:       ', song_section_options_expected)
    # print('song_solo_options_actual     :       ', song_solo_options_actual)
    # if song_solo_options_actual == song_section_options_expected:
    #     print('Configuration file song_solo options as expected.')
    # else:
    #     print('exit: Error in configuration file. Actual song_solo options does not equal expected song_solo options.')
    #     sys.exit()

    # song_bridge
    song_bridge_options_actual = config.options("song_bridge")
    # print('song_bridge_options_potentially:     ', song_section_options_expected)
    # print('song_bridge_options_actual     :     ', song_bridge_options_actual)
    # if song_bridge_options_actual == song_section_options_expected:
    #     print('Configuration file song_bridge options as expected.')
    # else:
    #     print('exit: Error in configuration file. Actual song_bridge options does not equal expected song_bridge options.')
    #     sys.exit()

    # song_outro
    song_outro_options_actual = config.options("song_outro")
    # print('song_outro_options_potentially:      ', song_section_options_expected)
    # print('song_outro_options_actual     :      ', song_outro_options_actual)
    # if song_outro_options_actual == song_section_options_expected:
    #     print('Configuration file song_outro options as expected.')
    # else:
    #     print('exit: Error in configuration file. Actual song_outro options does not equal expected song_outro options.')
    #     sys.exit()

    # input('Press Enter to continue...')
    return


def get_config():
    """
    function that reads the config
    returns text
    """

    global CONF_FILENAME

    # [paths]
    global INPUT_LYRICS_PATH
    global INPUT_LYRICS_FULLY_QUALIFIED
    global INPUT_MUSIC_PATH
    global INPUT_MUSIC_FULLY_QUALIFIED
    global INPUT_STYLE_PATH

    global OUTPUT_PATH

    # [filenames]
    global INPUT_LYRICS_FILENAME
    global INPUT_MUSIC_FILENAME

    # [markmelgen]
    global BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED
    global BEAT_PLACEMENTS_DENIED_SET
    global BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET
    global CADENCE_ALTERNATE_PHRASE_END
    global CADENCE_DUR_MIN
    global CADENCE_SECTION_END
    global CADENCE_TONE_FREQUENCY
    global CADENCE_TONE_PROBABILITY
    global CADENCE_TONE_SAMPLES

    global DISPLAY_GRAPHS
    global DISPLAY_HTML
    global DISPLAY_MXL
    global DISPLAY_KAR

    global DURATION_EQ
    global DURATION_SET
    global DUR_RATIONAL
    global DUR_TUPLET
    global DUR_LEAST
    global DUR_LONGEST
    global DUR_PREV_DIFF

    global INSTRUMENT

    global MAX_PHRASE_REST

    global PER_SECTION_LIST_LENGTH

    global PER_SECTION_DURATION_SET
    global PER_SECTION_DUR_LEAST
    global PER_SECTION_DUR_LONGEST
    global PER_SECTION_DUR_PREV_DIFF
    global PER_SECTION_DUR_RATIONAL
    global PER_SECTION_DUR_TUPLET
    global PER_SECTION_REST_NOTE_LINE_OFFSET
    global PER_SECTION_TONES_ON_KEY
    global PER_SECTION_TONE_PREV_INTERVAL
    global PER_SECTION_TONE_RANGE_BOTTOM
    global PER_SECTION_TONE_RANGE_TOP
    global PER_SECTION_TONE_SCALE_SET

    global REST_NOTE_LINE_OFFSET

    global TEMPO_BPM
    global TIME_SIG_WANTED

    global TONE_ASCENT
    global TONE_ASCENT_MIN_INTERVAL
    global TONE_ASCENT_TRIGGER
    global TONE_ASCENT_TRIGGER_EVERY_N_TIMES

    global TONE_DESCENT
    global TONE_DESCENT_MAX_INTERVAL
    global TONE_DESCENT_TRIGGER
    global TONE_DESCENT_TRIGGER_EVERY_N_TIMES

    global TONE_EQ
    global TONE_INTERVAL
    global TONES_ON_KEY
    global TONES_OFF_KEY
    global TONE_PREV_INTERVAL

    global TONE_RANGE_MID
    global TONE_RANGE_BOTTOM
    global TONE_RANGE_TOP

    global TONE_SCALE_SET
    global TONE_SCALE_ON_ANHEMITONIC
    global TONE_SCALE_ON_HEMITONIC

    global USE_STYLES
    USE_STYLES = False

    # Capture and log the command line arguments
    command_line = " ".join(sys.argv)
    logger.debug(f"Command line: {command_line}")

    parser = argparse.ArgumentParser(
        description="MarkMelGen: A tool for generating Markov melodies."
    )

    # Specify command line arguments.
    parser.add_argument(
        "-c",
        "--config",
        help="config file path (default: MarkMelGen.conf)",
        default="MarkMelGen.conf",
        type=str,
    )

    # New arguments for controlling score display
    parser.add_argument("--display-graphs", help="Display graphs", action="store_true")
    parser.add_argument(
        "--display-html", help="Display HTML score", action="store_true"
    )
    parser.add_argument(
        "--display-mxl", help="Display MuseScore MXL score", action="store_true"
    )
    parser.add_argument(
        "--display-kar", help="Display MuseScore KAR score", action="store_true"
    )

    # Specify the log level

    # Example log messages
    # logger.debug(f"Logging to {log_filename} ")
    # logger.info("Info test message")
    # logger.warning("Warning test message")
    # logger.error("Error test message")
    # logger.critical("Critical test message")

    parser.add_argument(
        "-l",
        "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)",
    )

    # Override configuration settings
    parser.add_argument(
        "-o",
        "--override",
        action="append",
        help="Override certain configuration settings in the format 'section.key=value'. Can be specified multiple times. e.g. -o paths.INPUT_LYRICS_PATH=input\\lyrics\\ -o filenames.INPUT_LYRICS_FILENAME=Drifting_Stranger.txt -o markmelgen.DISPLAY_GRAPHS=True -o markmelgen.TEMPO_BPM=90.0 -o markmelgen.TIME_SIG_WANTED='6/8' -o markmelgen.DURATION_SET=['0.5','1.25','1.5'] -o markmelgen.USE_STYLES=['early_jazz_1','early_jazz_2']",
    )

    # Add the style arguments
    parser.add_argument(
        "--create-style",
        type=str,
        help="Path to input music directory (must be a directory)",
    )

    parser.add_argument(
        "--list-styles", action="store_true", help="List available styles and exit"
    )

    # parser.add_argument(
    #     "--use-styles", nargs="+", help="List of styles to use", type=str
    # )

    parser.add_argument(
        "-v", "--version", action="store_true", help="Show version and exit"
    )

    # Parse command line arguments.
    args = parser.parse_args()

    if args.version:
        print(f"Processing argument: --version (value: {args.version})")
        print(MARKMELGEN_VERSION)
        sys.exit()

    setup_logger(args.loglevel)

    DISPLAY_HTML = args.display_html
    DISPLAY_MXL = args.display_mxl
    DISPLAY_KAR = args.display_kar

    logger.debug(f"DISPLAY_HTML: {DISPLAY_HTML}")
    logger.debug(f"DISPLAY_MXL: {DISPLAY_MXL}")
    logger.debug(f"DISPLAY_KAR: {DISPLAY_KAR}")

    # input('Press Enter to continue...')

    """Get Config Parameters"""
    config = configparser.ConfigParser(allow_no_value=True)

    config.read(args.config)

    CONF_FILENAME = os.path.basename(args.config)
    print("MarkMelGen version " + MARKMELGEN_VERSION)
    print("args.config, CONF_FILENAME", args.config, CONF_FILENAME)
    # e.g. default  = MarkMelGen.conf MarkMelGen.conf
    # e.g. override = conf\test\All-Sections.conf All-Sections.conf

    parse_configuration_file(config)

    INPUT_LYRICS_FILENAME = config["filenames"]["INPUT_LYRICS_FILENAME"]
    INPUT_MUSIC_FILENAME = config["filenames"]["INPUT_MUSIC_FILENAME"]

    temp_INPUT_LYRICS_PATH = config["paths"]["INPUT_LYRICS_PATH"]
    if temp_INPUT_LYRICS_PATH != None:
        INPUT_LYRICS_PATH = temp_INPUT_LYRICS_PATH

    temp_INPUT_MUSIC_PATH = config["paths"]["INPUT_MUSIC_PATH"]
    # print('INPUT_MUSIC_PATH = temp_INPUT_MUSIC_PATH', INPUT_MUSIC_PATH, temp_INPUT_MUSIC_PATH )
    if temp_INPUT_MUSIC_PATH != "":
        INPUT_MUSIC_PATH = temp_INPUT_MUSIC_PATH
    print("INPUT_MUSIC_PATH", INPUT_MUSIC_PATH)

    temp_INPUT_STYLE_PATH = config["paths"]["INPUT_STYLE_PATH"]
    # print('INPUT_STYLE_PATH = temp_INPUT_STYLE_PATH', INPUT_STYLE_PATH, temp_INPUT_STYLE_PATH )
    if temp_INPUT_STYLE_PATH != "":
        INPUT_STYLE_PATH = temp_INPUT_STYLE_PATH
    print("INPUT_STYLE_PATH", INPUT_STYLE_PATH)

    INPUT_LYRICS_FULLY_QUALIFIED = INPUT_LYRICS_PATH + INPUT_LYRICS_FILENAME
    print("INPUT_LYRICS_FULLY_QUALIFIED", INPUT_LYRICS_FULLY_QUALIFIED)

    INPUT_MUSIC_FULLY_QUALIFIED = INPUT_MUSIC_PATH + INPUT_MUSIC_FILENAME
    print("INPUT_MUSIC_FULLY_QUALIFIED", INPUT_MUSIC_FULLY_QUALIFIED)

    temp_OUTPUT_PATH = config["paths"]["OUTPUT_PATH"]
    if temp_OUTPUT_PATH != None:
        OUTPUT_PATH = temp_OUTPUT_PATH
    print("OUTPUT_PATH", OUTPUT_PATH)

    # [markmelgen]
    temp_BEAT_PLACEMENTS_DENIED_SET = config["markmelgen"]["BEAT_PLACEMENTS_DENIED_SET"]
    print("string temp_BEAT_PLACEMENTS_DENIED_SET", temp_BEAT_PLACEMENTS_DENIED_SET)

    if temp_BEAT_PLACEMENTS_DENIED_SET != "":
        try:
            # Safely evaluate the string to a list
            temp_BEAT_PLACEMENTS_DENIED_SET = ast.literal_eval(
                temp_BEAT_PLACEMENTS_DENIED_SET
            )
            # Convert each string in the list to a Fraction
            BEAT_PLACEMENTS_DENIED_SET = [
                eval(f) for f in temp_BEAT_PLACEMENTS_DENIED_SET
            ]
        except BaseException as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("exit: Error BEAT_PLACEMENTS_DENIED_SET", BEAT_PLACEMENTS_DENIED_SET)
            sys.exit()
    print("BEAT_PLACEMENTS_DENIED_SET", BEAT_PLACEMENTS_DENIED_SET)
    # input('Press Enter to continue...')

    # BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET is a set of integers
    temp_BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET = config["markmelgen"][
        "BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET"
    ]
    print(
        "string BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET",
        temp_BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET,
    )

    if temp_BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET != "":
        # ast.literal_eval: Safely evaluate an expression node or a string containing a Python literal or container display.
        # The string or node provided may only consist of the following Python literal structures:
        # strings, bytes, numbers, tuples, lists, dicts, sets, booleans, None, bytes and sets.
        try:
            BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET = ast.literal_eval(
                temp_BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET
            )
            if not all(
                isinstance(item, int) for item in BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET
            ):
                raise ValueError(
                    "All items in BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET must be integers"
                )
        except BaseException as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print(
                "exit: Error BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET",
                BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET,
            )
            sys.exit()
    print(
        "BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET", BEAT_PLACEMENTS_DENOMINATOR_DENIED_SET
    )
    # input('Press Enter to continue...')

    # BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED is an integer >= 0
    temp_BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED = config["markmelgen"][
        "BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED"
    ]
    try:
        if is_number_an_integer(temp_BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED):
            BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED = int(
                temp_BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED
            )
            if BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED < 0:
                raise ValueError(
                    "BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED must be >= 0"
                )
        else:
            print(
                "exit: ValueError BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED",
                temp_BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED,
                "is not an integer",
            )
            sys.exit()
    except ValueError as e:
        print("exit:", e)
        sys.exit()
    print(
        "BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED",
        BEAT_PLACEMENT_DENOMINATOR_MAXIMUM_ALLOWED,
    )
    # input('Press Enter to continue...')

    CADENCE_ALTERNATE_PHRASE_END = config["markmelgen"].getboolean(
        "CADENCE_ALTERNATE_PHRASE_END"
    )
    print("CADENCE_ALTERNATE_PHRASE_END", CADENCE_ALTERNATE_PHRASE_END)

    # CADENCE_DUR_MIN can be a Fraction or a float
    temp_CADENCE_DUR_MIN = config["markmelgen"]["CADENCE_DUR_MIN"]
    try:
        if not temp_CADENCE_DUR_MIN.isnumeric():
            CADENCE_DUR_MIN = Fraction(temp_CADENCE_DUR_MIN)
    except ValueError:
        print("ValueError", temp_CADENCE_DUR_MIN, " is not a number")
        # throw ValueError(temp_CADENCE_DUR_MIN + " is not a number")
    print("CADENCE_DUR_MIN", CADENCE_DUR_MIN)

    CADENCE_SECTION_END = config["markmelgen"].getboolean("CADENCE_SECTION_END")
    print("CADENCE_SECTION_END", CADENCE_SECTION_END)

    temp_CADENCE_TONE_FREQUENCY = config["markmelgen"]["CADENCE_TONE_FREQUENCY"]
    print("string CADENCE_TONE_FREQUENCY", temp_CADENCE_TONE_FREQUENCY)

    if temp_CADENCE_TONE_FREQUENCY != "":
        # ast.literal_eval: Safely evaluate an expression node or a string containing a Python literal or container display.
        # The string or node provided may only consist of the following Python literal structures:
        # strings, bytes, numbers, tuples, lists, dicts, sets, booleans, None, bytes and sets.
        total = 0
        CADENCE_TONE_FREQUENCY = ast.literal_eval(temp_CADENCE_TONE_FREQUENCY)
        print("Python literal structure CADENCE_TONE_FREQUENCY", CADENCE_TONE_FREQUENCY)
        for cadence_tone_frequency_num in range(0, len(CADENCE_TONE_FREQUENCY)):
            cadence_tone_name = CADENCE_TONE_FREQUENCY[cadence_tone_frequency_num][0]
            cadence_tone_frequency = CADENCE_TONE_FREQUENCY[cadence_tone_frequency_num][
                1
            ]
            total = total + cadence_tone_frequency
            print(
                "cadence_tone_frequency_num=",
                cadence_tone_frequency_num,
                "cadence_tone_name=",
                cadence_tone_name,
                "cadence_tone_frequency=",
                cadence_tone_frequency,
            )
            if cadence_tone_frequency <= 0.0:
                print("exit: Error CADENCE_TONE_FREQUENCY frequency < 1")
                sys.exit()

        # convert CADENCE_TONE_FREQUENCY to CADENCE_TONE_PROBABILITY
        print("Total cadence tone frequency=", total)

        # Compute the probability for each transition -----------------------------------------------------------
        ptotal = 0
        CADENCE_TONE_PROBABILITY = CADENCE_TONE_FREQUENCY
        for cadence_tone_num in range(0, len(CADENCE_TONE_PROBABILITY)):
            CADENCE_TONE_PROBABILITY[cadence_tone_num][1] = (
                CADENCE_TONE_PROBABILITY[cadence_tone_num][1] / total
            )
            ptotal = ptotal + CADENCE_TONE_PROBABILITY[cadence_tone_num][1]
        print("CADENCE_TONE_PROBABILITY=", CADENCE_TONE_PROBABILITY)
        print("Probability total=", ptotal)

        # create a 100 element sample of cadence tones which can be used to choose a random cadence tone.
        CADENCE_TONE_SAMPLES = sum(
            ([val] * int((prob * 100)) for val, prob in CADENCE_TONE_PROBABILITY), []
        )
        print("CADENCE_TONE_SAMPLES=", CADENCE_TONE_SAMPLES)
    else:
        CADENCE_TONE_FREQUENCY = ""

    DISPLAY_GRAPHS = config["markmelgen"].getboolean("DISPLAY_GRAPHS")
    print("DISPLAY_GRAPHS", DISPLAY_GRAPHS)

    DISPLAY_HTML = config["markmelgen"].getboolean("DISPLAY_HTML")
    print("DISPLAY_HTML", DISPLAY_HTML)

    DISPLAY_MXL = config["markmelgen"].getboolean("DISPLAY_MXL")
    print("DISPLAY_MXL", DISPLAY_MXL)

    DISPLAY_KAR = config["markmelgen"].getboolean("DISPLAY_KAR")
    print("DISPLAY_KAR", DISPLAY_KAR)

    # input('Press Enter to continue...')

    temp_DURATION_EQ = config["markmelgen"]["DURATION_EQ"]
    print("string DURATION_EQ", temp_DURATION_EQ)

    if temp_DURATION_EQ != "":
        # ast.literal_eval: Safely evaluate an expression node or a string containing a Python literal or container display.
        # The string or node provided may only consist of the following Python literal structures:
        # strings, bytes, numbers, tuples, lists, dicts, sets, booleans, None, bytes and sets.
        DURATION_EQ = ast.literal_eval(temp_DURATION_EQ)
        print("Python literal structure DURATION_EQ", DURATION_EQ)
        for duration_eq_num in range(0, len(DURATION_EQ)):
            duration_name = DURATION_EQ[duration_eq_num][0]
            duration_factor = DURATION_EQ[duration_eq_num][1]
            # print('duration_eq_num=',duration_eq_num,'duration_name=', duration_name,'duration_factor=', duration_factor)
            if duration_factor <= 0.0:
                print("exit: Error DURATION_EQ factor <= 0.0")
                sys.exit()
    else:
        DURATION_EQ = ""
    # input('Press Enter to continue...')

    temp_DURATION_SET = config["markmelgen"]["DURATION_SET"]
    print("string DURATION_SET", temp_DURATION_SET)

    if temp_DURATION_SET != "":
        # ast.literal_eval: Safely evaluate an expression node or a string containing a Python literal or container display.
        # The string or node provided may only consist of the following Python literal structures:
        # strings, bytes, numbers, tuples, lists, dicts, sets, booleans, None, bytes and sets.
        try:
            DURATION_SET = ast.literal_eval(temp_DURATION_SET)
        except BaseException as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("exit: Error DURATION_SET", DURATION_SET)
            sys.exit()

        # print('Python literal structure for DURATION_SET strings evaluated to:', DURATION_SET, type(DURATION_SET))
        if not isinstance(DURATION_SET, list):
            print("exit: DURATION_SET is not a list e.g. []")
            sys.exit()
        for dur_num in range(0, len(DURATION_SET)):
            # print('dur type()', DURATION_SET[dur_num], type(DURATION_SET[dur_num]))
            temp_dur = DURATION_SET[dur_num]
            if is_number_an_integer(temp_dur):
                print(
                    "exit: ValueError dur_frac",
                    temp_dur,
                    " is an integer e.g. 1. Should be a float e.g. 1.0",
                )
                sys.exit()
            try:
                if not temp_dur.isnumeric():
                    dur_frac = Fraction(temp_dur)
                    DURATION_SET[dur_num] = dur_frac
            except ValueError:
                print("exit: ValueError dur_frac", temp_dur, " is not a number")
                sys.exit()
                # throw ValueError(temp_dur + " is not a number")
            # print("dur_frac", dur_frac)
    else:
        DURATION_SET = []
    print("DURATION_SET strings converted to Fractions:", DURATION_SET)
    PER_SECTION_DURATION_SET = [DURATION_SET] * PER_SECTION_LIST_LENGTH

    # input('Press Enter to continue...')

    # DUR_LEAST can be a Fraction or a float
    temp_DUR_LEAST = config["markmelgen"]["DUR_LEAST"]
    try:
        if not temp_DUR_LEAST.isnumeric():
            DUR_LEAST = Fraction(temp_DUR_LEAST)
    except ValueError:
        print("exit: ValueError DUR_LEAST", temp_DUR_LEAST, " is not a number")
        sys.exit()
        # throw ValueError(temp_DUR_LEAST + " is not a number")
    print("DUR_LEAST", DUR_LEAST)
    # PER_SECTION_DUR_LEAST[PER_SECTION_LIST_LENGTH - 1] = DUR_LEAST
    PER_SECTION_DUR_LEAST = [DUR_LEAST] * PER_SECTION_LIST_LENGTH

    # DUR_LONGEST can be a Fraction or a float
    temp_DUR_LONGEST = config["markmelgen"]["DUR_LONGEST"]
    try:
        if not temp_DUR_LONGEST.isnumeric():
            DUR_LONGEST = Fraction(temp_DUR_LONGEST)
    except ValueError:
        print("exit: ValueError DUR_LONGEST", temp_DUR_LONGEST, " is not a number")
        sys.exit()
        # throw ValueError(temp_DUR_LONGEST + " is not a number")
    print("DUR_LONGEST", DUR_LONGEST)
    # PER_SECTION_DUR_LONGEST[PER_SECTION_LIST_LENGTH - 1] = DUR_LONGEST
    PER_SECTION_DUR_LONGEST = [DUR_LONGEST] * PER_SECTION_LIST_LENGTH

    DUR_RATIONAL = config["markmelgen"].getboolean("DUR_RATIONAL")
    print("DUR_RATIONAL", DUR_RATIONAL)
    PER_SECTION_DUR_RATIONAL = [DUR_RATIONAL] * PER_SECTION_LIST_LENGTH

    DUR_TUPLET = config["markmelgen"].getboolean("DUR_TUPLET")
    print("DUR_TUPLET", DUR_TUPLET)
    # PER_SECTION_DUR_TUPLET[PER_SECTION_LIST_LENGTH - 1] = DUR_TUPLET
    PER_SECTION_DUR_TUPLET = [DUR_TUPLET] * PER_SECTION_LIST_LENGTH

    if DUR_RATIONAL and DUR_TUPLET:
        print("exit: Error DUR_RATIONAL and DUR_TUPLET cannot both be True ")
        sys.exit()

    DUR_PREV_DIFF = config["markmelgen"].getfloat("DUR_PREV_DIFF")
    print("DUR_PREV_DIFF", DUR_PREV_DIFF)
    if DUR_PREV_DIFF != 0 and DUR_PREV_DIFF <= 1:
        print("exit: Error DUR_PREV_DIFF != 0 and DUR_PREV_DIFF <= 1 ")
        sys.exit()
    PER_SECTION_DUR_PREV_DIFF = [DUR_PREV_DIFF] * PER_SECTION_LIST_LENGTH

    INSTRUMENT = config["markmelgen"]["INSTRUMENT"]
    print("INSTRUMENT", INSTRUMENT)

    MAX_PHRASE_REST = config["markmelgen"].getfloat("MAX_PHRASE_REST")
    print("MAX_PHRASE_REST", MAX_PHRASE_REST)

    # REST_NOTE_LINE_OFFSET can be a Fraction or a float or '' (blank for default which is internally set to None)
    temp_REST_NOTE_LINE_OFFSET = config["markmelgen"]["REST_NOTE_LINE_OFFSET"]
    if temp_REST_NOTE_LINE_OFFSET == "":
        REST_NOTE_LINE_OFFSET = None
    else:
        try:
            if not temp_REST_NOTE_LINE_OFFSET.isnumeric():
                REST_NOTE_LINE_OFFSET = Fraction(temp_REST_NOTE_LINE_OFFSET)
        except ValueError:
            print("ValueError", temp_REST_NOTE_LINE_OFFSET, " is not a number")
            # throw ValueError(temp_REST_NOTE_LINE_OFFSET + " is not a number")
    print("REST_NOTE_LINE_OFFSET", REST_NOTE_LINE_OFFSET)
    # copy markmelgen value to PER_SECTION values
    PER_SECTION_REST_NOTE_LINE_OFFSET = [
        REST_NOTE_LINE_OFFSET
    ] * PER_SECTION_LIST_LENGTH

    TEMPO_BPM = config["markmelgen"].getfloat("TEMPO_BPM")
    print("TEMPO_BPM", TEMPO_BPM)

    temp_TIME_SIG_WANTED = config["markmelgen"]["TIME_SIG_WANTED"]
    if temp_TIME_SIG_WANTED != "":
        TIME_SIG_WANTED = temp_TIME_SIG_WANTED
    print("TIME_SIG_WANTED", TIME_SIG_WANTED)

    # TONE_ASCENT
    TONE_ASCENT = config["markmelgen"].getboolean("TONE_ASCENT")
    print("TONE_ASCENT", TONE_ASCENT)

    TONE_ASCENT_MIN_INTERVAL = config["markmelgen"].getint("TONE_ASCENT_MIN_INTERVAL")
    print("TONE_ASCENT_MIN_INTERVAL", TONE_ASCENT_MIN_INTERVAL)
    if TONE_ASCENT_MIN_INTERVAL < 2:
        print("exit: Error TONE_ASCENT_MIN_INTERVAL < 2 ")
        sys.exit()

    TONE_ASCENT_TRIGGER_EVERY_N_TIMES = config["markmelgen"].getint(
        "TONE_ASCENT_TRIGGER_EVERY_N_TIMES"
    )
    print("TONE_ASCENT_TRIGGER_EVERY_N_TIMES", TONE_ASCENT_TRIGGER_EVERY_N_TIMES)

    # TONE_DESCENT
    TONE_DESCENT = config["markmelgen"].getboolean("TONE_DESCENT")
    print("TONE_DESCENT", TONE_DESCENT)

    TONE_DESCENT_MAX_INTERVAL = config["markmelgen"].getint("TONE_DESCENT_MAX_INTERVAL")
    print("TONE_DESCENT_MAX_INTERVAL", TONE_DESCENT_MAX_INTERVAL)
    if TONE_DESCENT_MAX_INTERVAL < 2:
        print("exit: Error TONE_DESCENT_MAX_INTERVAL < 2 ")
        sys.exit()

    TONE_DESCENT_TRIGGER_EVERY_N_TIMES = config["markmelgen"].getint(
        "TONE_DESCENT_TRIGGER_EVERY_N_TIMES"
    )
    print("TONE_DESCENT_TRIGGER_EVERY_N_TIMES", TONE_DESCENT_TRIGGER_EVERY_N_TIMES)

    temp_TONE_EQ = config["markmelgen"]["TONE_EQ"]
    print("string TONE_EQ", temp_TONE_EQ)

    if temp_TONE_EQ != "":
        # ast.literal_eval: Safely evaluate an expression node or a string containing a Python literal or container display.
        # The string or node provided may only consist of the following Python literal structures:
        # strings, bytes, numbers, tuples, lists, dicts, sets, booleans, None, bytes and sets.
        TONE_EQ = ast.literal_eval(temp_TONE_EQ)
        print("Python literal structure TONE_EQ", TONE_EQ)
        for tone_eq_num in range(0, len(TONE_EQ)):
            tone_name = TONE_EQ[tone_eq_num][0]
            tone_factor = TONE_EQ[tone_eq_num][1]
            print(
                "tone_eq_num=",
                tone_eq_num,
                "tone_name=",
                tone_name,
                "tone_factor=",
                tone_factor,
            )
            if tone_factor <= 0.0:
                print("exit: Error TONE_EQ factor <= 0.0")
                sys.exit()
    else:
        TONE_EQ = ""
    # input('Press Enter to continue...')

    TONE_INTERVAL = config["markmelgen"]["TONE_INTERVAL"]
    if (
        TONE_INTERVAL == "smallest"
        or TONE_INTERVAL == "largest"
        or TONE_INTERVAL == "random"
    ):
        print("TONE_INTERVAL", TONE_INTERVAL)
    else:
        print(
            "exit: Error TONE_INTERVAL = ",
            TONE_INTERVAL,
            " should be [smallest | largest | random]",
        )
        sys.exit()

    TONES_ON_KEY = config["markmelgen"].getboolean("TONES_ON_KEY")
    print("TONES_ON_KEY", TONES_ON_KEY)
    # copy markmelgen value to PER_SECTION values
    PER_SECTION_TONES_ON_KEY = [TONES_ON_KEY] * PER_SECTION_LIST_LENGTH

    TONES_OFF_KEY = config["markmelgen"].getboolean("TONES_OFF_KEY")
    print("TONES_OFF_KEY", TONES_OFF_KEY)

    TONE_PREV_INTERVAL = config["markmelgen"].getint("TONE_PREV_INTERVAL")
    print("TONE_PREV_INTERVAL", TONE_PREV_INTERVAL)
    PER_SECTION_TONE_PREV_INTERVAL = [TONE_PREV_INTERVAL] * PER_SECTION_LIST_LENGTH

    TONE_RANGE_BOTTOM = config["markmelgen"]["TONE_RANGE_BOTTOM"]
    print("TONE_RANGE_BOTTOM", TONE_RANGE_BOTTOM)
    # copy markmelgen value to PER_SECTION values
    PER_SECTION_TONE_RANGE_BOTTOM = [TONE_RANGE_BOTTOM] * PER_SECTION_LIST_LENGTH

    TONE_RANGE_TOP = config["markmelgen"]["TONE_RANGE_TOP"]
    print("TONE_RANGE_TOP", TONE_RANGE_TOP)
    # copy markmelgen value to PER_SECTION values
    PER_SECTION_TONE_RANGE_TOP = [TONE_RANGE_TOP] * PER_SECTION_LIST_LENGTH

    n_min = music21.note.Note()
    n_min.nameWithOctave = TONE_RANGE_BOTTOM
    n_max = music21.note.Note()
    n_max.nameWithOctave = TONE_RANGE_TOP

    if n_max.nameWithOctave < n_min.nameWithOctave:
        print("exit: Error in configuration file. TONE_RANGE_TOP < TONE_RANGE_BOTTOM.")
        sys.exit()

    TONE_ASCENT_TRIGGER = TONE_RANGE_BOTTOM
    TONE_DESCENT_TRIGGER = TONE_RANGE_TOP

    tone_range_semis = get_semitone_interval(n_min, n_max)
    print("tone_range in semitones", tone_range_semis)

    TONE_RANGE_MID = n_min.pitch.transpose(int(tone_range_semis / 2))
    print("TONE_RANGE_MID", TONE_RANGE_MID)

    if tone_range_semis < 12:
        print(
            "exit: Error tone range in semitones must be at least one octave (12 semitones)"
        )
        sys.exit()

    print("n_min.octave", n_min.octave, "n_max.octave", n_max.octave)

    tone_range_oct_min_str = ""
    for i in TONE_RANGE_BOTTOM:
        if i.isdigit() or i == "-":
            tone_range_oct_min_str = tone_range_oct_min_str + i

    tone_range_oct_max_str = ""
    for i in TONE_RANGE_TOP:
        if i.isdigit() or i == "-":
            tone_range_oct_max_str = tone_range_oct_max_str + i

    print(
        "tone_range_oct_min_str",
        tone_range_oct_min_str,
        "tone_range_oct_max_str",
        tone_range_oct_max_str,
    )
    if (int(tone_range_oct_min_str) > 9) or (int(tone_range_oct_max_str) > 9):
        print("exit: Error tone range max octave is 9.")
        sys.exit()

    if (int(tone_range_oct_min_str) < 0) or (int(tone_range_oct_max_str) < 0):
        print("exit: Error tone range min octave is 0.")
        sys.exit()

    # TONE_SCALE_NEW = json.loads(config.get("markmelgen", "TONE_SCALE_NEW"))
    # print('TONE_SCALE_NEW', TONE_SCALE_NEW)
    # for i in TONE_SCALE_NEW:
    #     if (i < 1) or (i > 7):
    #         print('exit: Error TONE_SCALE_NEW value < 1 or > 7')
    #         sys.exit()

    temp_TONE_SCALE_SET = config["markmelgen"]["TONE_SCALE_SET"]
    print("string TONE_SCALE_SET", temp_TONE_SCALE_SET)

    if temp_TONE_SCALE_SET != "":
        # ast.literal_eval: Safely evaluate an expression node or a string containing a Python literal or container display.
        # The string or node provided may only consist of the following Python literal structures:
        # strings, bytes, numbers, tuples, lists, dicts, sets, booleans, None, bytes and sets.
        TONE_SCALE_SET = ast.literal_eval(temp_TONE_SCALE_SET)
        # print('Python literal structure for TONE_SCALE_SET evaluated to:', TONE_SCALE_SET)
        for tone_num in range(0, len(TONE_SCALE_SET)):
            tone_name = TONE_SCALE_SET[tone_num]
            # print('tone_num=',tone_num,'tone_name=', tone_name)
            try:
                # temp_n = note.Note.name(tone_name)
                temp_n = note.Note(tone_name)
            # except music21.pitch.PitchException or music21.pitch.AccidentalException:
            except BaseException as err:
                print(f"Unexpected {err=}, {type(err)=}")
                print("exit: Error TONE_SCALE_SET tone_name", tone_name)
                sys.exit()
    else:
        TONE_SCALE_SET = ""
    PER_SECTION_TONE_SCALE_SET = [TONE_SCALE_SET] * PER_SECTION_LIST_LENGTH
    # input('Press Enter to continue...')

    TONE_SCALE_ON_ANHEMITONIC = config["markmelgen"].getboolean(
        "TONE_SCALE_ON_ANHEMITONIC"
    )
    print("TONE_SCALE_ON_ANHEMITONIC", TONE_SCALE_ON_ANHEMITONIC)

    TONE_SCALE_ON_HEMITONIC = config["markmelgen"].getboolean("TONE_SCALE_ON_HEMITONIC")
    print("TONE_SCALE_ON_HEMITONIC", TONE_SCALE_ON_HEMITONIC)


    temp_USE_STYLES = config["markmelgen"].get("USE_STYLES", "[]")  # Default to an empty list if not present
    print("string USE_STYLES", temp_USE_STYLES)

    if temp_USE_STYLES != "":
        try:
            # Safely evaluate the string to a Python list
            USE_STYLES = ast.literal_eval(temp_USE_STYLES)
            if not isinstance(USE_STYLES, list):
                raise ValueError("USE_STYLES must be a list of strings")
            # Ensure all elements are strings
            USE_STYLES = [str(style) for style in USE_STYLES]
        except (ValueError, SyntaxError) as err:
            print(f"Error parsing USE_STYLES: {err}")
            sys.exit("exit: Invalid USE_STYLES format in configuration file")
    else:
        USE_STYLES = []
    print("USE_STYLES", USE_STYLES)



    # list section keys
    # print('list(config[DEFAULT].keys()))')
    # print(list(config['DEFAULT'].keys()))
    # print('list(config[markmelgen].keys()))')
    # print(list(config['markmelgen'].keys()))

    # print('From the config file, list the song sections and optional song section specific Keys:')
    for sec in Config_Song_Section:
        # print('{:15} = {}'.format(sec.name, sec.value))
        # print(list(config[sec.name].keys()))
        # print('{:15} = {}'.format(sec.name, list(config[sec.name].keys())))
        pass

    # read SECTION data
    for sect in Config_Song_Section:
        # print(sect.name, sect.value)
        # if section exists in config:
        if not config.has_section(sect.name):
            print("exit: Error in config file. Missing [section name]", sect.name)
            sys.exit()
        else:
            # print('config.has_section',sect.name)
            # if option exists in section then read it

            if config.has_option(sect.name, "DURATION_SET"):
                temp_DURATION_SET = config[sect.name]["DURATION_SET"]
                # print('string DURATION_SET', temp_DURATION_SET)

                if temp_DURATION_SET != "":
                    # ast.literal_eval: Safely evaluate an expression node or a string containing a Python literal or container display.
                    # The string or node provided may only consist of the following Python literal structures:
                    # strings, bytes, numbers, tuples, lists, dicts, sets, booleans, None, bytes and sets.
                    try:
                        section_DURATION_SET = ast.literal_eval(temp_DURATION_SET)
                    except BaseException as err:
                        print(f"Unexpected {err=}, {type(err)=}")
                        print(
                            "exit: Error",
                            sect.name,
                            "section_DURATION_SET",
                            section_DURATION_SET,
                        )
                        sys.exit()

                    # print('Python literal structure for section_DURATION_SET strings evaluated to:', section_DURATION_SET,
                    #       type(section_DURATION_SET))
                    if not isinstance(section_DURATION_SET, list):
                        print("exit: section_DURATION_SET is not a list e.g. []")
                        sys.exit()
                    for dur_num in range(0, len(section_DURATION_SET)):
                        # print('dur type()', section_DURATION_SET[dur_num], type(section_DURATION_SET[dur_num]))
                        temp_dur = section_DURATION_SET[dur_num]
                        if is_number_an_integer(temp_dur):
                            print(
                                "exit: ValueError dur_frac",
                                temp_dur,
                                " is an integer e.g. 1. Should be a float e.g. 1.0",
                            )
                            sys.exit()
                        try:
                            if not temp_dur.isnumeric():
                                dur_frac = Fraction(temp_dur)
                                section_DURATION_SET[dur_num] = dur_frac
                        except ValueError:
                            print(
                                "exit: ValueError",
                                sect.name,
                                "dur_frac",
                                temp_dur,
                                " is not a number",
                            )
                            sys.exit()
                            # throw ValueError(temp_dur + " is not a number")
                        # print("dur_frac", dur_frac)
                else:
                    section_DURATION_SET = []
                print(
                    sect.name,
                    "DURATION_SET strings converted to Fractions:",
                    section_DURATION_SET,
                )
                PER_SECTION_DURATION_SET[sect.value] = section_DURATION_SET

            if config.has_option(sect.name, "DUR_LEAST"):
                # DUR_LEAST can be a Fraction or a float
                temp_DUR_LEAST = config[sect.name]["DUR_LEAST"]
                try:
                    if not temp_DUR_LEAST.isnumeric():
                        section_DUR_LEAST = Fraction(temp_DUR_LEAST)
                    if temp_DUR_LEAST == "0":
                        section_DUR_LEAST = 0
                except ValueError:
                    print(
                        "exit: ValueError",
                        sect.name,
                        "DUR_LEAST",
                        temp_DUR_LEAST,
                        " is not a number",
                    )
                    sys.exit()
                    # throw ValueError(temp_DUR_LEAST + " is not a number")
                print(sect.name, "DUR_LEAST", section_DUR_LEAST)
                PER_SECTION_DUR_LEAST[sect.value] = section_DUR_LEAST

            if config.has_option(sect.name, "DUR_LONGEST"):
                # DUR_LONGEST can be a Fraction or a float
                temp_DUR_LONGEST = config[sect.name]["DUR_LONGEST"]
                try:
                    if not temp_DUR_LONGEST.isnumeric():
                        section_DUR_LONGEST = Fraction(temp_DUR_LONGEST)
                    if temp_DUR_LONGEST == "0":
                        section_DUR_LONGEST = 0
                except ValueError:
                    print(
                        "exit: ValueError",
                        sect.name,
                        "DUR_LONGEST",
                        temp_DUR_LONGEST,
                        " is not a number",
                    )
                    sys.exit()
                    # throw ValueError(temp_DUR_LONGEST + " is not a number")
                print(sect.name, "DUR_LONGEST", section_DUR_LONGEST)
                PER_SECTION_DUR_LONGEST[sect.value] = section_DUR_LONGEST

            if config.has_option(sect.name, "DUR_PREV_DIFF"):
                section_DUR_PREV_DIFF = config[sect.name].getfloat("DUR_PREV_DIFF")
                if section_DUR_PREV_DIFF != 0 and section_DUR_PREV_DIFF <= 1:
                    print(
                        "exit: Error",
                        sect.name,
                        "section_DUR_PREV_DIFF != 0 and section_DUR_PREV_DIFF <= 1 ",
                    )
                    sys.exit()
                print(sect.name, "DUR_PREV_DIFF", section_DUR_PREV_DIFF)
                PER_SECTION_DUR_PREV_DIFF[sect.value] = section_DUR_PREV_DIFF

            if config.has_option(sect.name, "DUR_RATIONAL"):
                section_dur_rational = config[sect.name].getboolean("DUR_RATIONAL")
                print(sect.name, "DUR_RATIONAL", section_dur_rational)
                PER_SECTION_DUR_RATIONAL[sect.value] = section_dur_rational

            if config.has_option(sect.name, "DUR_TUPLET"):
                section_dur_tuplet = config[sect.name].getboolean("DUR_TUPLET")
                print(sect.name, "DUR_TUPLET", section_dur_tuplet)
                PER_SECTION_DUR_TUPLET[sect.value] = section_dur_tuplet

            if config.has_option(sect.name, "REST_NOTE_LINE_OFFSET"):
                # REST_NOTE_LINE_OFFSET can be a Fraction or a float or '' (blank for default which is internally set to None)
                temp_REST_NOTE_LINE_OFFSET = config[sect.name]["REST_NOTE_LINE_OFFSET"]
                if temp_REST_NOTE_LINE_OFFSET == "":
                    section_REST_NOTE_LINE_OFFSET = None
                else:
                    try:
                        if not temp_REST_NOTE_LINE_OFFSET.isnumeric():
                            section_REST_NOTE_LINE_OFFSET = Fraction(
                                temp_REST_NOTE_LINE_OFFSET
                            )
                        if temp_REST_NOTE_LINE_OFFSET == "0":
                            section_REST_NOTE_LINE_OFFSET = 0
                    except ValueError:
                        print(
                            "exit: ValueError REST_NOTE_LINE_OFFSET",
                            temp_REST_NOTE_LINE_OFFSET,
                            " in section",
                            sect.name,
                            " is not a number",
                        )
                        sys.exit()
                print(sect.name, "REST_NOTE_LINE_OFFSET", section_REST_NOTE_LINE_OFFSET)
                PER_SECTION_REST_NOTE_LINE_OFFSET[sect.value] = (
                    section_REST_NOTE_LINE_OFFSET
                )

            if config.has_option(sect.name, "TONES_ON_KEY"):
                section_tones_on_key = config[sect.name].getboolean("TONES_ON_KEY")
                print(sect.name, "TONES_ON_KEY", section_tones_on_key)
                PER_SECTION_TONES_ON_KEY[sect.value] = section_tones_on_key

            if config.has_option(sect.name, "TONE_PREV_INTERVAL"):
                section_TONE_PREV_INTERVAL = config[sect.name].getint(
                    "TONE_PREV_INTERVAL"
                )
                print(sect.name, "TONE_PREV_INTERVAL", section_TONE_PREV_INTERVAL)
                PER_SECTION_TONE_PREV_INTERVAL[sect.value] = section_TONE_PREV_INTERVAL

            if config.has_option(sect.name, "TONE_RANGE_BOTTOM"):
                section_tone_range_bottom = config[sect.name]["TONE_RANGE_BOTTOM"]
                print(sect.name, "TONE_RANGE_BOTTOM", section_tone_range_bottom)
                PER_SECTION_TONE_RANGE_BOTTOM[sect.value] = section_tone_range_bottom

            if config.has_option(sect.name, "TONE_RANGE_TOP"):
                section_tone_range_top = config[sect.name]["TONE_RANGE_TOP"]
                print(sect.name, "TONE_RANGE_TOP   ", section_tone_range_top)
                PER_SECTION_TONE_RANGE_TOP[sect.value] = section_tone_range_top

                n_min = music21.note.Note()
                n_min.nameWithOctave = section_tone_range_bottom
                n_max = music21.note.Note()
                n_max.nameWithOctave = section_tone_range_top

                # if n_max.nameWithOctave < n_min.nameWithOctave:
                if n_max < n_min:
                    print(
                        "exit: Error in configuration file. TONE_RANGE_TOP < TONE_RANGE_BOTTOM. section name",
                        sect.name,
                    )
                    sys.exit()

            if config.has_option(sect.name, "TONE_SCALE_SET"):
                temp_TONE_SCALE_SET = config[sect.name]["TONE_SCALE_SET"]
                print(sect.name, "string TONE_SCALE_SET", temp_TONE_SCALE_SET)

                if temp_TONE_SCALE_SET != "":
                    # ast.literal_eval: Safely evaluate an expression node or a string containing a Python literal or container display.
                    # The string or node provided may only consist of the following Python literal structures:
                    # strings, bytes, numbers, tuples, lists, dicts, sets, booleans, None, bytes and sets.
                    section_TONE_SCALE_SET = ast.literal_eval(temp_TONE_SCALE_SET)
                    # print('Python literal structure for TONE_SCALE_SET evaluated to:', section_TONE_SCALE_SET)
                    for tone_num in range(0, len(section_TONE_SCALE_SET)):
                        tone_name = section_TONE_SCALE_SET[tone_num]
                        # print('tone_num=',tone_num,'tone_name=', tone_name)
                        try:
                            # temp_n = note.Note.name(tone_name)
                            temp_n = note.Note(tone_name)
                        # except music21.pitch.PitchException or music21.pitch.AccidentalException:
                        except BaseException as err:
                            print(f"Unexpected {err=}, {type(err)=}")
                            print(
                                "exit: Error",
                                sect.name,
                                "TONE_SCALE_SET tone_name",
                                tone_name,
                            )
                            sys.exit()
                else:
                    section_TONE_SCALE_SET = ""

                PER_SECTION_TONE_SCALE_SET[sect.value] = section_TONE_SCALE_SET

    # print the PER_SECTION lists
    print("")
    print(
        "PER_SECTION values        [intro, verse, prechorus, chorus, solo, bridge, outro, default]"
    )
    print(
        "========================================================================================="
    )

    print("PER_SECTION_DURATION_SET ", PER_SECTION_DURATION_SET)
    print("PER_SECTION_DUR_LEAST    ", PER_SECTION_DUR_LEAST)
    print("PER_SECTION_DUR_LONGEST  ", PER_SECTION_DUR_LONGEST)
    print("PER_SECTION_DUR_PREV_DIFF", PER_SECTION_DUR_PREV_DIFF)
    print("PER_SECTION_DUR_RATIONAL ", PER_SECTION_DUR_RATIONAL)
    print("PER_SECTION_DUR_TUPLET   ", PER_SECTION_DUR_TUPLET)
    print("PER_SECTION_REST_NOTE_LINE_OFFSET    ", PER_SECTION_REST_NOTE_LINE_OFFSET)
    print("PER_SECTION_TONES_ON_KEY      ", PER_SECTION_TONES_ON_KEY)
    print("PER_SECTION_TONE_PREV_INTERVAL", PER_SECTION_TONE_PREV_INTERVAL)
    print("PER_SECTION_TONE_RANGE_BOTTOM ", PER_SECTION_TONE_RANGE_BOTTOM)
    print("PER_SECTION_TONE_RANGE_TOP    ", PER_SECTION_TONE_RANGE_TOP)
    print("PER_SECTION_TONE_SCALE_SET    ", PER_SECTION_TONE_SCALE_SET)

    print(
        "========================================================================================="
    )
    print(f"Configuration file loaded: {CONF_FILENAME}")
    print("")
    print("")
    print("")
    print("")
    print("")
    # input('Press Enter to continue...')

    # Bind reference to final parameter values.

    if args.display_graphs == True:
        DISPLAY_GRAPHS = args.display_graphs
    if args.display_html == True:
        DISPLAY_HTML = args.display_html
    if args.display_mxl == True:
        DISPLAY_MXL = args.display_mxl
    if args.display_kar == True:
        DISPLAY_KAR = args.display_kar

    if args.list_styles:
        # In MarkMelGen.py, after the config is loaded (e.g., after config.read(CONF_FILENAME))
        # print(f"INPUT_STYLE_PATH from config: {INPUT_STYLE_PATH}")

        # List the styles and exit
        print(f"Processing argument: --list-styles (value: {args.list_styles})")
        print(f"Available styles in {INPUT_STYLE_PATH} :")
        style_list = []
        try:
            for style_dir in os.listdir(INPUT_STYLE_PATH):
                if os.path.isdir(os.path.join(INPUT_STYLE_PATH, style_dir)):
                    print(f"- {style_dir}")
                    style_list.append(style_dir)
        except FileNotFoundError:
            print(f"Error: Style directory not found at {INPUT_STYLE_PATH}")
        if style_list:
            print("\nTo configure the use styles, copy & paste the line below to your .conf file :")
            print(f"USE_STYLES=[{','.join(repr(style) for style in style_list)}]")
            print("\nTo override .conf styles, copy & paste the line below to your -o override :")
            print(f"-o markmelgen.USE_STYLES=[{','.join(repr(style) for style in style_list)}]")
        sys.exit()

    if args.create_style:
        print(f"Processing argument: --create_style (value: {args.create_style})")
        create_style(args.create_style, DISPLAY_HTML, INPUT_STYLE_PATH)
        sys.exit(0)

    # Add a flag to track the override
    duration_set_override = False

    # Override with command-line arguments
    if args.override:
        logger.debug(f"args.override: {args.override}")
        for override_arg in args.override:
            logger.debug(f"override_arg: {override_arg}")
            try:
                section_key, value_str = override_arg.split("=", 1)
                section, key = section_key.split(".", 1)
                value = parse_value(value_str)

                if not config.has_section(section):
                    config.add_section(section)
                config.set(section, key, str(value))  # configparser only stores strings, so we convert back to string.
                # logger.info(f"Overriding: {section}.{key} with {value} (type: {type(value)})")

                # Check if the override is for USE_STYLES
                if section == "markmelgen" and key == "USE_STYLES":
                    try:
                        # If value is already a list, use it directly
                        if isinstance(value, list):
                            temp_USE_STYLES = value  # Directly assign the list
                        else:
                            # Safely evaluate the string to a Python list
                            temp_USE_STYLES = ast.literal_eval(value)
                        
                        # Ensure the result is a list of strings
                        if not isinstance(temp_USE_STYLES, list):
                            raise ValueError("USE_STYLES must be a list of strings")
                        USE_STYLES = [str(style) for style in temp_USE_STYLES]
                        logger.debug(f"USE_STYLES overridden to: {USE_STYLES}")
                    except (ValueError, SyntaxError) as err:
                        logger.error(f"Error parsing overridden USE_STYLES: {err}")
                        sys.exit("exit: Invalid USE_STYLES format in override argument")

                # Set the flag if the override is for DURATION_SET
                if section == "markmelgen" and key == "DURATION_SET":
                    duration_set_override = True
                    logger.debug(f"duration_set_override: {duration_set_override}")

            except ValueError:
                logger.info(
                    f"Invalid override format: {override_arg}. Use 'section.key=value'."
                )
            except configparser.NoSectionError:
                logger.info(f"Invalid section: {section} in {override_arg}.")
            except configparser.NoOptionError:
                logger.info(f"Invalid key: {key} in {override_arg}.")

        # Execute the assignment based on the flag
        if duration_set_override:
            PER_SECTION_DURATION_SET = [DURATION_SET] * PER_SECTION_LIST_LENGTH
            logger.debug(f"duration_set_override DURATION_SET: {DURATION_SET} PER_SECTION_DURATION_SET: {PER_SECTION_DURATION_SET}")

        # 4. Access the settings (example - showing how to get different types)
        lyrics_path = config.get("paths", "INPUT_LYRICS_PATH", fallback="")
        # If the path is blank, use the current working directory.
        # if not lyrics_path:
        #     lyrics_path = os.getcwd()

        INPUT_LYRICS_PATH = config["paths"]["INPUT_LYRICS_PATH"]
        INPUT_LYRICS_FILENAME = config["filenames"]["INPUT_LYRICS_FILENAME"]
        INPUT_LYRICS_FULLY_QUALIFIED = INPUT_LYRICS_PATH + INPUT_LYRICS_FILENAME
        TEMPO_BPM = config["markmelgen"].getfloat("TEMPO_BPM")
        TIME_SIG_WANTED = config["markmelgen"]["TIME_SIG_WANTED"]
        DISPLAY_GRAPHS = config["markmelgen"].getboolean("DISPLAY_GRAPHS")

        duration_set_str = config.get("markmelgen", "DURATION_SET", fallback="[]")
        DURATION_SET = parse_value(duration_set_str)
        temp_DURATION_SET = get_duration_set(DURATION_SET)  # Convert to list of Fractions
        PER_SECTION_DURATION_SET = [temp_DURATION_SET] * PER_SECTION_LIST_LENGTH

        logger.info(f"Using lyrics path: {INPUT_LYRICS_PATH}")
        logger.info(f"Using lyrics filename: {INPUT_LYRICS_FILENAME}")
        logger.info(f"Using lyrics fully qualified: {INPUT_LYRICS_FULLY_QUALIFIED}")
        logger.info(f"Using tempo (BPM): {TEMPO_BPM}")
        logger.info(f"Using time sig wanted: {TIME_SIG_WANTED}")
        logger.info(f"Using Display graphs: {DISPLAY_GRAPHS}")
        logger.info(f"Using Duration set: {DURATION_SET} (type: {type(DURATION_SET)})")
        logger.info(f"Using Duration set (PER_SECTION): {PER_SECTION_DURATION_SET}")  
        logger.info(f"Using USE_STYLES: {USE_STYLES}")

    return # end of get_config()

if __name__ == "__main__":

    get_config()

    # input('After get_config() Press Enter to continue...')

    main()
