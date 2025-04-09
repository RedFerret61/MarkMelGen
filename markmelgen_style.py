#!/usr/bin/env python
# -*- coding: utf-8 -*-
# MarkMelGen_Style.py
#
# style data and functions for MarkMelGen
#
# free and open-source software, Paul Wardley Davies, see license.txt

import MarkMelGen_utilities
import copy
import logging
import io
import os
import sys
# import json
import pickle

from contextlib import redirect_stdout
from logging_config import logger
from MarkMelGen_utilities import *
from music21 import *
from music21 import meter
from showscore import show


MARKMELGEN_VERSION = "2.0.0"

def are_dictionaries_the_same(dict1, dict2):
    """
    Compare two dictionaries and return the first difference found.
    If no differences are found, return True.
    """
    for key in dict1:
        if key not in dict2:
            return f"Key {key} found in dict1 but not in dict2"
        if dict1[key] != dict2[key]:
            return f"Difference found at key {key}: {dict1[key]} != {dict2[key]}"
    
    for key in dict2:
        if key not in dict1:
            return f"Key {key} found in dict2 but not in dict1"
    
    return True


#v2 pickle
def write_transition_probabilities_to_disk(transition_probabilities, style_path, transition_name):
    """
    Writes transition probabilities to disk as a pickle file.

    Args:
        transition_probabilities (dict): The transition probabilities dictionary.
        style_path (str): The path to the style directory.
        transition_name (str): The name of the transition (e.g., "note_transition_probabilities", "duration_transition_probabilities").
    """
    file_path = os.path.join(style_path, f"{transition_name}.pkl")
    with open(file_path, 'wb') as f:
        pickle.dump(transition_probabilities, f)
    print(f"{transition_name} written to {file_path}")
    return

# v3 Pickle
def read_transition_probabilities_from_disk(style_path, transition_name):
    """
    Reads transition probabilities from disk.

    Args:
        style_path (str): The path to the style directory.
        transition_name (str): The name of the transition (e.g., "note_transition_probabilities", "duration_transition_probabilities").

    Returns:
        dict: The transition probabilities dictionary, or None if the file does not exist.
    """
    file_path = os.path.join(style_path, f"{transition_name}.pkl")
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return None

    with open(file_path, 'rb') as f:
        transition_probabilities = pickle.load(f)

    logger.debug(f"{transition_name} read from {file_path}")
    return transition_probabilities

def _extract_note_transitions_from_part(part, note_transitions, total_note_transitions):
    """
    Extracts note transitions from a single part of a score.
    """
    notes = [
        n for n in part.stripTies().flatten().notes if isinstance(n, note.Note)
    ]
    logger.debug(f"notes to calculate note_transition {notes}")
    for i in range(len(notes) - 2):
        prev_note = notes[i].name
        current_note = notes[i + 1].name
        next_note = notes[i + 2].name

        if (prev_note, current_note) not in note_transitions:
            note_transitions[(prev_note, current_note)] = {}
        if next_note not in note_transitions[(prev_note, current_note)]:
            note_transitions[(prev_note, current_note)][next_note] = 0
        note_transitions[(prev_note, current_note)][next_note] += 1
        if (prev_note, current_note) not in total_note_transitions:
            total_note_transitions[(prev_note, current_note)] = 0
        total_note_transitions[(prev_note, current_note)] += 1

    logger.debug(f"note_transitions {note_transitions}")
    logger.debug(f"total_note_transitions {total_note_transitions}")
    return


def calculate_note_transition_probabilities(note_transitions, total_note_transitions):
    note_transition_probabilities = {}
    for (prev_note, current_note), transitions in note_transitions.items():
        note_transition_probabilities[(prev_note, current_note)] = {
            next_note: count / total_note_transitions[(prev_note, current_note)]
            for next_note, count in transitions.items()
        }

    print("Note Transition Probabilities:")
    for (prev_note, current_note), transitions in note_transition_probabilities.items():
        print(f"{(prev_note, current_note)}: {transitions}")

    log_transition_analysis(
        note_transition_probabilities, "Note transition: transition"
    )

    return note_transition_probabilities

def _extract_rest_note_transitions_from_part(part,rest_note_transitions, total_rest_note_transitions):
    """
    Extracts rest_note transitions from a single part of a score.
    Modified to capture 2nd order Markov chains
    """
    rests_and_notes = [
        n for n in part.stripTies().flatten().notesAndRests if (isinstance(n, note.Note) or isinstance(n, note.Rest))
    ]

    # Add "0.0,0.0" to the start to set the start of the line
    # Create a dummy rest at the beginning to represent the start of the measure
    dummy_rest = note.Rest(quarterLength=0.0)
    rests_and_notes.insert(0, dummy_rest)

    logger.debug(f"notesAndRests to calculate rest_note_transition {rests_and_notes}")

    for i in range(len(rests_and_notes) - 2):  # Iterate up to the third-to-last element
        prev = rests_and_notes[i]
        current = rests_and_notes[i+1]
        next_element = rests_and_notes[i+2]
        
        prev_duration = str(prev.duration.quarterLength)
        current_duration = str(current.duration.quarterLength)

        # the next_duration is stored as a float instead of a string by directly 
        # using next_element.duration.quarterLength without converting it to string.
        next_duration = next_element.duration.quarterLength

        combined_key = (prev_duration, current_duration)

        if combined_key not in rest_note_transitions:
            rest_note_transitions[combined_key] = {}

        if next_duration not in rest_note_transitions[combined_key]:
            rest_note_transitions[combined_key][next_duration] = 0

        if i == 0:  # If this is the first iteration, assume prev_duration and current_duration are "0.0,0.0"
            first_combined_key = ("0.0", "0.0")
            if first_combined_key not in rest_note_transitions:
                rest_note_transitions[first_combined_key] = {}
            if next_duration not in rest_note_transitions[first_combined_key]:
                rest_note_transitions[first_combined_key][next_duration] = 0
            rest_note_transitions[first_combined_key][next_duration] += 1
            if first_combined_key not in total_rest_note_transitions:
                total_rest_note_transitions[first_combined_key] = 0
            total_rest_note_transitions[first_combined_key] += 1
            

        rest_note_transitions[combined_key][next_duration] += 1

        if combined_key not in total_rest_note_transitions:
            total_rest_note_transitions[combined_key] = 0

        total_rest_note_transitions[combined_key] += 1

    logger.debug(f"rest_note_transitions {rest_note_transitions}")
    logger.debug(f"total_rest_note_transitions {total_rest_note_transitions}")
    return

