#!/usr/bin/env python
# -*- coding: utf-8 -*-
# song_section_values.py
#
# which given a compressed musicxml file (.mxl) with a song melody stave and section names as stave text,
# Note: section_name_matches = ['intro', 'verse', 'prechorus', 'chorus', 'solo', 'bridge', 'outro']
# calculates and outputs the text for MarkMelGen.conf file song section values [song_intro] ... [song_outro]
#
# free and open-source software, Paul Wardley Davies, see MarkMelGen/license.txt

# usage: song_section_values.py [-h] [-m MXLFILE]
#
# optional arguments:
#   -h, --help            show this help message and exit
#   -m MXLFILE, --music MXLFILE
#                         music file path, relative to current working directory e.g. input/music/sectioned/music.mxl
#                         MusicXML files are .mxl for compressed files.
#                         The MuiscXML file must contain staff text words to identify the section start point:
#                         'intro', 'verse', 'prechorus', 'chorus', 'solo', 'bridge', 'outro'
#                         'In MuseScore, to create staff text choose a location by selecting a note or rest and then use the menu option Add → Text → Staff Text, or use the shortcut Ctrl+T ',

# standard libraries
import argparse
import bisect
from fractions import Fraction
import math
import music21
from music21 import *
import os
import re
import sys

class SongSectionValues:
    """
    A class that stores SongSectionValues
    such as duration types and tone range in a section of a song.
    Methods include __init__ and update with a note
    """
    # class variables shared by all instances
    number_of_song_sections = 0
    song_key = None
    TIME_SIG_WANTED = '3/4'
    songTimeSig = None

    structure_by_name_long = ''
    structure_by_name = ''
    structure_by_name_initial = ''
    structure_by_letter  = ''

    section_letter = {} # dictionary to hold section to letter mapping e.g. {'verse': 'A', 'chorus': 'B'}
    letter_current = 'A'

    def increment_sections(self):
        SongSectionValues.number_of_song_sections += 1

    # class instantiation automatically invokes __init__
    def __init__(self, song_key):
        """
        takes song_key
        and initialises section data
        """

        # update class variables
        SongSectionValues.song_key = song_key

        # set instance variable unique to each instance
        self.dur_prev = 0
        self.note_prev = None

        self.DURATION_SET = []
        self.DUR_PREV_DIFF = 0
        self.DUR_RATIONAL = True
        self.DUR_TUPLET = False
        self.DUR_LEAST = 99.0
        self.DUR_LONGEST = 0.01
        self.REST_NOTE_LINE_OFFSET = None
        self.TONES_ON_KEY = True
        self.TONE_PREV_INTERVAL = 0
        self.TONE_RANGE_BOTTOM = 'B9'
        self.TONE_RANGE_TOP = 'C0'
        self.TONE_SCALE_SET = []
        print('# ------------------------------------------------------------------------------------------------------')

    def set_time_sig(self, songTimeSig):
        """
        given time signature update class variable
        """
        # update class variable
        SongSectionValues.songTimeSig = songTimeSig


    def set_section(self, name):
        """
        given a section name
        update the class and instance variables
        """

        # update class variables
        self.increment_sections()

        SongSectionValues.structure_by_name_long = SongSectionValues.structure_by_name_long + str(name) + '-'
        SongSectionValues.structure_by_name = SongSectionValues.structure_by_name + truncate_section(name) + '-'
        SongSectionValues.structure_by_name_initial = SongSectionValues.structure_by_name_initial + truncate_section(name)[0]

        # if section not in section_letter dictionary: add to dictionary, increment value
        if truncate_section(name) not in SongSectionValues.section_letter:
            SongSectionValues.section_letter[truncate_section(name)] = SongSectionValues.letter_current
            SongSectionValues.letter_current = chr((ord(SongSectionValues.letter_current) - ord('A') + 1) % 26 + ord('A'))
        # add section letter to structure_by_letter
        SongSectionValues.structure_by_letter = SongSectionValues.structure_by_letter + SongSectionValues.section_letter[truncate_section(name)]

        # set instance variable unique to each instance
        self.name = name


    def update(self, n, first_note_of_section):
        """
        if triplet: DUR_TUPLET = True
        if note.dur < DUR_LEAST: DUR_LEAST = note.dur
        if note.dur > DUR_LONGEST: DUR_LONGEST = note.dur
        if note not scale note: TONES_ON_KEY = True
        if note.nameWithOctave < TONE_RANGE_BOTTOM: TONE_RANGE_BOTTOM = note.nameWithOctave
        if note.nameWithOctave > TONE_RANGE_TOP: TONE_RANGE_TOP = note.nameWithOctave
        """

        # complex durations
        c1_6 = Fraction(1, 6)
        c1_3 = Fraction(1, 3)
        c2_3 = Fraction(2, 3)
        c4_3 = Fraction(4, 3)
        c8_3 = Fraction(8, 3)

        if first_note_of_section:
            # update (only on first note) REST_NOTE_LINE_OFFSET
            prev_measure_offset = (math.trunc(n.offset / SongSectionValues.songTimeSig.beatCount) ) * SongSectionValues.songTimeSig.beatCount
            note_offset_from_start_measure = n.offset - prev_measure_offset
            # print('n.offset',n.offset,'ts.beatCount',ts.beatCount,'prev_measure_offset',prev_measure_offset,'note_offset_from_start_measure',note_offset_from_start_measure )
            self.REST_NOTE_LINE_OFFSET = note_offset_from_start_measure
            first_note_of_section = False

        else: # notes other than first note

            # update DUR_PREV_DIFF, TONE_PREV_INTERVAL

            # from MarMelGen.conf:
            # DUR_PREV_DIFF - compare duration with previous duration, e.g. where 2, duration is >= 1/2 previous and <= 2 x previous etc ,
            # where 0 and <= 1, do not compare with previous duration.

            # if this_dur_Prev_diff is bigger, update DUR_PREV_DIFF
            bigger = False
            if self.dur_prev != 0:  # do not work out for first note
                if self.dur_prev < n.duration.quarterLength:  # previous note is shorter e.g. dur_prev = 1.0 <  n = 2.0
                    this_dur_Prev_diff = (float(n.duration.quarterLength)) / (float(Fraction(self.dur_prev)))
                    # this_dur_Prev_diff =  e.g. (n = 2.0) / dur_prev = 1.0
                    if this_dur_Prev_diff > self.DUR_PREV_DIFF: bigger = True
                if self.dur_prev > n.duration.quarterLength:  # previous note is longer e.g. dur_prev = 4.0 <  n = 2.0
                    this_dur_Prev_diff = (float(Fraction(self.dur_prev)) / float(
                        n.duration.quarterLength))  # this_dur_Prev_diff =  e.g. (n = 2.0) * dur_prev = 4.0
                    if this_dur_Prev_diff > self.DUR_PREV_DIFF: bigger = True
            if bigger: self.DUR_PREV_DIFF = this_dur_Prev_diff

            # update TONE_PREV_INTERVAL: calc semitone_interval_with_prev_note for
            aInterval = interval.Interval(self.note_prev, n)
            AIntSemi = abs(aInterval.semitones)
            if AIntSemi > self.TONE_PREV_INTERVAL: self.TONE_PREV_INTERVAL = AIntSemi

        # any note update:
        # DURATION_SET, DUR_RATIONAL, DUR_TUPLET, DUR_LEAST, DUR_LONGEST, TONES_ON_KEY, TONE_RANGE_BOTTOM, TONE_RANGE_TOP
        # dur_prev
        duration_found = False
        for dur_from_set in self.DURATION_SET:
            if Fraction(n.duration.quarterLength) == Fraction(dur_from_set):
                duration_found = True
        if not duration_found:
            bisect.insort(self.DURATION_SET, str(n.duration.quarterLength))

        # if triplet: DUR_TUPLET = True
        if ((n.duration.quarterLength == c1_6) or (n.duration.quarterLength == c1_3) or (n.duration.quarterLength == c2_3)):
            self.DUR_TUPLET = True
            self.DUR_RATIONAL = False
        # if note.dur < DUR_LEAST: DUR_LEAST = note.dur
        if n.duration.quarterLength < self.DUR_LEAST: self.DUR_LEAST = n.duration.quarterLength
        # if note.dur > DUR_LONGEST: DUR_LONGEST = note.dur
        if n.duration.quarterLength > self.DUR_LONGEST: self.DUR_LONGEST = n.duration.quarterLength

        # if note not scale note: TONES_ON_KEY = True
        if self.song_key.mode == 'major':
            sc = scale.MajorScale(self.song_key.tonic.name)
        else:
            sc = scale.MinorScale(self.song_key.tonic.name)
        scale_degree = sc.getScaleDegreeFromPitch(n)
        if scale_degree == None:
            self.TONES_ON_KEY = False

        # if note.nameWithOctave < TONE_RANGE_BOTTOM: TONE_RANGE_BOTTOM = note.nameWithOctave
        # if n.nameWithOctave < self.TONE_RANGE_BOTTOM: self.TONE_RANGE_BOTTOM = n.nameWithOctave
        # if note.nameWithOctave > TONE_RANGE_TOP: TONE_RANGE_TOP = note.nameWithOctave
        # Following gave False with next line: A5 > G5, B5 > G5, C6 > G5 (assume bug with music21)
        # if n.nameWithOctave > self.TONE_RANGE_TOP: self.TONE_RANGE_TOP = n.nameWithOctave

        new_note = note.Note()
        new_note.nameWithOctave = n.nameWithOctave
        min_note = note.Note()
        min_note.nameWithOctave = self.TONE_RANGE_BOTTOM
        max_note = note.Note()
        max_note.nameWithOctave = self.TONE_RANGE_TOP

        if note.Note(n.nameWithOctave) < note.Note(min_note.nameWithOctave):
            self.TONE_RANGE_BOTTOM = n.nameWithOctave

        if note.Note(n.nameWithOctave) > note.Note(max_note.nameWithOctave):
            self.TONE_RANGE_TOP = n.nameWithOctave

        # TONE_SCALE_SET
        tone_found = False
        for tone_from_set in self.TONE_SCALE_SET:
            if pitch.Pitch(n.name).ps == pitch.Pitch(tone_from_set).ps:
                tone_found = True
        if not tone_found:
            bisect.insort(self.TONE_SCALE_SET, str(n.name))

        self.dur_prev = n.duration.quarterLength  # update self.dur_prev
        self.note_prev = n


    def print(self):
        print('')
        print('# section', self.number_of_song_sections, 'name      =', self.name)

        truncated_section_name = truncate_section(self.name)
        printable_name = '[song_' + truncated_section_name + ']'
        print(printable_name)

        print('DURATION_SET =', self.DURATION_SET)
        print('DUR_LEAST =', self.DUR_LEAST)
        print('DUR_LONGEST =', self.DUR_LONGEST)
        print('DUR_PREV_DIFF =', self.DUR_PREV_DIFF)
        print('DUR_RATIONAL =', self.DUR_RATIONAL)
        print('DUR_TUPLET =', self.DUR_TUPLET)
        print('REST_NOTE_LINE_OFFSET =', self.REST_NOTE_LINE_OFFSET)
        print('TONES_ON_KEY =', self.TONES_ON_KEY)
        print('TONE_PREV_INTERVAL =', self.TONE_PREV_INTERVAL)
        print('TONE_RANGE_BOTTOM =', self.TONE_RANGE_BOTTOM)
        print('TONE_RANGE_TOP =', self.TONE_RANGE_TOP)
        print('TONE_SCALE_SET =', self.TONE_SCALE_SET)
        print('')

    def print_class_variable(self):
        print('# ------------------------------------------------------------------------------------------------------')
        print('# number_of_sections_found =', SongSectionValues.number_of_song_sections)
        print('# song structure:')
        print('# long    =', SongSectionValues.structure_by_name_long[:-1])
        print('# name    =', SongSectionValues.structure_by_name[:-1])
        print('# initial =', self.structure_by_name_initial)
        print('# letter  =', self.structure_by_letter)

