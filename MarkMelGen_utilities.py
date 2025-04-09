#!/usr/bin/env python
# -*- coding: utf-8 -*-
# MarkMelGen_utilities.py
#
# common data and functions for MarkMelGen
#
# free and open-source software, Paul Wardley Davies, see license.txt

import ast
import copy
import datetime
import json
import math
import mido
import music21
import re
import sys
import traceback

from fractions import Fraction
from logging_config import logger
from mido import *
from music21 import *
from music21 import meter

MARKMELGEN_VERSION = "2.0.0"


def analyze_melody_beats(melody_stream, strip=True):
    """
    Analyze a melody for the number of on beat notes, offbeat notes,
    on beat cadence notes, offbeat cadence notes, minimum and maximum duration,
    and minimum and maximum beat placement.

    Args:
        melody_stream (music21.stream.Stream): The melody stream to analyze.
        strip (bool): Whether to strip the melody of ties. Default is True.

    Returns:
        dict: A dictionary containing the analysis results.
    """
    analysis_results = {
        "on_beat_notes": 0,
        "offbeat_notes": 0,
        "on_beat_cadence_notes": 0,
        "offbeat_cadence_notes": 0,
        "min_duration": float("inf"),
        "max_duration": float("-inf"),
        "min_beat_placement": float("inf"),
        "max_beat_placement": float("-inf"),
    }

    # Check if time signature is found and valid
    time_signatures = melody_stream.getTimeSignatures()
    if not time_signatures:
        print("Error: Time signature not found.")
        sys.exit(1)

    ts = time_signatures[0]  # Assuming a single time signature for simplicity

    # Flatten the score
    flat_melody = melody_stream.flatten()

    # Remove ties and merge tied notes if strip is True
    if strip:
        melody_stripped = flat_melody.stripTies()
    else:
        melody_stripped = flat_melody

    for i, element in enumerate(melody_stripped.notesAndRests):
        if isinstance(element, note.Note):
            # Check if the note is on the beat
            if is_note_on_beat(element, ts):
                analysis_results["on_beat_notes"] += 1
                # Check for cadence note (followed by a rest)
                if i < len(melody_stripped.notesAndRests) - 1 and isinstance(
                    melody_stripped.notesAndRests[i + 1], note.Rest
                ):
                    analysis_results["on_beat_cadence_notes"] += 1
            else:
                analysis_results["offbeat_notes"] += 1
                # Check for cadence note (followed by a rest)
                if i < len(melody_stripped.notesAndRests) - 1 and isinstance(
                    melody_stripped.notesAndRests[i + 1], note.Rest
                ):
                    analysis_results["offbeat_cadence_notes"] += 1

            # Update minimum and maximum duration
            if element.quarterLength < analysis_results["min_duration"]:
                analysis_results["min_duration"] = element.quarterLength
            if element.quarterLength > analysis_results["max_duration"]:
                analysis_results["max_duration"] = element.quarterLength

            # Update minimum and maximum beat placement
            # beat_placement = element.offset % ts.beatDuration.quarterLength
            beat_placement = fractional_part_as_fraction(element.offset, ts)

            if beat_placement >= 1.0:

                logger.warning(
                    f"analyze_melody_beats beat_placement >= 1.0 {beat_placement} element.offset {element.offset} ts {ts}"
                )
                # print(f'analyze_melody_beats beat_placement >= 1.0 {beat_placement} element.offset {element.offset} ts {ts}')

            if beat_placement < analysis_results["min_beat_placement"]:
                analysis_results["min_beat_placement"] = beat_placement
            if beat_placement > analysis_results["max_beat_placement"]:
                analysis_results["max_beat_placement"] = beat_placement

    # Calculate percentages
    total_notes = analysis_results["on_beat_notes"] + analysis_results["offbeat_notes"]
    analysis_results["total_notes_ties_stripped"] = total_notes
    analysis_results["percentage_on_beat"] = (
        (analysis_results["on_beat_notes"] / total_notes) * 100
        if total_notes > 0
        else 0
    )
    # truncate a float to one decimal place
    analysis_results["percentage_on_beat"] = (
        math.trunc(analysis_results["percentage_on_beat"] * 10) / 10
    )

    total_cadences = (
        analysis_results["on_beat_cadence_notes"]
        + analysis_results["offbeat_cadence_notes"]
    )
    analysis_results["total_cadences"] = total_cadences
    analysis_results["percentage_on_beat_cadences"] = (
        (analysis_results["on_beat_cadence_notes"] / total_cadences) * 100
        if total_cadences > 0
        else 0
    )
    # truncate a float to one decimal place
    analysis_results["percentage_on_beat_cadences"] = (
        math.trunc(analysis_results["percentage_on_beat_cadences"] * 10) / 10
    )

    # Handle cases where no notes are present
    if analysis_results["min_duration"] == float("inf"):
        analysis_results["min_duration"] = 0
    if analysis_results["max_duration"] == float("-inf"):
        analysis_results["max_duration"] = 0
    if analysis_results["min_beat_placement"] == float("inf"):
        analysis_results["min_beat_placement"] = 0
    if analysis_results["max_beat_placement"] == float("-inf"):
        analysis_results["max_beat_placement"] = 0

    return analysis_results

def log_analyze_melody_beats(melody_stream, melody_name="Melody"):
    """
    Logs the analysis results of a melody stream using analyze_melody_beats.

    Args:
        melody_stream (music21.stream.Stream): The melody stream to analyze and log.
        melody_name (str): The name of the melody to log.
    """
    analysis_results = analyze_melody_beats(melody_stream)

    logger.info(f" ")
    logger.info(f"{melody_name} Melody Beats Analysis Results:")
    # Print analysis results
    for key, value in analysis_results.items():
        logger.info(f"{key}: {value}")

    return

def is_stream_object(obj):
  """
  Checks if an object is a music21 Stream (or a subclass of Stream).

  Args:
    obj: The object to check.

  Returns:
    bool: True if the object is a Stream, False otherwise.
  """
#   return isinstance(obj, stream.Stream) or issubclass(obj.__class__, stream.Stream)
  return isinstance(obj, stream.Stream) 