def calculate_rest_note_transition_probabilities(rest_note_transitions, total_rest_note_transitions):
    rest_note_transition_probabilities = {}
    for (prev_duration, current_duration), transitions in rest_note_transitions.items():
        rest_note_transition_probabilities[(prev_duration, current_duration)] = {
            next_duration: count / total_rest_note_transitions[(prev_duration, current_duration)]
            for next_duration, count in transitions.items()
        }

    print("Rest Note Transition Probabilities:")
    for (prev_duration, current_duration), transitions in rest_note_transition_probabilities.items():
        print(f"{(prev_duration, current_duration)}: {transitions}")

    log_transition_analysis(rest_note_transition_probabilities, "Rest Note transition: transition")
    return rest_note_transition_probabilities

def _extract_bpm_transitions_from_part(part, time_signature, bpm_transitions, total_bpm_transitions):
    """
    Extracts bpm (beat placement) transitions from a single part of a score.
    """
    notes = [n for n in part.stripTies().flatten().notes if isinstance(n, note.Note)]
    logger.debug(f"notes to calculate bpm_transition {notes}")

    for i in range(len(notes) - 2):
        prev_note = notes[i]
        current_note = notes[i + 1]
        next_note = notes[i + 2]
        
        prev_bp = fractional_part_as_fraction(prev_note.beat, time_signature)
        current_bp = fractional_part_as_fraction(current_note.beat, time_signature)
        next_bp = fractional_part_as_fraction(next_note.beat, time_signature)

        key = (str(prev_bp), str(current_bp))

        if key not in bpm_transitions:
            bpm_transitions[key] = {}
        if next_bp not in bpm_transitions[key]:
            bpm_transitions[key][next_bp] = 0
        bpm_transitions[key][next_bp] += 1

        if key not in total_bpm_transitions:
            total_bpm_transitions[key] = 0
        total_bpm_transitions[key] += 1

    logger.debug(f"bpm_transitions: {bpm_transitions}")
    logger.debug(f"total_bpm_transitions: {total_bpm_transitions}")

    return

def calculate_bpm_transition_probabilities(bpm_transitions, total_bpm_transitions):
    """
    Calculates the transition probabilities for bpm (beat placement).
    """
    bpm_transition_probabilities = {}
    for (prev_bp, current_bp), transitions in bpm_transitions.items():
        bpm_transition_probabilities[(prev_bp, current_bp)] = {
            next_bp: count / total_bpm_transitions[(prev_bp, current_bp)]
            for next_bp, count in transitions.items()
        }
    
    print("BPM Transition Probabilities:")
    for (prev_bp, current_bp), transitions in bpm_transition_probabilities.items():
        print(f"{(prev_bp, current_bp)}: {transitions}")

    log_transition_analysis(bpm_transition_probabilities, "BPM transition: transition")
    return bpm_transition_probabilities

def _extract_dtransitions_from_part(part, dtransitions, total_dtransitions):
    """
    Extracts duration transitions from a single part of a score.
    Does not filter out tuple durations.
    """
    notes = [n for n in part.stripTies().flatten().notes if isinstance(n, note.Note)]
    logger.debug(f"notes to calculate dtransition {notes}")
    for i in range(len(notes) - 2):  # Iterate up to the third-to-last element
        prev_note = notes[i]
        current_note = notes[i + 1]
        next_note = notes[i + 2]

        # Skip notes with tuple durations
        # if prev_note.duration.tuplets or current_note.duration.tuplets or next_note.duration.tuplets:
        #     logger.debug(f"Skipping prev/curr/next tuple durations ql & tuplets: {prev_note.duration.quarterLength} {prev_note.duration.tuplets}, {current_note.duration.quarterLength} {current_note.duration.tuplets}, {next_note.duration.quarterLength} {next_note.duration.tuplets}")
        #     continue

        prev_duration = str(prev_note.duration.quarterLength)
        current_duration = str(current_note.duration.quarterLength)
        # the next_duration is stored as a float instead of a string by directly 
        # using next_note.duration.quarterLength without converting it to string.
        next_duration = next_note.duration.quarterLength

        combined_key = (prev_duration, current_duration)

        if combined_key not in dtransitions:
            dtransitions[combined_key] = {}
        if next_duration not in dtransitions[combined_key]:
            dtransitions[combined_key][next_duration] = 0
        dtransitions[combined_key][next_duration] += 1

        if combined_key not in total_dtransitions:
            total_dtransitions[combined_key] = 0
        total_dtransitions[combined_key] += 1

    logger.debug(f"dtransitions: {dtransitions}")
    logger.debug(f"total_dtransitions: {total_dtransitions}")
    return

def calculate_dtransition_probabilities(dtransitions, total_dtransitions):
    """
    Calculates the transition probabilities for durations.
    """
    dtransition_probabilities = {}
    for (prev_duration, current_duration), transitions in dtransitions.items():
        dtransition_probabilities[(prev_duration, current_duration)] = {
            next_duration: count / total_dtransitions[(prev_duration, current_duration)]
            for next_duration, count in transitions.items()
        }
    
    print("Duration Transition Probabilities:")
    for (prev_duration, current_duration), transitions in dtransition_probabilities.items():
        print(f"{(prev_duration, current_duration)}: {transitions}")

    log_transition_analysis(dtransition_probabilities, "Duration transition: transition")
    return dtransition_probabilities