def is_section(content):
    """
    content_is_section = False
    if content starts with section_name: content_is_section = True
    return content_is_section
    """
    section_name_matches = ['Intro', 'Verse', 'Prechorus', 'Chorus', 'Solo', 'Bridge', 'Outro',
                            'intro', 'verse', 'prechorus', 'chorus', 'solo', 'bridge', 'outro',
                            'INTRO', 'VERSE', 'PRECHORUS', 'CHORUS', 'SOLO', 'BRIDGE', 'OUTRO', 'preChorus']
    content_is_section = False
    # if content.startswith('intro',  'verse', 'prechorus', 'chorus', 'solo', 'bridge', 'outro'):
    if any(x in content for x in section_name_matches):
        content_is_section = True
    return content_is_section

def truncate_section(name):
    """
    given a long section name e.g. VERSE_1
    return short name e.g. verse
    """
    section_name = ['intro', 'verse', 'prechorus', 'chorus', 'solo', 'bridge', 'outro']
    # for each section_name
    #   if section_name is a case-insensitive match to the beginning of the string
    #       return section_name
    for sec in  section_name:
        if name.lower().startswith(sec):
            return sec


def show_histograms(score, label):
    """
    function that shows histograms of the score with the supplied label
    """

    # show a histogram of output pitch space.
    p = graph.plot.HistogramPitchSpace(score)
    p.title = label + ' - histogram'
    p.run()  # with defaults and proper configuration, will open graph

    # show a histogram of pitch class
    p = graph.plot.HistogramPitchClass(score)
    # p.title = label + ' - histogram-pitchClass-count'
    p.title = label + ' - histogram'
    p.run()  # with defaults and proper configuration, will open graph

    # show a histogram of quarter lengths
    p = graph.plot.HistogramQuarterLength(score)
    p.title = label + ' - histogram'
    p.run()  # with defaults and proper configuration, will open graph

    # show a A graph of events, sorted by pitch space, over time
    p = graph.plot.HorizontalBarPitchSpaceOffset(score)
    p.title = label + ' - graph'
    p.run()  # with defaults and proper configuration, will open graph