def analyze_melody_notes(melody_stream):
    """
    Analyze a melody for useful statistics, including counting the total number of sharps and flats.

    Args:
        melody_stream (music21.stream.Stream): The melody stream to analyze.

    Returns:
        dict: A dictionary containing the analysis results.
    """
    analysis_results = {
        "total_notes": 0,
        "total_sharps": 0,
        "total_flats": 0,
        "total_accidentals": 0,
        "note_durations": {},
        "note_pitches": {},
    }

    if is_stream_object(melody_stream):
        flat_melody = melody_stream.flatten()
    else:       
        flat_melody = melody_stream.stream().flatten()

    # for element in melody_stream.flatten().notes:
    for element in flat_melody.notes:
        if isinstance(element, note.Note):
            analysis_results["total_notes"] += 1

            # Count sharps and flats
            if "#" in element.name:
                analysis_results["total_sharps"] += 1
            elif "-" in element.name:
                analysis_results["total_flats"] += 1

            # Count note durations
            duration = element.quarterLength
            if duration not in analysis_results["note_durations"]:
                analysis_results["note_durations"][duration] = 0
            analysis_results["note_durations"][duration] += 1

            # Count note pitches
            pitch = element.nameWithOctave
            if pitch not in analysis_results["note_pitches"]:
                analysis_results["note_pitches"][pitch] = 0
            analysis_results["note_pitches"][pitch] += 1

    # Calculate the total number of accidentals
    analysis_results["total_accidentals"] = (
        analysis_results["total_sharps"] + analysis_results["total_flats"]
    )

    return analysis_results


def append_or_set_title(score, text_to_append):
    if score.metadata is None:
        score.metadata = metadata.Metadata()

    if score.metadata.title:
        score.metadata.title += text_to_append
    else:
        score.metadata.title = text_to_append


def log_analyze_melody_notes(melody_stream, melody_name="Melody"):
    """
    Logs the analysis results of a melody stream using analyze_melody_notes.

    Args:
        melody_stream (music21.stream.Stream): The melody stream to analyze and log.
        melody_name (str): The name of the melody to log.
    """
    analysis_results = analyze_melody_notes(melody_stream)

    logger.info(f" ")
    logger.info(f"{melody_name} Melody Note Analysis Results:")

    ts = get_first_time_signature(melody_stream)
    show_text_in_stream(melody_stream, ts)

    # logger.debug(f"Total Notes: {analysis_results['total_notes']}")
    # logger.debug(f"Total Sharps: {analysis_results['total_sharps']}")
    # logger.debug(f"Total Flats: {analysis_results['total_flats']}")
    # logger.debug(f"Total Accidentals: {analysis_results['total_accidentals']}")
    # logger.debug(f"Note Durations: {analysis_results['note_durations']}")
    # logger.debug(f"Note Pitches: {analysis_results['note_pitches']}")

    logger.info(f"Total Notes: {analysis_results['total_notes']}")
    logger.info(f"Total Sharps: {analysis_results['total_sharps']}")
    logger.info(f"Total Flats: {analysis_results['total_flats']}")
    logger.info(f"Total Accidentals: {analysis_results['total_accidentals']}")
    logger.info(f"Note Durations: {analysis_results['note_durations']}")
    logger.info(f"Note Pitches: {analysis_results['note_pitches']}")

def log_transition_analysis(transition, transition_name="Transition"):
    """
    Logs the transition dictionary and the results of analyze_transition.

    Args:
        transition (dict): The transition dictionary to analyze and log.
        transition_name (str): The name of the transition to log.
    """
    logger.debug(f"{transition_name} Dictionary:")
    for key, sub_dict in transition.items():
        logger.debug(f"{key}: {sub_dict}")

    analysis_results = analyze_transition(transition)
    logger.debug(f"{transition_name} Analysis Results:")
    logger.debug(f"Number of Items: {analysis_results['num_items']}")
    logger.debug(f"Minimum Sub-Items: {analysis_results['min_sub_items']}")
    logger.debug(f"Average Sub-Items: {analysis_results['avg_sub_items']}")
    logger.debug(f"Maximum Sub-Items: {analysis_results['max_sub_items']}")


def analyze_transition(transition):
    """
    Analyze the transition dictionary and produce the number of items in the dictionary,
    the minimum number of sub-items per dictionary item, the average number of sub-items per dictionary item,
    and the maximum number of sub-items per dictionary item.

    Args:
        transition (dict): The transition dictionary to analyze.

    Returns:
        dict: A dictionary containing the analysis results.
    """
    analysis_results = {
        "num_items": 0,
        "min_sub_items": float("inf"),
        "avg_sub_items": 0,
        "max_sub_items": float("-inf"),
    }

    num_items = len(transition)
    analysis_results["num_items"] = num_items

    if num_items == 0:
        analysis_results["min_sub_items"] = 0
        analysis_results["avg_sub_items"] = 0
        analysis_results["max_sub_items"] = 0
        return analysis_results

    total_sub_items = 0

    for key, sub_dict in transition.items():
        num_sub_items = len(sub_dict)
        total_sub_items += num_sub_items

        if num_sub_items < analysis_results["min_sub_items"]:
            analysis_results["min_sub_items"] = num_sub_items
        if num_sub_items > analysis_results["max_sub_items"]:
            analysis_results["max_sub_items"] = num_sub_items

    analysis_results["avg_sub_items"] = total_sub_items / num_items

    return analysis_results


def update_transition(transition, key, value):
    """
    update the transition key with the value
    and return the transition
    """
    if key in transition:
        if value in transition[key]:
            transition[key][value] += 1
            # print('increment existing [key] [value]: transition[key][value] += 1: key, value:', key, value)
        else:
            transition[key][value] = 1
            # print('insert new value in existing key: transition[key][value] = 1: key, value:', key, value)
    else:  # key not in transition
        transition[key] = {value: 1}
        # print('Add missing key: transition[key] = {value: 1}: key, value:', key, value)

    return transition



def get_total_frequency(transition_with_frequencies):
    """
    given a transition_with_frequencies
    calculate the total_frequency and return it
    """
    total_frequency = 0
    # Compute the total_frequency for the transition_with_frequencies
    for k, v in transition_with_frequencies.items():
        for i, j in v.items():
            total_frequency = total_frequency + transition_with_frequencies[k][i]
            # print('k, v, i, j, transition_with_frequencies[k][i]', k, v, i, j, transition_with_frequencies[k][i] )

    # print('total_frequency:', total_frequency)

    return total_frequency

def transition_frequency_to_probability(transition):
    """
    given a transition dictionary with frequencies
    convert the frequencies to probabilities and
    return the transition dictionary
    """
    total_freq = get_total_frequency(transition)

    # Compute the probability for each transition_with_frequencies
    for k, v in transition.items():
        for i, j in v.items():
            transition[k][i] = j / total_freq

    # print('transition', transition)

    return transition