# v1 gemini
# def _extract_cad_dtransitions_from_part(part,cad_dtransitions, total_cad_dtransitions):
#     """
#     Extracts cadence transitions from a single part of a score.
#      where cad_dtransition is a dictionary that stores the cadence transition probabilities learned from a corpus of musical pieces, that enables picking a note that is likely to follow the previous two notes.
#     """
#     notes_and_rests = [n for n in part.stripTies().flatten().notesAndRests]

#     for i in range(len(notes_and_rests) - 2):
#         if isinstance(notes_and_rests[i], note.Rest):
#             continue
        
#         # Check for a potential cadence
#         is_cadence = False
        
#         #check if the next element is a rest
#         for element_num in range((i + 1), len(notes_and_rests)):
#           if (type(notes_and_rests[element_num]) == music21.note.Rest):
#             is_cadence = True
#             break
#           elif (type(notes_and_rests[element_num]) == music21.note.Note):
#             break

#         # Check if this is the last note
#         if i + 2 == len(notes_and_rests):
#           is_cadence = True


#         if not is_cadence:
#           continue

#         prev_note_1 = notes_and_rests[i]
#         prev_note_2 = notes_and_rests[i+1]
#         current_note = notes_and_rests[i+2]

#         if not isinstance(prev_note_1, note.Note) or not isinstance(prev_note_2, note.Note) or not isinstance(current_note, note.Note):
#             continue

#         key = (prev_note_1.name, prev_note_2.name)
#         if key not in cad_dtransitions:
#             cad_dtransitions[key] = {}
#         if current_note.name not in cad_dtransitions[key]:
#             cad_dtransitions[key][current_note.name] = 0
#         cad_dtransitions[key][current_note.name] += 1

#         if key not in total_cad_dtransitions:
#             total_cad_dtransitions[key] = 0
#         total_cad_dtransitions[key] += 1

#     logger.debug(f"cad_dtransitions {cad_dtransitions}")
#     logger.debug(f"total_cad_dtransitions {total_cad_dtransitions}")

#     return

# v2 copilot
# def _extract_cad_dtransitions_from_part(part, cad_dtransitions, total_cad_dtransitions):
#     """
#     Extracts cadence transitions from a single part of a score.
#     If no cadence transitions are found, use the last three notes of the file to create an entry in the cad_dtransitions.
#     """
#     notes_and_rests = [n for n in part.stripTies().flatten().notesAndRests]
#     logger.debug(f"notes_and_rests to calculate cad_dtransition {notes_and_rests}")

#     found_cadence = False

#     for i in range(len(notes_and_rests) - 2):
#         if isinstance(notes_and_rests[i], note.Rest):
#             continue
        
#         # Check for a potential cadence
#         is_cadence = False
        
#         # Check if the next element is a rest
#         for element_num in range((i + 1), len(notes_and_rests)):
#             if isinstance(notes_and_rests[element_num], note.Rest):
#                 is_cadence = True
#                 break
#             elif isinstance(notes_and_rests[element_num], note.Note):
#                 break

#         # Check if this is the last note
#         if i + 2 == len(notes_and_rests):
#             is_cadence = True

#         if not is_cadence:
#             continue

#         prev_note_1 = notes_and_rests[i]
#         prev_note_2 = notes_and_rests[i + 1]
#         current_note = notes_and_rests[i + 2]

#         if not isinstance(prev_note_1, note.Note) or not isinstance(prev_note_2, note.Note) or not isinstance(current_note, note.Note):
#             continue

#         key = (prev_note_1.name, prev_note_2.name)
#         if key not in cad_dtransitions:
#             cad_dtransitions[key] = {}
#         if current_note.name not in cad_dtransitions[key]:
#             cad_dtransitions[key][current_note.name] = 0
#         cad_dtransitions[key][current_note.name] += 1

#         if key not in total_cad_dtransitions:
#             total_cad_dtransitions[key] = 0
#         total_cad_dtransitions[key] += 1

#         found_cadence = True

#     # If no cadences were found, use the last three notes of the file
#     if not found_cadence and len(notes_and_rests) >= 3:
#         prev_note_1 = notes_and_rests[-3]
#         prev_note_2 = notes_and_rests[-2]
#         current_note = notes_and_rests[-1]

#         if isinstance(prev_note_1, note.Note) and isinstance(prev_note_2, note.Note) and isinstance(current_note, note.Note):
#             key = (prev_note_1.name, prev_note_2.name)
#             if key not in cad_dtransitions:
#                 cad_dtransitions[key] = {}
#             if current_note.name not in cad_dtransitions[key]:
#                 cad_dtransitions[key][current_note.name] = 0
#             cad_dtransitions[key][current_note.name] += 1

#             if key not in total_cad_dtransitions:
#                 total_cad_dtransitions[key] = 0
#             total_cad_dtransitions[key] += 1

#     logger.debug(f"cad_dtransitions {cad_dtransitions}")
#     logger.debug(f"total_cad_dtransitions {total_cad_dtransitions}")

#     return

#v3 copilot use 3 notes before a rest 
# def _extract_cad_dtransitions_from_part(part, cad_dtransitions, total_cad_dtransitions):
#     """
#     Extracts cadence transitions from a single part of a score.
#     If no cadence transitions are found, use the last three notes of the file to create an entry in the cad_dtransitions.
#     """
#     notes_and_rests = [n for n in part.stripTies().flatten().notesAndRests]
#     logger.debug(f"notes_and_rests to calculate cad_dtransition {notes_and_rests}")

#     found_cadence = False

#     for i in range(len(notes_and_rests) - 2):
#         if isinstance(notes_and_rests[i], note.Rest):
#             continue
        