def main():
    """
    parse command line arguments
    read mxl
    normalise stream
    write normalised stream

    for each stream element
        if time sig: read time sig
        if text: read section name
            if not first section:
                song_section_values.print()
            init SongSectionValues
        if note: read note: song_section_values.update()
    song_section_values.print()
    """

    # Specify command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mxlfile',
                        help='music file path, relative to current working directory e.g. input/music/sectioned/music.mxl '
                            '(MusicXML files with the extension .mxl are compressed files). '
                            'The MusicXML file must contain staff text words at the section start note: '
                            'INTRO, VERSE, PRECHORUS, CHORUS, SOLO, BRIDGE or OUTRO. '
                            'In MuseScore, to create staff text: select section start note and then use the menu option Add → Text → Staff Text, or use the shortcut Ctrl+T. ',
                        default='',
                        type=str)

    # print the help message only if no arguments are supplied on the command line
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Parse command line arguments.
    args = parser.parse_args()
    print('')
    print("mxlfile fully qualified      :", args.mxlfile)

    # read mxl
    a_song = music21.converter.parse(args.mxlfile)
    # a_song.show('text')

    # normalise stream
    # analyze the key of the input song
    song_key = a_song.analyze('key')  # music21 generic algorithm for key finding
    print('Input song raw song_key.tonic.name, song_key.mode = ', song_key.tonic.name,
          song_key.mode)  # # e.g. song_key.tonic.name, song_key.mode =  B major or D minor

    if (song_key.tonic.name == 'C' and song_key.mode == 'major') or (
            song_key.tonic.name == 'A' and song_key.mode == 'minor'):
        print('No need to normalise as already normal C major or A minor.')
        song_transpose_interval = 0
    else:
        print('Need to normalise to C major or A minor.')
        # if minor find interval to A
        if song_key.mode == 'minor':
            song_transpose_interval = interval.Interval(song_key.tonic, pitch.Pitch('A'))
        else:  # song is major, find interval to C
            song_transpose_interval = interval.Interval(song_key.tonic, pitch.Pitch('C'))
        a_song = a_song.transpose(song_transpose_interval)

    # analyze the key of the transposed input song
    song_key = a_song.analyze('key')  # music21 generic algorithm for key finding
    print('Transposed (if required) input song interval song_key.tonic.name, song_key.mode = ',
          song_transpose_interval, song_key.tonic.name,
          song_key.mode)  # # e.g. song_key.tonic.name, song_key.mode =  C major or A minor

    # a_song.show('text')

    # remove file extension from filename, normalise filename and add file extension
    mxlfile_basename = os.path.basename(args.mxlfile)
    mxlfile_normalised_name = os.path.splitext(mxlfile_basename)[0] + '_in_C.mxl'

    # get path without filename e.g.
    # 1. blank if no path (file in cwd) mxlfile_path               :
    # 2. if has path                    mxlfile_path               : private/input/music/sectioned
    mxlfile_path = os.path.dirname(args.mxlfile)
    # print("mxlfile_path                 :", mxlfile_path)
    mxlfile_normalised_name_path = os.curdir + os.sep + mxlfile_path + os.sep + mxlfile_normalised_name
    print("mxlfile_normalised_output      :", mxlfile_normalised_name_path)

    # write normalised stream
    a_song.write(fp=mxlfile_normalised_name_path) # write normalised score to musicxml file

    print('Reading mxlfile_normalised...')
    print('Looking for sections: intro, verse, prechorus, chorus, solo, bridge, or outro... ')

    found_time_signature = False
    first_section_found = False
    first_note_of_section = True
    songTimeSig = None

    song_section_values = SongSectionValues(song_key)

    # for each element in stream
    for n in a_song.flat:

        if type(n) == music21.meter.TimeSignature:
            song_section_values.set_time_sig(n)

            # get the time signatures
            # first = True
            # for tSig in a_song.getTimeSignatures():
            #     if first:
            #         songTimeSig = tSig
                    # print('First Time Signature:',
                    #       songTimeSig)  # eg First Time Signature: <music21.meter.TimeSignature 4/4>
                    # ts = songTimeSig  # first time signature
                    # print('Time signature numerator =', ts.numerator, ' denominator =', ts.denominator, ' beatCount',
                    #       ts.beatCount)
                    # found_time_signature = True
                    # song_section_values.set_time_sig(songTimeSig)
                    # first = False
                # else:
                #     print('Other Time Signature:', tSig)

        if type(n) == music21.expressions.TextExpression:
            # print('music21.expressions.TextExpression')
            if is_section(n.content):
                first_note_of_section = True
                if first_section_found:
                    song_section_values.print()

                # if found_time_signature:
                #     song_section_values = SongSectionValues(song_key, songTimeSig)
                song_section_values = SongSectionValues(song_key)

                # else:
                #     print('exit: Error, edit mxl and insert Time Signature before first section name')
                #     sys.exit()
                #     #song_section_values = SongSectionValues(song_key, songTimeSig)
                #     pass

                song_section_values.set_section(n.content)

                if not first_section_found:
                    first_section_found = True

        # if note: update song_section_values
        if type(n) == music21.note.Note:
            # if type(n) != music21.note.Rest:
            if not n.duration.isGrace:
                song_section_values.update(n, first_note_of_section)
                if first_note_of_section == True: first_note_of_section = False

    # print data for last section
    if first_section_found:
        song_section_values.print()
    # if (number_of_sections_found) == 0:
    if not first_section_found:
        print('')
        print('Warning: Error number_of_sections_found = 0 ##########################################################')
        print('')
        print('MusicXML files are .mxl for compressed files')
        print('The MusicXML file must contain staff text words to identify the section start point: ')
        print('intro, verse, prechorus, chorus, solo, bridge or outro. ')
        print('In MuseScore, to create staff text choose a location by selecting a note or rest and then use the menu option Add → Text → Staff Text, or use the shortcut Ctrl+T.')

    else:
        song_section_values.print_class_variable()

    # show graphs
    label = 'Input ' + mxlfile_normalised_name
    show_histograms(a_song, label)

if __name__ == '__main__':

    main()