def calc_the_note_range(song):
    """
    function that takes a song stream
    and returns min_note.nameWithOctave and max_note.nameWithOctave
    """

    min_note = note.Note()
    max_note = note.Note()
    min_note.nameWithOctave = "C9"
    max_note.nameWithOctave = "A0"

    if is_stream_object(song):
        flat_melody = song.flatten()
    else:       
        flat_melody = song.stream().flatten()

    # for n in song.flatten().notes:
    for n in flat_melody.notes:

        if type(n) == music21.note.Note:
            if note.Note(n.nameWithOctave) < note.Note(min_note.nameWithOctave):
                min_note = n
                # print('min_note.nameWithOctave', min_note.nameWithOctave)
            if note.Note(n.nameWithOctave) > note.Note(max_note.nameWithOctave):
                max_note = n
                # print('max_note.nameWithOctave', max_note.nameWithOctave)

    return min_note.nameWithOctave, max_note.nameWithOctave


def check_score_well_formedness(score):
    """
    Checks if a music21 score object is well-formed for MusicXML conversion.

    Args:
        score: The music21 stream.Score object to be checked.

    Returns:
        True if the score is well-formed, False otherwise.
    """

    if not score.isWellFormedNotation():
        # warnings.warn(f'{score} is not well-formed; see isWellFormedNotation()', UserWarning)
        logger.warning(
            f"check_score_well_formedness score = {score} is not well-formed; see isWellFormedNotation()",
            UserWarning,
        )

        # Handle the issue, e.g., by fixing the score or logging the problem
        # For example, you can print the elements that are causing the issue
        for part in score.parts:
            for element in part.flatten().notesAndRests:
                if not element.isWellFormedNotation():
                    logger.warning(f"Element not well-formed: {element}")
        logger.debug(
            f"Score is not well-formed! Check the warnings for specific issues."
        )
        # for warning in score.warnings:
        #     logger.debug(f'warning = {warning} ')
        return False
    else:
        logger.debug(
            f"check_score_well_formedness score = {score} Score appears to be well-formed for MusicXML conversion."
        )

        print("Score appears to be well-formed for MusicXML conversion.")
        return True


from music21 import stream


def check_stream_structure(stream_object):
    """
    Analyzes a music21 stream and reports information about its structure.

    Args:
        stream_object: The music21 stream object to be analyzed.

    Returns:
        A dictionary containing information about the stream structure.
    """

    structure_info = {}

    # Check for stream type
    if not isinstance(stream_object, stream.Stream):
        structure_info["Error"] = "Input is not a music21 stream object."
        return structure_info

    # Number of parts
    structure_info["Number of Parts"] = len(stream_object.parts)

    # Information about each part
    part_info = []
    for i, part in enumerate(stream_object.parts):
        part_data = {}
        part_data["Part Index"] = i
        part_data["Number of Measures"] = len(part.getElementsByClass(stream.Measure))
        part_data["Number of Notes"] = len(
            part.flatten().notes
        )  # Count all notes within the part

        # Additional information (optional)
        # You can add checks for specific elements within each part, like chords or rests.

        part_info.append(part_data)

    structure_info["Part Information"] = part_info

    return structure_info


# freezer utility functions
# see https://web.mit.edu/music21/doc/moduleReference/moduleFreezeThaw.html


def converter_freezer_load_stream(file_path):
    """
    Load a music21 Stream object from a file using music21.freezeThaw.

    Parameters:
    file_path (str): The file path to load the Stream object from.

    Returns:
    music21.stream.Stream: The loaded Stream object.
    """
    # thawer = freezeThaw.StreamThawer()
    # thawer.open(file_path)
    stream = music21.converter.thaw(file_path, zipType="zlib")

    return stream


def converter_freezer_save_stream(stream_obj):
    """
    Save a music21 Stream object to a file using music21.freezeThaw in jsonpickle format
    where the music21 version used is at the end of the file e.g.
    "m21Version": {"py/tuple": ["9", "1", "0"]}}

    Parameters:
    stream_obj (music21.stream.Stream): The music21 Stream object to save.

    Returns:
    file_path (str): The file path where object saved. e.g. in windows
    C:/Users/admin2/AppData/Local/Temp/music21/m21-63ecd71ec51bb161a860fb26828a7d6b.p.json
    """
    # freezer = freezeThaw.StreamFreezer(stream_obj)
    # file_path = freezer.write(fmt='jsonpickle')
    # file_path = music21.converter.freeze(stream_obj, fp=file_path, zipType='zlib')
    # file_path = music21.converter.freeze(stream_obj, zipType='zlib')
    file_path = music21.converter.freeze(stream_obj)

    return file_path


def describe_tuplet(note_obj):
    """
    Takes a music21 Note object and returns a description of the associated tuplet (if any).

    Args:
        note_obj (music21.note.Note): The Note object to check for a tuplet.

    Returns:
        str: A description of the tuplet (e.g., '3:2' for a triplet).
             Returns an empty string if no tuplet is present.
    """
    if note_obj.tuplets:
        # Get the first tuplet (assuming there's only one)
        my_tuplet = note_obj.tuplets[0]

        # Extract relevant information
        num_actual_notes = my_tuplet.numberNotesActual
        num_normal_notes = my_tuplet.numberNotesNormal
        dur_actual_type = my_tuplet.durationActual.type

        # Create a string representation
        # tuplet_description = f"{num_actual_notes}:{num_normal_notes}"
        tuplet_description = f"{num_actual_notes}:{num_normal_notes}:{dur_actual_type}"

        return tuplet_description
    else:
        return ""  # No tuplet found


# freezer utility functions
# see https://web.mit.edu/music21/doc/moduleReference/moduleFreezeThaw.html

# def fractional_part_as_fraction(number):
#     # Convert the number to a Fraction
#     frac = Fraction(number).limit_denominator()
#     # Get the fractional part
#     fractional_part = frac - frac.numerator // frac.denominator
#     return fractional_part