#         # Check for a potential cadence
#         is_cadence = False
        
#         # Check if the next element is a rest
#         for element_num in range((i + 1), len(notes_and_rests)):
#             if isinstance(notes_and_rests[element_num], note.Rest):
#                 is_cadence = True
#                 break
#             elif isinstance(notes_and_rests[element_num], note.Note):
#                 break

#         # Check if this is the last note
#         if i + 2 == len(notes_and_rests):
#             is_cadence = True

#         if not is_cadence:
#             continue

#         prev_note_1 = notes_and_rests[i]
#         prev_note_2 = notes_and_rests[i + 1]
#         current_note = notes_and_rests[i + 2]

#         if not isinstance(prev_note_1, note.Note) or not isinstance(prev_note_2, note.Note) or not isinstance(current_note, note.Note):
#             continue

#         key = (prev_note_1.name, prev_note_2.name)
#         if key not in cad_dtransitions:
#             cad_dtransitions[key] = {}
#         if current_note.name not in cad_dtransitions[key]:
#             cad_dtransitions[key][current_note.name] = 0
#         cad_dtransitions[key][current_note.name] += 1

#         if key not in total_cad_dtransitions:
#             total_cad_dtransitions[key] = 0
#         total_cad_dtransitions[key] += 1

#         found_cadence = True

#     # If no cadences were found, use the last three notes of the file
#     if not found_cadence and len(notes_and_rests) >= 3:
#         prev_note_1 = notes_and_rests[-3]
#         prev_note_2 = notes_and_rests[-2]
#         current_note = notes_and_rests[-1]

#         if isinstance(prev_note_1, note.Note) and isinstance(prev_note_2, note.Note) and isinstance(current_note, note.Note):
#             key = (prev_note_1.name, prev_note_2.name)
#             if key not in cad_dtransitions:
#                 cad_dtransitions[key] = {}
#             if current_note.name not in cad_dtransitions[key]:
#                 cad_dtransitions[key][current_note.name] = 0
#             cad_dtransitions[key][current_note.name] += 1

#             if key not in total_cad_dtransitions:
#                 total_cad_dtransitions[key] = 0
#             total_cad_dtransitions[key] += 1

#     # If no cadences were found, check for three notes before a rest
#     if not found_cadence:
#         for i in range(len(notes_and_rests) - 3):
#             if isinstance(notes_and_rests[i], note.Note) and isinstance(notes_and_rests[i + 1], note.Note) and isinstance(notes_and_rests[i + 2], note.Note) and isinstance(notes_and_rests[i + 3], note.Rest):
#                 prev_note_1 = notes_and_rests[i]
#                 prev_note_2 = notes_and_rests[i + 1]
#                 current_note = notes_and_rests[i + 2]

#                 key = (prev_note_1.name, prev_note_2.name)
#                 if key not in cad_dtransitions:
#                     cad_dtransitions[key] = {}
#                 if current_note.name not in cad_dtransitions[key]:
#                     cad_dtransitions[key][current_note.name] = 0
#                 cad_dtransitions[key][current_note.name] += 1

#                 if key not in total_cad_dtransitions:
#                     total_cad_dtransitions[key] = 0
#                 total_cad_dtransitions[key] += 1

#                 found_cadence = True
#                 break

#     logger.debug(f"cad_dtransitions {cad_dtransitions}")
#     logger.debug(f"total_cad_dtransitions {total_cad_dtransitions}")

#     return

# v4 copilot
def _extract_cad_transitions_from_part(part, cad_transitions, total_cad_transitions):
    """
    Extracts cadence transitions from a single part of a score.
    If no cadence transitions are found, use the last three notes of the file to create an entry in the cad_dtransitions.
    """
    notes_and_rests = [n for n in part.stripTies().flatten().notesAndRests]
    logger.debug(f"notes_and_rests to calculate cad_dtransition {notes_and_rests}")

    found_cadence = False

    for i in range(len(notes_and_rests) - 3):
        if isinstance(notes_and_rests[i], note.Note) and isinstance(notes_and_rests[i + 1], note.Note) and isinstance(notes_and_rests[i + 2], note.Note) and isinstance(notes_and_rests[i + 3], note.Rest):
            prev_note_1 = notes_and_rests[i]
            prev_note_2 = notes_and_rests[i + 1]
            current_note = notes_and_rests[i + 2]

            if not isinstance(prev_note_1, note.Note) or not isinstance(prev_note_2, note.Note) or not isinstance(current_note, note.Note):
                continue

            key = (prev_note_1.name, prev_note_2.name)
            if key not in cad_transitions:
                cad_transitions[key] = {}
            if current_note.name not in cad_transitions[key]:
                cad_transitions[key][current_note.name] = 0
            cad_transitions[key][current_note.name] += 1

            if key not in total_cad_transitions:
                total_cad_transitions[key] = 0
            total_cad_transitions[key] += 1

            found_cadence = True

    # If no cadences were found, use the last three notes of the file
    if not found_cadence and len(notes_and_rests) >= 3:
        prev_note_1 = notes_and_rests[-3]
        prev_note_2 = notes_and_rests[-2]
        current_note = notes_and_rests[-1]

        if isinstance(prev_note_1, note.Note) and isinstance(prev_note_2, note.Note) and isinstance(current_note, note.Note):
            key = (prev_note_1.name, prev_note_2.name)
            if key not in cad_transitions:
                cad_transitions[key] = {}
            if current_note.name not in cad_transitions[key]:
                cad_transitions[key][current_note.name] = 0
            cad_transitions[key][current_note.name] += 1

            if key not in total_cad_transitions:
                total_cad_transitions[key] = 0
            total_cad_transitions[key] += 1

    logger.debug(f"cad_transitions {cad_transitions}")
    logger.debug(f"total_cad_transitions {total_cad_transitions}")

    return

def calculate_cad_transition_probabilities(cad_transitions, total_cad_transitions):
    """
    Calculates the transition probabilities for cadences.
    """
    cad_dtransition_probabilities = {}
    for (prev_note, current_note), transitions in cad_transitions.items():
        cad_dtransition_probabilities[(prev_note, current_note)] = {
            next_note: count / total_cad_transitions[(prev_note, current_note)]
            for next_note, count in transitions.items()
        }

    print("Cadence Transition Probabilities:")
    for (prev_note, current_note), transitions in cad_dtransition_probabilities.items():
        print(f"{(prev_note, current_note)}: {transitions}")

    log_transition_analysis(cad_dtransition_probabilities, "Cadence transition: transition")
    return cad_dtransition_probabilities

# v1 copilot
# def _extract_cad_dtransitions_from_part(part, cad_dtransitions, total_cad_dtransitions):
#     """
#     Extracts cadence duration transitions from a single part of a score.
#     """
#     notes_and_rests = [n for n in part.stripTies().flatten().notesAndRests]
#     logger.debug(f"notes_and_rests to calculate cad_dtransition {notes_and_rests}")

#     for i in range(len(notes_and_rests) - 3):
#         if isinstance(notes_and_rests[i], note.Note) and isinstance(notes_and_rests[i + 1], note.Note) and isinstance(notes_and_rests[i + 2], note.Note) and isinstance(notes_and_rests[i + 3], note.Rest):
#             prev_note_1 = notes_and_rests[i]
#             prev_note_2 = notes_and_rests[i + 1]
#             current_note = notes_and_rests[i + 2]

#             if not isinstance(prev_note_1, note.Note) or not isinstance(prev_note_2, note.Note) or not isinstance(current_note, note.Note):
#                 continue

#             key = (str(prev_note_1.duration.quarterLength), str(prev_note_2.duration.quarterLength))
#             if key not in cad_dtransitions:
#                 cad_dtransitions[key] = {}
#             if str(current_note.duration.quarterLength) not in cad_dtransitions[key]:
#                 cad_dtransitions[key][str(current_note.duration.quarterLength)] = 0
#             cad_dtransitions[key][str(current_note.duration.quarterLength)] += 1

#             if key not in total_cad_dtransitions:
#                 total_cad_dtransitions[key] = 0
#             total_cad_dtransitions[key] += 1

#     logger.debug(f"cad_dtransitions {cad_dtransitions}")
#     logger.debug(f"total_cad_dtransitions {total_cad_dtransitions}")

#     return

#v2 copilot last 3 notes of file
def _extract_cad_dtransitions_from_part(part, cad_dtransitions, total_cad_dtransitions):
    """
    Extracts cadence duration transitions from a single part of a score.
    """
    notes_and_rests = [n for n in part.stripTies().flatten().notesAndRests]
    logger.debug(f"notes_and_rests to calculate cad_dtransition {notes_and_rests}")

    for i in range(len(notes_and_rests) - 3):
        if isinstance(notes_and_rests[i], note.Note) and isinstance(notes_and_rests[i + 1], note.Note) and isinstance(notes_and_rests[i + 2], note.Note) and isinstance(notes_and_rests[i + 3], note.Rest):
            prev_note_1 = notes_and_rests[i]
            prev_note_2 = notes_and_rests[i + 1]
            current_note = notes_and_rests[i + 2]

            if not isinstance(prev_note_1, note.Note) or not isinstance(prev_note_2, note.Note) or not isinstance(current_note, note.Note):
                continue

            # Skip cadence notes with tuple durations
            # if prev_note_1.duration.tuplets or prev_note_2.duration.tuplets or current_note.duration.tuplets:
            #     logger.debug(f"Skipping cadence prev/curr/next tuple durations ql & tuplets: {prev_note_1.duration.quarterLength} {prev_note_1.duration.tuplets}, {prev_note_2.duration.quarterLength} {prev_note_2.duration.tuplets}, {current_note.duration.quarterLength} {current_note.duration.tuplets}")
            #     continue

            key = (str(prev_note_1.duration.quarterLength), str(prev_note_2.duration.quarterLength))
            if key not in cad_dtransitions:
                cad_dtransitions[key] = {}

            # if str(current_note.duration.quarterLength) not in cad_dtransitions[key]:
            #     cad_dtransitions[key][str(current_note.duration.quarterLength)] = 0
            # cad_dtransitions[key][str(current_note.duration.quarterLength)] += 1
            if current_note.duration.quarterLength not in cad_dtransitions[key]:
                cad_dtransitions[key][current_note.duration.quarterLength] = 0
            cad_dtransitions[key][current_note.duration.quarterLength] += 1

            if key not in total_cad_dtransitions:
                total_cad_dtransitions[key] = 0
            total_cad_dtransitions[key] += 1

    # If no cadences were found, use the last three notes of the file
    if len(notes_and_rests) >= 3:
        prev_note_1 = notes_and_rests[-3]
        prev_note_2 = notes_and_rests[-2]
        current_note = notes_and_rests[-1]

        if isinstance(prev_note_1, note.Note) and isinstance(prev_note_2, note.Note) and isinstance(current_note, note.Note):
            key = (str(prev_note_1.duration.quarterLength), str(prev_note_2.duration.quarterLength))
            if key not in cad_dtransitions:
                cad_dtransitions[key] = {}

            # if str(current_note.duration.quarterLength) not in cad_dtransitions[key]:
            #     cad_dtransitions[key][str(current_note.duration.quarterLength)] = 0
            # cad_dtransitions[key][str(current_note.duration.quarterLength)] += 1
            if current_note.duration.quarterLength not in cad_dtransitions[key]:
                cad_dtransitions[key][current_note.duration.quarterLength] = 0
            cad_dtransitions[key][current_note.duration.quarterLength] += 1

            if key not in total_cad_dtransitions:
                total_cad_dtransitions[key] = 0
            total_cad_dtransitions[key] += 1

    logger.debug(f"cad_dtransitions {cad_dtransitions}")
    logger.debug(f"total_cad_dtransitions {total_cad_dtransitions}")

    return