def fractional_part_as_fraction(value, time_signature):
    """
    Converts the fractional part of a number to a Fraction, considering the time signature.

    Args:
        value (float): The value to convert.
        time_signature (music21.meter.TimeSignature): The time signature of the piece.

    Returns:
        Fraction: The fractional part as a fraction within the context of the time signature.
    """
    try:
        value = float(value)
        if value < 0:
            raise ValueError("Negative values are not allowed")

        frac = Fraction(value).limit_denominator()
        fractional_part = frac - int(frac)

        # Calculate the beat placement within the measure
        # beats_per_measure = time_signature.numerator
        beat_duration = time_signature.beatDuration.quarterLength
        beat_placement = fractional_part * beat_duration
        logger.debug(
            f"fractional_part_as_fraction value = {value} frac = {frac} fractional_part = {fractional_part} beat_duration = time_signature.beatDuration.quarterLength = {beat_duration} beat_placement {beat_placement}"
        )
        logger.debug(
            f"fractional_part_as_fraction return  = {Fraction(beat_placement).limit_denominator()} where value = {value} time_signature = {time_signature}"
        )

        return Fraction(beat_placement).limit_denominator()
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting value to fraction: {e}")
        return Fraction(0)


def freezer_load_stream(file_path):
    """
    Load a music21 Stream object from a file using music21.freezeThaw.

    Parameters:
    file_path (str): The file path to load the Stream object from.

    Returns:
    music21.stream.Stream: The loaded Stream object.
    """
    thawer = freezeThaw.StreamThawer()
    thawer.open(file_path)
    return thawer.stream


def freezer_save_stream(stream_obj):
    """
    Save a music21 Stream object to a file using music21.freezeThaw in jsonpickle format
    where the music21 version used is at the end of the file e.g.
    "m21Version": {"py/tuple": ["9", "1", "0"]}}

    Parameters:
    stream_obj (music21.stream.Stream): The music21 Stream object to save.

    Returns:
    file_path (str): The file path where object saved. e.g. in windows
    C:/Users/admin2/AppData/Local/Temp/music21/m21-63ecd71ec51bb161a860fb26828a7d6b.p.json
    """
    freezer = freezeThaw.StreamFreezer(stream_obj)
    file_path = freezer.write(fmt="jsonpickle")
    return file_path


def get_beat_in_bar(note, time_signature):
    """
    Calculates the beat of the bar for a note, considering the time signature.

    Args:
        note: A music21 note object.
        time_signature: A music21 time signature object.
        NOTE: assuming only one time signature in stream.

    Returns:
        The beat of the bar (e.g., 1, 1.5) for the note.
    """
    # Get the numerator and denominator of the time signature
    numerator = time_signature.numerator
    denominator = time_signature.denominator

    # calculate the length of one bar in offsets
    bar_length_offset = numerator / (denominator / 4)

    # calculate beats per offset
    beats_per_offset = numerator / bar_length_offset

    # convert note offset to within bar offset (assuming only one time signature)
    prev_bar_offset = math.trunc(note.offset / bar_length_offset) * bar_length_offset
    within_bar_offset = note.offset - prev_bar_offset

    # convert offset within bar to beat
    beat_within_bar = (within_bar_offset * beats_per_offset) + 1

    return beat_within_bar




from fractions import Fraction
import ast

def get_duration_set(temp_DURATION_SET):
    """
    Function that takes a duration set string,
    and returns the DURATION_SET converted to fractions.

    Parameters:
    temp_DURATION_SET (str): The duration set string.

    Returns:
    list: The DURATION_SET converted to fractions.
    """
    if temp_DURATION_SET != "":
        try:
            DURATION_SET = ast.literal_eval(str(temp_DURATION_SET))
        except BaseException as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("exit: Error DURATION_SET")
            sys.exit()

        if not isinstance(DURATION_SET, list):
            print("exit: DURATION_SET is not a list e.g. []")
            sys.exit()
        for dur_num in range(0, len(DURATION_SET)):
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
    else:
        DURATION_SET = []
    return DURATION_SET

def get_first_time_signature(score):
    """
    Get the first time signature in a music21 score.

    Args:
        score (music21.stream.Score): The score to analyze.

    Returns:
        music21.meter.TimeSignature: The first time signature in the score, or None if no time signature is found.
    """
    if is_stream_object(score):
        flattened_score = score.flatten()
    else:       
        flattened_score = score.stream().flatten()

    for element in flattened_score.getElementsByClass(meter.TimeSignature):
        return element
    return None


def get_iso_datetime_str():
    """Returns the current date and time in ISO format (YYYY-MM-DD_HH-MM-SS)."""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S")


def get_offsets_per_bar(time_signature):
    """
    Calculates the number of offsets in a bar based on the time signature.

    Args:
        time_signature: A music21 time signature object.

    Returns:
        The number of offsets in a bar.
    """
    # Get the numerator and denominator of the time signature
    numerator, denominator = time_signature.ratio.components

    # Calculate the number of eighths per beat based on the denominator
    eighths_per_beat = {
        4: 2,  # Quarter note
        8: 1,  # Eighth note
        16: 0.5,  # Sixteenth note, etc.
    }.get(denominator, 1 / denominator)

    # Return the product of numerator and eighths per beat
    return numerator * eighths_per_beat


def has_tuplet(stream):
    """
    Checks if the given stream has a tuplet note.

    Args:
        stream (music21.stream.Stream): The input stream.

    Returns:
        bool: True if the stream has a tuplet note, False otherwise.
    """
    for element in stream.flatten().notesAndRests:
        if element.duration.tuplets:
            return True
    return False


def is_note_on_beat(note, time_signature):
    """
    Checks if a music21 note object starts on a beat, considering the time signature.
    see https://web.mit.edu/music21/doc/moduleReference/moduleMeterBase.html

    Args:
      note: A music21 note object.
      time_signature: A music21 time signature object.

    Returns:
      True if the note starts on a beat, False otherwise.
    """

    # beat_in_bar = get_beat_in_bar(note, time_signature)

    offsets_per_beat = 4.0 / time_signature.denominator

    # print('note.offset  % offsets_per_beat', note.offset , offsets_per_beat, note.offset  % offsets_per_beat)

    return note.offset % offsets_per_beat == 0.0


def is_offset_on_beat(note_offset, time_signature):
    """
    Checks if a music21 note_offset object starts on a beat, considering the time signature.
    see https://web.mit.edu/music21/doc/moduleReference/moduleMeterBase.html

    Args:
      note_offset: A music21 note_offset object.
      time_signature: A music21 time signature object.

    Returns:
      True if the note_offset starts on a beat, False otherwise.
    """

    offsets_per_beat = 4.0 / time_signature.denominator

    # print('note_offset  % offsets_per_beat', note_offset , offsets_per_beat, note_offset  % offsets_per_beat)

    return note_offset % offsets_per_beat == 0.0

def is_number_an_integer(number):
    """
    Check if the given number is an integer.

    Parameters:
    number (str): The number to check.

    Returns:
    bool: True if the number is an integer, False otherwise.
    """
    try:
        # return float(number).is_integer()
        return float(number).is_integer() and not '.' in number
    except ValueError:
        return False

def is_tuplet(quarter_length):
    """
    Checks if the given quarter-length duration is part of a tuplet.

    Args:
        quarter_length (float): The quarter-length duration to check.

    Returns:
        bool: True if the duration is part of a tuplet, False otherwise.
    """
    my_duration = duration.Duration(quarter_length)
    return bool(my_duration.tuplets)


def midi_to_musicxml(midi_file_path, musicxml_file_path):
    """
    reads a midi file and writes a musicxml file.

    Args:
        midi_file_path: path to midi file
        musicxml_file_path: path to musicxml file

    Returns:
        None

    Example use:

    OUTPUT_PATH = "private/output/"
    output_filename = "tuplet01"
    midi_file_path = OUTPUT_PATH + output_path + ".mid"
    musicxml_file_path = OUTPUT_PATH + output_filename + "-midi_to_musicxml.mxl"
    midi_to_musicxml(midi_file_path, musicxml_file_path)

    Note: any MuseScore 3.6.2 / 4.3.0 tuple import errors were still present in 2 out of 3 scores
    after midi - musicxml round trip.
    """
    # Read the MIDI file into a music21 stream
    midi_stream = converter.parse(midi_file_path)

    # Write the stream to a compressed MusicXML file
    midi_stream.write("musicxml", fp=musicxml_file_path)

# v1
# def parse_value(value_str):
#     """
#     Attempts to parse a string into a more specific type (int, float, bool, list, Fraction)
#     or returns the string itself if parsing fails.
#     """
#     value_str = value_str.strip()
#     if value_str.lower() == 'true':
#         return True
#     elif value_str.lower() == 'false':
#         return False
#     elif value_str.startswith('[') and value_str.endswith(']'):
#         # Attempt to parse as a list
#         try:
#             return [parse_value(item.strip()) for item in value_str[1:-1].split(',')]
#         except:
#             pass
#     elif '/' in value_str:
#         try:
#             return Fraction(value_str)
#         except ValueError:
#             pass
#     try:
#         return int(value_str)
#     except ValueError:
#         try:
#             return float(value_str)
#         except ValueError:
#             return value_str

#v2 with list comprehension
def parse_value(value_str):
    """
    Parses a string value from the config file into its appropriate Python type.
    Handles lists, floats, ints, bools, and strings.
    """
    try:
        # Attempt to parse as a list
        parsed_value = ast.literal_eval(value_str)
        if isinstance(parsed_value, list):
            return parsed_value
        
    except (ValueError, SyntaxError):
        pass

    try:
        # Attempt to parse as a float
        return float(value_str)
    except ValueError:
        pass

    try:
        # Attempt to parse as an int
        return int(value_str)
    except ValueError:
        pass

    # Attempt to parse as a boolean
    if value_str.lower() == "true":
        return True
    elif value_str.lower() == "false":
        return False

    # If all else fails, treat it as a string
    return value_str

def prepare_stream_for_xml(score):
    """
    Prepare the stream for writing to XML.
    """
    # Check if the score is well-formed
    if not score.isWellFormedNotation():
        logger.warning(f"Score {score} is not well-formed; see isWellFormedNotation()")
        # Handle the issue, e.g., by fixing the score or logging the problem
        for part in score.parts:
            for element in part.flatten().notesAndRests:
                if not element.isWellFormedNotation():
                    logger.warning(f"Element not well-formed: {element}")

    # Apply makeNotation to ensure proper formatting
    score.makeNotation(inPlace=True)

    # Ensure measures are correctly formed
    score.makeMeasures(inPlace=True)

    # Fix ties and beams for the entire score
    # score.fixTies()
    # score.fixBeams()

    # Fix ties and beams for each part
    for part in score.parts:
        for measure in part.getElementsByClass(stream.Measure):
            measure.makeNotation(inPlace=True)
        # part.fixTies()
        # part.fixBeams()

    return score


def print_call_chain():
    """
    Prints the current call chain (stack trace).
    """
    stack_trace = traceback.format_stack()
    for line in stack_trace:
        print(line.strip())


def quarterlength_to_musicxml_duration(quarterlength, divisions_per_quarter=10080):
    """
    Convert a music21 quarter length to a MusicXML duration.

    Parameters:
    quarterlength (float): The quarter length in music21 notation.
    divisions_per_quarter (int, optional): The number of divisions per quarter note in the MusicXML document.
    Music21 uses 10080 for divisions. Other software may use 480, 960, or 1920.

    Returns:
    int: The duration in MusicXML notation.
    """
    return int(quarterlength * divisions_per_quarter)


def show_text_in_stream(song, ts):
    # print('show_text_in_stream ------------------------------------------------- stream.id = decimal, hex', song.id, hex(song.id))
    # logger.debug(f"show_text_in_stream ---------------------------------------- stream.id {song.id}")
    logger.debug(f"show_text_in_stream ------------------------------------ {song} ts {ts}")

    # song.show('text')
    if is_stream_object(song):
        flat_song = song.flatten()
    else:       
        flat_song = song.stream().flatten()
    
    # flat_song = song.flatten().stream()
    # if not song.isWellFormedNotation():
    #     print("show_text_in_stream WARNING f'{song} is not well-formed; see isWellFormedNotation()")

    # offset_end = 0.0
    # for n in song.flatten().notes:
    # for n in song.flatten():
    for n in flat_song:
        # print('type(n) ', type(n) )
        if type(n) == music21.clef.TrebleClef:
            logger.debug("music21.clef.TrebleClef")

        if type(n) == music21.expressions.TextExpression:
            # print('music21.expressions.TextExpression')
            # print("TextExpression =", n.content)
            logger.debug(f"\n TextExpression = {n.content} ")

        if type(n) == music21.key.KeySignature:
            # print('music21.key.KeySignature', song.tonic.name, song.mode)
            logger.debug(f"music21.key.KeySignature{song.keySignature}")  # None
            # first = True
            # for sKS in song.flatten().getElementsByClass("KeySignature"):
            #     if first:
            first_ks = True
            for sKS in flat_song.getElementsByClass("KeySignature"):
                if first_ks:
                    songKeySignature = sKS
                    logger.debug(f"First KeySignature:{songKeySignature}")  # e.g. <music21.key.KeySignature of 1 flat>
                    logger.debug(f".sharps:{songKeySignature.sharps}")  # e.g. -1
                    logger.debug(f".getScale(major):{songKeySignature.getScale('major')}")  # e.g. <music21.scale.MajorScale F major>
                    first = False
                else:
                    logger.debug(f"other KeySignature:{sKS}")

        if type(n) == music21.metadata.Metadata:
            # Metadata represent data for a work or fragment, including
            # title, composer, dates, and other relevant information.
            logger.debug("music21.metadata.Metadata")
            # print('all =', song.metadata.all())
            # print('title =', song.metadata.title) # crash if none
            # print('composer =', song.metadata.composer)
            # print('date = ', song.metadata.date)
            # print('lyricist = ', song.metadata.lyricist)

        if type(n) == music21.meter.TimeSignature:
            # get the timesignatures
            first_ts = True
            logger.debug("music21.meter.TimeSignature")
            for (
                tSig
            ) in (
                song.getTimeSignatures()
                ):
                if first_ts:
                    songTimeSig = tSig
                    logger.debug(f"First Time Signature:{songTimeSig}")  # eg First Time Signature: <music21.meter.TimeSignature 4/4>
                    first_ts = False
                else:
                    logger.debug(f"Other Time Signature:{tSig}")


        if type(n) == music21.note.Note or type(n) == music21.note.Rest:
            show_text_of_note(n, ts)

        if type(n) == music21.tempo.MetronomeMark:
            logger.debug(f"music21.tempo.MetronomeMark{n.number}")

    min_note, max_note = calc_the_note_range(song)
    logger.debug(f"min_note, max_note{min_note}, {max_note}")
    return