def calculate_cad_dtransition_probabilities(cad_dtransitions, total_cad_dtransitions):
    """
    Calculates the transition probabilities for cadence durations.
    """
    cad_dtransition_probabilities = {}
    for (prev_duration, current_duration), transitions in cad_dtransitions.items():
        cad_dtransition_probabilities[(prev_duration, current_duration)] = {
            next_duration: count / total_cad_dtransitions[(prev_duration, current_duration)]
            for next_duration, count in transitions.items()
        }

    print("Cadence Duration Transition Probabilities:")
    for (prev_duration, current_duration), transitions in cad_dtransition_probabilities.items():
        print(f"{(prev_duration, current_duration)}: {transitions}")

    log_transition_analysis(cad_dtransition_probabilities, "Cadence Duration transition: transition")
    return cad_dtransition_probabilities

# def load_transitions_from_style(style_path):
#     """
#     Loads transition probabilities from pickle files in the specified style path.

#     Args:
#         style_path (str): The path to the directory containing the style files.

#     Returns:
#         tuple: A tuple containing the loaded transition probabilities:
#                (transition, bpm_transition, dtransition, cad_transition, cad_dtransition, rest_note_transition).
#                Returns (None, None, None, None, None, None) if any file is not found or if there is an error.
#     """
#     try:
#         # Define filenames
#         transition_filename = "note_transition_probabilities.pkl"
#         bpm_transition_filename = "bpm_transition_probabilities.pkl"
#         dtransition_filename = "dtransition_probabilities.pkl"
#         cad_transition_filename = "cad_transition_probabilities.pkl"
#         cad_dtransition_filename = "cad_dtransition_probabilities.pkl"
#         rest_note_transition_filename = "rest_note_transition_probabilities.pkl"

#         # Construct full file paths
#         transition_file = os.path.join(style_path, transition_filename)
#         bpm_transition_file = os.path.join(style_path, bpm_transition_filename)
#         dtransition_file = os.path.join(style_path, dtransition_filename)
#         cad_transition_file = os.path.join(style_path, cad_transition_filename)
#         cad_dtransition_file = os.path.join(style_path, cad_dtransition_filename)
#         rest_note_transition_file = os.path.join(style_path, rest_note_transition_filename)

#         # Load transitions from files
#         with open(transition_file, "rb") as f:
#             transition = pickle.load(f)

#         with open(bpm_transition_file, "rb") as f:
#             bpm_transition = pickle.load(f)

#         with open(dtransition_file, "rb") as f:
#             dtransition = pickle.load(f)

#         with open(cad_transition_file, "rb") as f:
#             cad_transition = pickle.load(f)

#         with open(cad_dtransition_file, "rb") as f:
#             cad_dtransition = pickle.load(f)

#         with open(rest_note_transition_file, "rb") as f:
#             rest_note_transition = pickle.load(f)

#         return (
#             transition,
#             bpm_transition,
#             dtransition,
#             cad_transition,
#             cad_dtransition,
#             rest_note_transition,
#         )

#     except FileNotFoundError as e:
#         logger.error(f"Error loading transition files: {e}")
#         return None, None, None, None, None, None
#     except Exception as e:
#         logger.error(f"An unexpected error occurred: {e}")
#         return None, None, None, None, None, None

def load_transition_files(style_path):
    try:
        # Load transition
        transition_file = os.path.join(style_path, "note_transition_probabilities.pkl")
        with open(transition_file, "rb") as f:
            transition = pickle.load(f)

        # Load bpm_transition
        bpm_transition_file = os.path.join(style_path, "bpm_transition_probabilities.pkl")
        with open(bpm_transition_file, "rb") as f:
            bpm_transition = pickle.load(f)

        # Load dtransition
        dtransition_file = os.path.join(style_path, "dtransition_probabilities.pkl")
        with open(dtransition_file, "rb") as f:
            dtransition = pickle.load(f)

        # Load cad_transition
        cad_transition_file = os.path.join(style_path, "cad_transition_probabilities.pkl")
        with open(cad_transition_file, "rb") as f:
            cad_transition = pickle.load(f)

        # Load cad_dtransition
        cad_dtransition_file = os.path.join(style_path, "cad_dtransition_probabilities.pkl")
        with open(cad_dtransition_file, "rb") as f:
            cad_dtransition = pickle.load(f)

        # Load rest_note_transition
        rest_note_transition_file = os.path.join(style_path, "rest_note_transition_probabilities.pkl")
        with open(rest_note_transition_file, "rb") as f:
            rest_note_transition = pickle.load(f)

        return transition, bpm_transition, dtransition, cad_transition, cad_dtransition, rest_note_transition

    except FileNotFoundError as e:
        print(f"Error loading transition files: {e}")
        return None, None, None, None, None, None
    