def show_text_of_note(n, ts):
    """
    takes a note and the beats to the bar
    and print the text to the console
    """
    if ts is None:
        logger.warning('WARNING: show_text_of_note ts is None - exiting ')
        return
        
    # Example log messages
    # logger.debug('Debug test message')
    # logger.info('Info test message')
    # logger.warning('Warning test message')
    # logger.error('Error test message')
    # logger.critical('Critical test message')

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

    tie_representation = ""
    lyric_representation = ""
    tuplet_type = ""
    tuplet_desc = ""

    if type(n) == music21.note.Note or type(n) == music21.note.Rest:

        beat_in_bar = get_beat_in_bar(n, ts)

        # find if note is ON or OFF the beat
        if is_note_on_beat(n, ts):
            type_of_beat = "ON "
        else:
            type_of_beat = "OFF"

        # convert ql to musicxml duration
        musicxml_duration = quarterlength_to_musicxml_duration(n.duration.quarterLength)

        # format data
        formatted_offset = f"{n.offset:.2f}"
        formatted_bar = f"{((n.offset / beat_count)+1):.2f}"
        formatted_beat_in_bar = f"{beat_in_bar:.2f}"
        formatted_musicxml_duration = f"{musicxml_duration:.0f}"
        formatted_offset_end = f"{offset_end:.2f}"

        # print a line before the first note of the bar
        if beat_in_bar == 1:
            logger.debug(
                "OFFSET----BAR-------BEAT------QUARTERLENGTH-------MXLDUR-OFFSETEND-NOTE---QLEN-LYRIC-----"
            )

        if n.isRest:
            pass
        else:
            # represent a tie start or continue by '-'
            if n.tie is not None:
                # Access the tie type
                if n.tie.type == "start" or n.tie.type == "continue":
                    tie_representation = "-"
                else:
                    # Handle other cases (e.g. stop, etc.)
                    tie_representation = ""
            if n.lyric is None:
                lyric_representation = ""
            else:
                lyric_representation = n.lyric

            if hasattr(n.duration, "tuplets"):
                # print('hasattr(n.duration, tuplets', n.duration)
                # input('Press Enter to continue...')
                try:
                    if n.duration.tuplets != ():
                        has_tuplet = True
                        # Get the first tuplet (assuming there's only one)
                        my_tuplet = n.duration.tuplets[0]
                        # Determine the type of the tuplet
                        tuplet_type = my_tuplet.type

                        tuplet_desc = describe_tuplet(n.duration)

                        # print('n.duration.quarterLength, n.duration.tuplets[0], n.duration.tuplets[0].fullName, n.duration.tuplets[0].tupletMultiplier(),tuplet_desc ',n.duration.quarterLength, n.duration.tuplets[0], n.duration.tuplets[0].fullName, n.duration.tuplets[0].tupletMultiplier(),tuplet_desc)
                        # input('Press Enter to continue...')
                except IndexError:
                    pass
                    # print('n.duration.tuplets IndexError',my_tuplet.type)
                    # input('Press Enter to continue...')

            else:
                tuplet_type = ""

    if type(n) == music21.note.Note:

        # print('o %.4f' % n.offset, n.offset, '    \t Bar %.4f' % ((n.offset / beat_count)+1), '\t Beat %.4f' % beat_in_bar, type_of_beat, 'ql',
        #       n.duration.quarterLength, tuplet_desc, '    \t = o_end %.4f' % offset_end, '\t note qLen lyric:\t', n.nameWithOctave, tie_representation, '\t',
        #       n.duration.quarterLength, '\t', lyric_representation)

        # 0         1         2         3         4         5         6         7
        # 01234567890123456789012345678901234567890123456789012345678901234567890123456789
        # Offset----Bar-------Beat------QuarterLength-------OffsetEnd-Note--QLen-Lyric-----
        # 436.0000  110.0000  1.0000 ON 2/3 3:2:quarter     436.666   A5    2/3  when

        # :<9 means the output will be left-aligned and take up at least 9 characters. If the output string is less than 9 characters long, it will be padded with spaces on the right
        # where 9 is the field width - 1
        text = f"{formatted_offset:<9} {formatted_bar:<9} {formatted_beat_in_bar:<4} {type_of_beat:<4} {str(n.duration.quarterLength):<5} {tuplet_desc:<13} {formatted_musicxml_duration:<6} {formatted_offset_end:<9} {n.nameWithOctave:<4} {tie_representation:<1} {str(n.duration.quarterLength):<3} {lyric_representation:<9}"
        # print(text)
        logger.debug(text)
    if type(n) == music21.note.Rest:

        # print(
        #     "o %.4f" % n.offset,
        #     n.offset,
        #     "    \t bar %.4f" % ((n.offset / beat_count) + 1),
        #     "\t Beat %.4f" % beat_in_bar,
        #     type_of_beat,
        #     "ql",
        #     n.duration.quarterLength,
        #     tuplet_desc,
        #     "\t = o_end %.4f" % offset_end,
        #     "\t rest quarterLength:",
        #     n.duration.quarterLength,
        # )
        text = f"{formatted_offset:<9} {formatted_bar:<9} {formatted_beat_in_bar:<4} {type_of_beat:<4} {str(n.duration.quarterLength):<5} {tuplet_desc:<13} {formatted_musicxml_duration:<6} {formatted_offset_end:<9} {'rest':<6} {str(n.duration.quarterLength):<3} "

        # print(text)
        logger.debug(text)