def process_mxl_file(file_path, note_transitions, total_note_transitions, rest_note_transitions, total_rest_note_transitions, bpm_transitions, total_bpm_transitions, dtransitions, total_dtransitions, cad_transitions, total_cad_transitions, cad_dtransitions, total_cad_dtransitions, display_html):
       
    print(f"Processing file: {file_path}")
    score = converter.parse(file_path)

    # Redirect stdout to capture show('text') output
    f = io.StringIO()
    with redirect_stdout(f):
        score.show('text')
    out = f.getvalue()
    logger.debug(f"{file_path} score.show('text')\n{out}")

    # Set or append to the title
    append_or_set_title(score, "Parse.")

    # remove MetronomeMarks to avoid a bug in OSMD: e.g
    # Error rendering data:TypeError: Cannot read properties of undefined (reading 'TempoExpressions')
    for el in score[tempo.MetronomeMark]:
        el.activeSite.remove(el)
    if display_html:
        show(score)

    # Log the analysis results of the melody notes
    log_analyze_melody_notes(score, "input Melody before transpose")

    # Remove grace notes
    cleaned_melody = remove_zero_length_notes(score)

    # Set or append to the title
    append_or_set_title(score, "Graceless.")

    mono_melody = convert_to_monophonic(cleaned_melody)
    append_or_set_title(mono_melody, "Mono.")

    # Log the analysis results of the melody notes
    log_analyze_melody_notes(mono_melody, "input Melody after convert_to_monophonic")

    # Transpose the score to the key with the minimum number of sharps or flats
    transposed_score = normalise_transpose(mono_melody)

    # Redirect stdout to capture show('text') output
    f = io.StringIO()
    with redirect_stdout(f):
        transposed_score.show('text')
    out = f.getvalue()
    logger.debug(f"{file_path} transposed_score.show('text')\n{out}")

    # Set or append to the title
    append_or_set_title(transposed_score, "Transpose.")
    if display_html:
        show(transposed_score)
    # Log the analysis results of the melody notes
    log_analyze_melody_notes(transposed_score, "input Melody after transpose")

    time_signature = get_first_time_signature(transposed_score)
    logger.debug(f"time_signature: {time_signature}")

    for part in transposed_score.parts:
        _extract_note_transitions_from_part(part,note_transitions, total_note_transitions)
        _extract_rest_note_transitions_from_part(part,rest_note_transitions,total_rest_note_transitions)
        _extract_bpm_transitions_from_part(part, time_signature, bpm_transitions, total_bpm_transitions)
        _extract_dtransitions_from_part(part, dtransitions, total_dtransitions)
        _extract_cad_transitions_from_part(part, cad_transitions, total_cad_transitions)
        _extract_cad_dtransitions_from_part(part, cad_dtransitions, total_cad_dtransitions)

    return