def split_notes_to_reinforce_the_beat(s):
    """
    given a stream with a time signature
    .flatten() the score,
    replace the original time signature with 1/4,
    call makeNotation() on it,
    flatten the score again,
    put the original time signature back,
    call makeNotation() again
    return the stream
    """
    # Store the original time signature
    original_ts = s.getTimeSignatures()[0]
    print("split_notes_to_reinforce_the_beat original_ts", original_ts)
    # input('Press Enter to continue...')

    # Flatten the score
    s = s.flatten()

    # Replace the time signature with 1/4
    s.replace(original_ts, meter.TimeSignature("1/4"))

    # Call makeNotation on the score
    s = s.makeNotation()

    # Flatten the score again
    s = s.flatten()

    # Put the original time signature back
    s.replace(s.getTimeSignatures()[0], original_ts)

    # Call makeNotation again
    s = s.makeNotation()
    return s


def stream_to_midi_with_lyrics(stream, filename):
    """
    Writes a music21 stream with lyrics to a MIDI file using mido.

    Args:
    stream: A music21 stream object containing melody and lyrics.
    filename: The desired filename for the MIDI karaoke file, may end in _[k].kar
    """
    text = f"\nstream_to_midi_with_lyrics {filename}"
    logger.info(text)

    # Create a new MIDI file with a single track
    mid = MidiFile(ticks_per_beat=480)  # Set ticks per beat
    # mid = MidiFile(ticks_per_beat=1920)  # Set ticks per beat # caused failures at tempos > 175 BPM
    track = MidiTrack()
    mid.tracks.append(track)

    title_text1 = "@T" + filename
    track.append(MetaMessage("text", text=title_text1, time=0))
    # title_text2 = "@T" + stream.metadata.title
    # track.append(MetaMessage('text', text=title_text2, time=0))
    title_text3 = "@T" + stream.metadata.composer
    track.append(MetaMessage("text", text=title_text3, time=0))

    # Get the tempo from the music21 stream (assumes the stream has a tempo)
    # m21_tempo = stream.flatten().getElementsByClass("MetronomeMark")[0].number

    # Flatten the stream to get all elements
    flat_stream = stream.flatten()

    # Get the tempo from the stream
    metronome_marks = flat_stream.getElementsByClass("MetronomeMark")
    if metronome_marks:
        m21_tempo = metronome_marks[0].number
    else:
        m21_tempo = 120  # Default tempo if no MetronomeMark is found

    logger.debug(f"\ntempo = {m21_tempo}")

    # Get the time signature from the music21 stream
    # time_signature = stream.recurse().getElementsByClass(meter.TimeSignature)[0]
    # # Extract numerator and denominator from time signature
    # numerator, denominator = time_signature.numerator, time_signature.denominator
    time_signatures = stream.recurse().getElementsByClass(meter.TimeSignature)
    if time_signatures:
        time_signature = time_signatures[0]
        numerator, denominator = time_signature.numerator, time_signature.denominator
    else:
        time_signature = meter.TimeSignature('4/4')  # Default time signature
        numerator, denominator = 4, 4

    logger.debug(
        f"time_signature = {time_signature}, numerator = {numerator}, denominator = {denominator} "
    )

    # key signature C
    track.append(MetaMessage("key_signature", key="C"))

    # Set tempo and time signature
    # tempo = int(60_000_000 / m21_tempo)  # Convert BPM to microseconds per beat
    # Example fix: Handle None values
    if m21_tempo is not None:
        tempo = int(60_000_000 / m21_tempo)
    else:
        # Handle the case when m21_tempo is None (e.g., provide a default value)
        tempo = 120  # Default tempo in BPM

    track.append(MetaMessage("set_tempo", tempo=tempo))
    track.append(
        MetaMessage("time_signature", numerator=numerator, denominator=denominator)
    )

    # Iterate over all the notes in the music21 stream
    prev_offset_ticks = 0
    prev_n = None

    # Flag for first lyric
    first_lyric = True
    note_velocity = 85
    time = 0
    expression_text_found = False

    # for note in stream.flat.notesAndRests:
    for n in stream.flatten():

        if type(n) == music21.note.Note or type(n) == music21.note.Rest:
            # Convert offset and duration to ticks
            offset_ticks = int(n.offset * mid.ticks_per_beat)
            logger.debug(
                f"n.offset {n.offset} * mid.ticks_per_beat {mid.ticks_per_beat } = offset_ticks == {offset_ticks} "
            )
            duration_ticks = int(n.duration.quarterLength * mid.ticks_per_beat)
            logger.debug(
                f"n.duration.quarterLength {n.duration.quarterLength} * mid.ticks_per_beat {mid.ticks_per_beat } = duration_ticks == {duration_ticks} "
            )

            if prev_n == None:
                time = offset_ticks - prev_offset_ticks
            else:
                if prev_n.isRest:
                    time = prev_offset_ticks
                else:
                    time = offset_ticks - prev_offset_ticks
                    prev_offset_ticks = offset_ticks
            # prev_offset_ticks = offset_ticks
            logger.debug(f"time = {time}, prev_offset_ticks = {prev_offset_ticks} ")

            # If the n is a rest, add the duration of the rest to prev_offset_ticks
            if n.isRest:
                logger.debug(f"n.isRest")
                if prev_n != None:
                    logger.debug(f"prev_n != None")
                    if prev_n.isNote:
                        prev_offset_ticks = 0
                        logger.debug(f"prev_n.isNote prev_offset_ticks = 0 ")
                prev_offset_ticks += duration_ticks
                logger.debug(f"n.isRest prev_offset_ticks = {prev_offset_ticks} ")
                prev_n = n
                continue  # Skip this iteration, effectively adding a rest

            # If the n has lyrics, add a text meta event with the lyrics
            if n.lyric is not None:
                # lyric_text = n.lyric
                # avoid UnicodeEncodeError: 'latin-1' codec can't encode characters in position 2-3: ordinal not in range(256)
                lyric_text = remove_non_ascii(n.lyric)
                if first_lyric:
                    lyric_text = "\\\\" + lyric_text
                    first_lyric = False
                if expression_text_found:
                    lyric_text = expression_text + lyric_text
                    expression_text_found = False
                if prev_n != None:
                    if prev_n.isRest:
                        track.append(MetaMessage("text", text=lyric_text, time=time))
                        logger.debug(f"MetaMessage text = {lyric_text}, time = {time} ")
                    else:
                        track.append(MetaMessage("text", text=lyric_text, time=0))
                        logger.debug(f"MetaMessage text = {lyric_text}, time = 0 ")
                time = 0  # Reset time for the n event

            # Add n to track
            track.append(
                Message("note_on", note=n.pitch.midi, velocity=note_velocity, time=time)
            )
            logger.debug(f"MetaMessage note_on = {n.pitch.midi}, time = {time} ")
            track.append(
                Message(
                    "note_off",
                    note=n.pitch.midi,
                    velocity=note_velocity,
                    time=duration_ticks,
                )
            )
            logger.debug(
                f"MetaMessage note_off = {n.pitch.midi}, time = {duration_ticks} "
            )
            prev_n = n

        if type(n) == music21.expressions.TextExpression:
            expression_text_found = True
            expression_text = n.content.replace(" ", "")

    # Save the MIDI file
    mid.save(filename)