def create_style(input_path, display_html, INPUT_STYLE_PATH):
    
    logger.debug(f"create_style function called with parameters:")
    logger.debug(f"  input_path: {input_path}")
    logger.debug(f"  display_html: {display_html}")
    logger.debug(f"  INPUT_STYLE_PATH: {INPUT_STYLE_PATH}")

    note_transitions = {}
    total_note_transitions = {}
    rest_note_transitions = {}
    total_rest_note_transitions = {}
    bpm_transitions = {}
    total_bpm_transitions = {}
    dtransitions = {}
    total_dtransitions = {}
    cad_transitions = {}
    total_cad_transitions = {}
    cad_dtransitions = {}
    total_cad_dtransitions = {}

    mxl_files_found = False

    if os.path.isdir(input_path):
        print(f"Creating style from directory: {input_path}")
        for filename in os.listdir(input_path):
            if filename.endswith(".mxl"):
                mxl_files_found = True
                process_mxl_file(
                    os.path.join(input_path, filename),
                    note_transitions,
                    total_note_transitions,
                    rest_note_transitions,
                    total_rest_note_transitions,
                    bpm_transitions,
                    total_bpm_transitions,
                    dtransitions,
                    total_dtransitions,
                    cad_transitions,
                    total_cad_transitions,
                    cad_dtransitions,
                    total_cad_dtransitions,                    
                    display_html
                )
    else:
        print(f"Invalid path: {input_path}. The path must be a directory.")
        sys.exit(1)

    if not mxl_files_found:
        print(f"No .mxl files found in directory: {input_path}")
        sys.exit(1)

    note_transition_probabilities = calculate_note_transition_probabilities(
        note_transitions, total_note_transitions
    )
    log_transition_analysis(
        note_transition_probabilities, "Note transition: transition"
    )

    rest_note_transition_probabilities = calculate_rest_note_transition_probabilities(rest_note_transitions, total_rest_note_transitions)
    # rest_note_transition_probabilities = transition_frequency_to_probability(rest_note_transitions)

    log_transition_analysis(
        rest_note_transition_probabilities, "Rest Note transition: transition"
    )

    bpm_transition_probabilities = calculate_bpm_transition_probabilities(bpm_transitions, total_bpm_transitions)
    log_transition_analysis(
        bpm_transition_probabilities, "BPM transition: transition"
    )

    dtransition_probabilities = calculate_dtransition_probabilities(dtransitions, total_dtransitions)
    log_transition_analysis(
        dtransition_probabilities, "Duration transition: transition"
    )

    cad_transition_probabilities = calculate_cad_transition_probabilities(cad_transitions, total_cad_transitions)
    log_transition_analysis(
        cad_transition_probabilities, "Cadence transition: transition"
    )

    cad_dtransition_probabilities = calculate_cad_dtransition_probabilities(cad_dtransitions, total_cad_dtransitions)
    log_transition_analysis(
        cad_dtransition_probabilities, "Cadence Duration transition: transition"
    )

    # create new style directory
    # style_name = os.path.basename(os.path.normpath(input_path))
    # style_path = os.path.join("input", "style", style_name)
    style_name = os.path.basename(os.path.normpath(input_path))    
    style_path = os.path.join(INPUT_STYLE_PATH, style_name)
    os.makedirs(style_path, exist_ok=True)
    print(f"Created style directory: {style_path}")
    logger.debug(f"Created style directory: {style_path}")

    write_transition_probabilities_to_disk(note_transition_probabilities, style_path, "note_transition_probabilities")
    write_transition_probabilities_to_disk(rest_note_transition_probabilities, style_path, "rest_note_transition_probabilities")
    write_transition_probabilities_to_disk(bpm_transition_probabilities, style_path, "bpm_transition_probabilities")
    write_transition_probabilities_to_disk(dtransition_probabilities, style_path, "dtransition_probabilities")
    write_transition_probabilities_to_disk(cad_transition_probabilities, style_path, "cad_transition_probabilities")
    write_transition_probabilities_to_disk(cad_dtransition_probabilities, style_path, "cad_dtransition_probabilities")

    # Test reading
    read_probabilities = read_transition_probabilities_from_disk(style_path, "note_transition_probabilities")
    logger.debug(f"read_transition_probabilities_from_disk success, first key : {list(read_probabilities.keys())[0]} ")    
    log_transition_analysis(
        read_probabilities, "Note transition: read_probabilities"
    )

    read_rest_note_probabilities = read_transition_probabilities_from_disk(style_path, "rest_note_transition_probabilities")
    logger.debug(f"read_rest_note_probabilities success, first key : {list(read_rest_note_probabilities.keys())[0]} ")
    log_transition_analysis(
        read_rest_note_probabilities, "Rest Note transition: read_probabilities"
    )

    read_bpm_probabilities = read_transition_probabilities_from_disk(style_path, "bpm_transition_probabilities")
    logger.debug(f"read_bpm_probabilities success, first key : {list(read_bpm_probabilities.keys())[0]} ")      # log the first key of the dictionary           
    log_transition_analysis(
        read_bpm_probabilities, "BPM transition: read_probabilities"
    )

    read_dtransition_probabilities = read_transition_probabilities_from_disk(style_path, "dtransition_probabilities")
    logger.debug(f"read_dtransition_probabilities success, first key : {list(read_dtransition_probabilities.keys())[0]} ")
    log_transition_analysis(
        read_dtransition_probabilities, "Duration transition: read_probabilities"
    )

    read_cad_probabilities = read_transition_probabilities_from_disk(style_path, "cad_transition_probabilities")
    # logger.debug(f"read_cad_probabilities success, first key : {list(read_cad_probabilities.keys())[0]} ")
    if read_cad_probabilities:
        logger.debug(f"read_cad_probabilities success, first key : {list(read_cad_probabilities.keys())[0]} ")
    else:
        logger.debug("read_cad_probabilities failed to read or empty")

    log_transition_analysis(
        read_cad_probabilities, "Cadence transition: read_probabilities"
    )    

    read_cad_dtransition_probabilities = read_transition_probabilities_from_disk(style_path, "cad_dtransition_probabilities")
    if read_cad_dtransition_probabilities:
        logger.debug(f"read_cad_dtransition_probabilities success, first key : {list(read_cad_dtransition_probabilities.keys())[0]} ")
    else:
        logger.debug("read_cad_dtransition_probabilities failed to read or empty")

    log_transition_analysis(
        read_cad_dtransition_probabilities, "Cadence Duration transition: read_probabilities"
    )

    # Create a modified copy for testing
    # modified_read_probabilities = copy.deepcopy(read_probabilities)

    # Modify the copied dictionary to test
    # if modified_read_probabilities:  # Check if the dictionary is not empty
    #     first_key = list(modified_read_probabilities.keys())[0]  # Get the first key
    #     if modified_read_probabilities[first_key]: #check if the sub dictionary is not empty
    #         first_sub_key = list(modified_read_probabilities[first_key].keys())[0] # Get the first sub-key
    #         modified_read_probabilities[first_key][first_sub_key] += 0.01  # Modify the probability
    #         print(f"Modified read_probabilities: Added 0.01 to {first_key} -> {first_sub_key}")


    # Compare the dictionaries
    logger.debug("Comparing the Note transition probabilities dictionaries...")
    comparison_result = are_dictionaries_the_same(note_transition_probabilities, read_probabilities)
    # comparison_result = are_dictionaries_the_same(note_transition_probabilities, modified_read_probabilities)

    if comparison_result is True:
        logger.debug("The note_transition_probabilities and read_probabilities dictionaries are the same.")
    else:
        logger.debug(f"Differences found: {comparison_result}")

    # Compare the dictionaries
    logger.debug("Comparing the Rest Note transition probabilities dictionaries...")
    comparison_result = are_dictionaries_the_same(rest_note_transition_probabilities, read_rest_note_probabilities)

    if comparison_result is True:
        logger.debug("The rest_note_transition_probabilities and read_rest_note_probabilities dictionaries are the same.")
    else:
        logger.debug(f"Differences found: {comparison_result}")
    
    # Compare the dictionaries
    logger.debug("Comparing the BPM transition probabilities dictionaries...")      
    comparison_result = are_dictionaries_the_same(bpm_transition_probabilities, read_bpm_probabilities)

    if comparison_result is True:
        logger.debug("The bpm_transition_probabilities and read_bpm_probabilities dictionaries are the same.")
    else:
        logger.debug(f"Differences found: {comparison_result}") 

    # Compare the dictionaries
    logger.debug("Comparing the Duration transition probabilities dictionaries...")
    comparison_result = are_dictionaries_the_same(dtransition_probabilities, read_dtransition_probabilities)

    if comparison_result is True:
        logger.debug("The dtransition_probabilities and read_dtransition_probabilities dictionaries are the same.")
    else:
        logger.debug(f"Differences found: {comparison_result}")

    # Compare the dictionaries
    logger.debug("Comparing the Cadence transition probabilities dictionaries...")
    comparison_result = are_dictionaries_the_same(cad_transition_probabilities, read_cad_probabilities)
    if comparison_result is True:
        logger.debug("The cad_transition_probabilities and read_cad_probabilities dictionaries are the same.")
    else:
        logger.debug(f"Differences found: {comparison_result}")

    # Compare the dictionaries
    logger.debug("Comparing the Cadence duration transition probabilities dictionaries...")
    comparison_result = are_dictionaries_the_same(cad_dtransition_probabilities, read_cad_dtransition_probabilities)
    if comparison_result is True:
        logger.debug("The cad_dtransition_probabilities and read_cad_dtransition_probabilities dictionaries are the same.")
    else:
        logger.debug(f"Differences found: {comparison_result}")

    return 