def remove_non_ascii(text):
  """Removes non-ASCII characters from a string.

  Args:
    text: The input string.

  Returns:
    A new string with non-ASCII characters removed.
  """
  # Method 1: Using encode and decode (fastest for most cases)
  # return text.encode("ascii", "ignore").decode("ascii")

  # Method 2: Using regular expressions (more flexible)
  return re.sub(r"[^\x00-\x7F]+", "", text)

def remove_zero_length_notes(score: stream.Score) -> stream.Score:
    """
    Removes notes with a quarterLength of 0.0 from a music21 Score,
    while preserving all other elements such as metadata, key/time signatures, etc.
    """
    new_score = stream.Score()
    new_score.metadata = score.metadata  # Copy metadata
    
    for part in score.parts:
        new_part = stream.Part(id=part.id)
        
        # Copy instrument safely to avoid duplicate object issue
        instr = part.getInstrument()
        if instr is not None:
            new_part.insert(0, instr.__class__())  # Create a new instance of the instrument
        
        for element in part.flatten():  # Process all elements
            if isinstance(element, note.Note):
                if element.quarterLength > 0.0:
                    new_part.append(element)
            else:
                new_part.append(element)  # Keep all other elements
        
        new_score.append(new_part)
    
    return new_score

def convert_part_to_monophonic(part):
    """
    Converts a music21 Part to a monophonic melody.

    Args:
        part: A music21 Part object.

    Returns:
        A new music21 Part object representing the monophonic melody.
    """
    new_part = stream.Part()
    new_part.id = part.id + "_mono"

    for element in part.getElementsByClass(['Measure','Stream']):
       
        if element.notes :
             if len(element.notes) > 0:
                  try:
                      lowest_note = min(element.notes, key=lambda n: n.pitch.ps)
                      new_part.append(copy.deepcopy(lowest_note))
                  except ValueError :
                      print("WARNING in convert_to_monophonic: ValueError: min() arg is an empty sequence.")
             else:
                for el in element:
                  new_part.append(copy.deepcopy(el))

    
        elif element.isClassOrSubclass((note.Rest,meter.TimeSignature,clef.Clef)):
              new_part.append(copy.deepcopy(element))
        else:
          pass
            
    return new_part

def convert_to_monophonic(score: stream.Score) -> stream.Score:
    """
    Removes notes with a quarterLength of 0.0 from a music21 Score,
    while preserving all other elements such as metadata, key/time signatures, etc.
    """
    new_score = stream.Score()
    new_score.metadata = score.metadata  # Copy metadata
    
    for part in score.parts:
        first_note = True
        found_note = False
        new_part = stream.Part(id=part.id)
        
        # Copy instrument safely to avoid duplicate object issue
        instr = part.getInstrument()
        if instr is not None:
            new_part.insert(0, instr.__class__())  # Create a new instance of the instrument
        
        for element in part.flatten():  # Process all elements
            if isinstance(element, note.Note):
                if first_note:
                    new_part.append(element)
                    first_note = False
                    found_note = True
                    prev_offset = element.offset
                else:
                    if element.offset != prev_offset:
                        new_part.append(element)
                    prev_offset = element.offset
            elif isinstance(element, chord.Chord):
                # Check if element.notes is empty
                if not element.notes:
                    # raise ValueError("No notes found in the element to convert to monophonic.")
                    logger.debug(f"ERROR: No notes found in the element to convert to monophonic.")
                    logger.debug(f"element: {element}")
                    continue
                # Convert chord to note.Note
                lowest_note = min(element.notes, key=lambda n: n.pitch.ps)
                new_note = note.Note(lowest_note.pitch)
                new_note.duration = element.duration
                new_note.offset = element.offset
                if element.tie is not None:
                    new_note.tie = element.tie
                
                if first_note:
                    new_part.append(new_note)
                    first_note = False
                    found_note = True
                    prev_offset = element.offset
                else:
                   if element.offset != prev_offset:
                    new_part.append(new_note)
                   prev_offset = element.offset

            else:
                new_part.append(element)  # Keep all other elements

        
        new_score.append(new_part)
    
    return new_score

def count_accidentals(score):
    """Counts the number of sharps and flats in a score."""
    accidentals_count = 0
    for element in score.flatten().getElementsByClass(['Note', 'Chord']):
        if isinstance(element, note.Note):
            if element.pitch.accidental:
                if element.pitch.accidental.alter != 0 :
                    accidentals_count += 1
        elif isinstance(element, chord.Chord):
            for pitch in element.pitches:
                if pitch.accidental:
                    if pitch.accidental.alter != 0 :
                       accidentals_count += 1
    
    for ks in score.flatten().getElementsByClass('KeySignature'):
        accidentals_count += abs(ks.sharps)
    return accidentals_count


def normalise_transpose(score):
    """
    Transposes a score to find the key with the minimum number of accidentals.

    Args:
        score: A music21.stream.Score object.

    Returns:
        A transposed music21.stream.Score object with the minimum number of accidentals.
    """
    original_score = score
    min_accidentals = float('inf')
    best_transposed_score = None

    for semitones in range(0, 12):
        transposed_score = score.transpose(semitones)
        accidentals = count_accidentals(transposed_score)

        if accidentals < min_accidentals:
            min_accidentals = accidentals
            best_transposed_score = transposed_score

    if best_transposed_score is None:
       return original_score
    else:
        return best_transposed_score