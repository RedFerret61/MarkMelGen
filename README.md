# MarkMelGen
MarkMelGen is a Markov Melody Generation python program that 
takes configuration, lyric, and example music files and 
creates a tune for the supplied words.

MarkMelGen allows the user to add some structure with lyrical sections (intro, verse, prechorus, chorus, solo, bridge, or outro) 
and line functions (such as copy, transpose, invert and reverse)
to develop the Markov melodies and so compose more memorable songs.

MarkMelGen demonstration video:

[![MarkMelGen video](assets/images/youtube1.png)](https://www.youtube.com/watch?v=cAxGzUqxgFw "MarkMelGen video")

MarkMelGen has been tested on: 
* Windows 10 21H2  
  - MarkMelGen 1.0.0 with MuseScore 4.0.0, Python 3.10.8, music21 v 8.1.0
    (where versions obtained using on Windows: Start winver, MarkMelGen: first line of standard output or top right of output MusicXML, MuseScore: Help About..., python: python --version music21: pip list)
* macOS Big Sur 11.6.1 
  - MarkMelGen 0.9.0 with MuseScore 3.6.2, Python 3.10.0, music21 v 7.1.0 
* Ubuntu 20.04
  - MarkMelGen 1.0.0 with MuseScore 3.2.3, Python 3.8.10, music21 v 8.1.0

**Table of Contents**

1. [WindowsInstall](#WindowsInstall)
2. [macOSInstall](#macOSInstall)
3. [UbuntuInstall](#UbuntuInstall)
4. [Configuration](#Configuration)
5. [InputLyrics](#InputLyrics)
6. [InputMusic](#InputMusic)
7. [Output](#Output)
8. [Tools](#Tools)
9. [Workflow](#Workflow)

*Note: GitHub has a full table of contents with links in the header icon (top left of the readme.md).*

---
## WindowsInstall
### MarkMelGen Installation instructions for Windows
Pre-requisites for MarkMelGen include MuseScore, Python, and Music21.

### MuseScore Windows installation
Browse to https://musescore.org/en/download
 
Download for Windows and run installer.
### Python Windows installation
 1. Firstly check python version required by Music21.
 See 
    * https://music21-mit.blogspot.com in October 2022 this stated 
    
            "V8 is the first to fully support Python 3.10" and 

    * https://web.mit.edu/music21/doc/installing/installWindows.html in October 2021 this stated 

            "Windows users should download and install Python version 3.8 or higher."
* For example
  * Python 3.10.8 worked for me with music21 version 8.1.0
  * Python 3.10.0 did not work for me with music21 version 7.1.0 (numpy not compatible)
  * Python 3.9.6 worked for me with music21 versions 6.7.1 and 7.1.0   
  
(if you have an old version of python you don't need then Start, search, add, click on Add or remove programs, click on the old Python version, Uninstall, Uninstall, Close. You may need to manually remove the old version from your path: e.g. Start, search, env, Edit the system environment variables, Environment Variables..., User variables, Path, Edit..., select line with the old python scripts e.g ...Python39\Scripts\, Delete, select old python e.g. ...Python39\, Delete, OK x3)

  

2. Browse to https://www.python.org/downloads/windows
    
    Download desired version (may not be the latest) and run.
    
    Select "Add Python to PATH". Install.


3. Check the new Python works: Start, search, cmd, click on Command Prompt, type:
   
    python --version

    Expect the version to be displayed e.g. Python 3.10.8

### Music21 Windows installation
 
1. Music21 Installation details at https://web.mit.edu/music21/doc/installing/installWindows.html

    At command prompt:

    pip install music21

2. Check music21 version installed with:

   pip list

3. Configure with (press return to accept defaults):

   python -m music21.configure

if you have problems and want to try different versions. Uninstall music21 with:

   pip uninstall music21

To upgrade music21 at a later date to the latest version, 'pip uninstall music21' then 'pip install music21' again.

### MarkMelGen Windows installation

#### Install MarkMelGen on Windows
 Download release zip to desired directory for MarkMelGen e.g. C:\Users\paul\Music and
 unzip with right click Extract All ... 
 (this creates a folder with the name of the zip file).
#### Run MarkMelGen on Windows 

 In a Command Prompt window change to install directory and run MarkMelGen e.g.:

    cd C:\Users\paul\Music\MarkMelGen-1.0.0
    run
    :: or
    MarkMelGen.py
    :: or
    python MarkMelGen.py -c MarkMelGen.conf


 Graphs of input and output should open in Photos, then MuseScore should open.  
 Press Space to start or stop playback.
 
When finished, Close MuseScore and on taskbar right click on Photos and Close all windows.

#### Run MarkMelGen demonstration configuration files on Windows

 In a Command Prompt window type run_conf to run the configuration files in the conf directory e.g.:

    run_conf
    :: or to run one conf file:
    python MarkMelGen.py -c conf/Greensleeves.conf


Several runs of MarkMelGen will occur. Follow instructions to press Enter or close windows to continue.  A Logfile is written and music XML files created in the output directory.
Provided MuseScore is installed to the default location, recent output should be displayed in MuseScore.
 
When finished, Close MuseScore.


MarkMelGen configurations demonstration video:

[![MarkMelGen video](assets/images/youtube2.png)](https://www.youtube.com/watch?v=NSwdJdkqDRk "MarkMelGen configurations video")



#### Run MarkMelGen test files

 In a Command Prompt window type run_conf_test to run the configuration files in the conf directory e.g.:


    :: to run one conf test file without graphs:
    python MarkMelGen.py -g -c conf/test/TONE_SCALE_ON_ANHEMITONIC.conf
    :: to run all the conf test files automatically 
    :: (without Pressing Enter or Closing Windows):
    run_conf_test

To see the run_conf_test batch file results, Start File Explorer and go to the output folder in your MarkMelGen install directory.
Double-click on a musicxml file to open it in MuseScore.
(First time right click open with Musescore).
When finished, Close MuseScore.

---

## macOSInstall
### MarkMelGen Installation instructions for macOS
Pre-requisites for MarkMelGen include MuseScore, Python, and Music21.

### MuseScore on macOS
See https://musescore.org/en/handbook/3/install-macos  

 1. Download for mac from https://musescore.org/en/download
 2. Double-click the DMG file to mount the disk image.
 3. Drag and drop the MuseScore icon to the Applications folder icon.
 4. Launch MuseScore from the Applications folder to complete setup.

### Python on macOS:
 1. Firstly check python version required by Music21.
see https://web.mit.edu/music21/doc/installing/installMac.html
in December 2021 this recommended Python 3.9 or later.

 2. Use https://docs.python.org/3/using/mac.html and https://www.python.org/downloads/macos/
 3. To check the installed version of python, click the Launchpad icon in the Dock, type Terminal in the search field, then click Terminal. Then type:
    

    python3 --version
    Python 3.10.0




### Music21 on macOS
 

1. Install Music21. In a Terminal type:


        pip3 install music21


2. Check music21 version installed with:

       pip3 list



#### Install MarkMelGen on macOS
 Download release zip to desired directory for MarkMelGen and unzip by double-clicking on the zipped file .
#### Run MarkMelGen on macOS

 In command prompt change to install directory, make run files executable and run MarkMelGen e.g.:

 ```  
 cd ~/MarkMelGen
 chmod a+x run*
 ./run.sh
 # or to run without graphs      
 python3 MarkMelGen.py -g -c MarkMelGen.conf
```


MuseScore should open.  
 Press Space to start or stop playback..
 
When finished:
* if you are running with graphs, on the Dock on the graph icon, click and close all the Windows.
* Close MuseScore.


#### Run MarkMelGen demonstration configuration files on macOS

 In a Command Prompt window type run_conf to run the configuration files in the conf directory e.g.:

    ./run_conf.sh
    :: or to run one conf file:
    python3 MarkMelGen.py -c conf/Greensleeves.conf


Several runs of MarkMelGen will occur. Follow instructions to press Enter or close windows to continue.  A Logfile is written and music XML files created in the output directory.
Provided MuseScore is installed to the default location, output should be displayed in MuseScore.
 
When finished, close any graph and MuseScore windows.


#### Run MarkMelGen test files on macOS

 In a Command Prompt window type run_conf_test to run the configuration files in the conf directory e.g.:


    # to run one conf test file without graphs:
    python3 MarkMelGen.py -g -c conf/test/TONE_SCALE_ON_ANHEMITONIC.conf
    # to run all the conf test files automatically 
    # (without Pressing Enter or Closing Windows):
    ./run_conf_test.sh

To see the run_conf_test file results, go to the output folder in your MarkMelGen install directory.
Open desired musicxml file in MuseScore. When finished, Close MuseScore.

---

## UbuntuInstall

### MarkMelGen Installation instructions for Ubuntu
Pre-requisites for MarkMelGen include MuseScore, Python, and Music21.

### MuseScore on Ubuntu
 1. Install MuseScore via the command line:
   

    sudo add-apt-repository ppa:mscore-ubuntu/mscore3-stable
    sudo apt-get update
    sudo apt install musescore3

Note: If you use Ubuntu Software to install MuseScore, music21 will not find the MuseScore snap location. 

2. Activities, search MuseScore, click on MuseScore to complete setup.

### Python on Ubuntu:
 1. Firstly check python version required by Music21.
see https://web.mit.edu/music21/doc/installing/installLinux.html
in October 2021 this stated Music21 requires Python 3.7+.

 2. Check default installed version of python Ctrl+Alt+T
    

    python3 --version
    Python 3.8.10

The default python on Ubuntu 20.04 is compatible.


### Music21 on Ubuntu
 
1. If the package installer for Python (pip3) is not yet installed, in terminal :

       sudo apt install python3-pip


2. Install Music21


        pip3 install music21

3. or to upgrade music21 e.g. from 7.1.0 to 8.1.0

        pip3 uninstall music21
        pip3 install music21



4. Check music21 version installed with:

       pip3 list



#### Install MarkMelGen on Ubuntu
 Download release zip to desired directory for MarkMelGen and unzip.
#### Run MarkMelGen on Ubuntu

 In command prompt change to install directory and run MarkMelGen e.g.:

 ```  
 cd ~/pycharm
 chmod a+x run*
 ./run.sh
 # or to run without graphs      
 python3 MarkMelGen.py -g -c MarkMelGen.conf
```


MuseScore should open.  
 Press Space to start or stop playback..
 
When finished:
* if you are running with graphs, on the left sidebar (unity launcher) on the Image Viewer icon, right click, Quit 8 Windows.
* Close MuseScore.


#### Run MarkMelGen demonstration configuration files on Ubuntu

 In a Command Prompt window type run_conf to run the configuration files in the conf directory e.g.:

    ./run_conf.sh
    :: or to run one conf file:
    python3 MarkMelGen.py -c conf/Greensleeves.conf


Several runs of MarkMelGen will occur. Follow instructions to press Enter or close windows to continue.  A Logfile is written and music XML files created in the output directory.
Provided MuseScore is installed to the default location, output should be displayed in MuseScore.
 
When finished, close any graph and MuseScore windows.


#### Run MarkMelGen test files on Ubuntu

 In a Command Prompt window type run_conf_test to run the configuration files in the conf directory e.g.:


    :: to run one conf test file without graphs:
    python MarkMelGen.py -g -c conf/test/TONE_SCALE_ON_ANHEMITONIC.conf
    :: to run all the conf test files automatically 
    :: (without Pressing Enter or Closing Windows):
    ./run_conf_test.sh

To see the run_conf_test batch file results, Start File Explorer and go to the output folder in your MarkMelGen install directory.
Double-click on a musicxml file to open it in MuseScore. When finished, Close MuseScore.


---

## Configuration

Initial configuration file sections apply to the whole song.
Alternative examples are commented out.  The commented lines begin with a #.
The configuration file can be edited by adding a # 
to comment out an initial value, and then
remove the comment # on the desired alternative value.


Later sections apply to individual song sections i.e. [song_intro] to [song-outro] sections.
All values in these individual song sections can be commented out,
or individual entries can be uncommented.

e.g. MarkMelGen.conf

    # MarkMelGen.conf
    # Configuration file for MarkMelgen 1.0.0 python configparser
    
    # Configuration files may include comments, prefixed by specific characters (# by default)
    # A configuration file consists of sections, each led by a [section] header,
    # followed by key/value (or option/value) entries separated by a specific string (= by default).
    # By default, section names are case sensitive but keys are not.
    # Leading and trailing whitespace is removed from keys and values.
    # Values can be omitted if the parser is configured to allow it.
    # if a single option appears twice there will be a DuplicateOptionError.
    
    
    
    
    [paths]
    # The directories used. If blank use current working directory.
    
    INPUT_LYRICS_PATH =
    # INPUT_LYRICS_PATH = input/lyrics/
    
    # INPUT_MUSIC_PATH =
    # INPUT_MUSIC_PATH = input/music/
    # INPUT_MUSIC_PATH = input/music/bach/
    # INPUT_MUSIC_PATH = input/music/beethoven/
    # INPUT_MUSIC_PATH = input/music/chopin/
    # INPUT_MUSIC_PATH = input/music/essenFolksong/
    INPUT_MUSIC_PATH = input/music/mozart/
    # INPUT_MUSIC_PATH = input/music/rachmaninov/
    # INPUT_MUSIC_PATH = input/music/trecento/
    
    OUTPUT_PATH =
    # OUTPUT_PATH = output/
    
    
    
    
    [filenames]
    # The input filenames used.
    
    INPUT_LYRICS_FILENAME = Lyrics.txt
    # INPUT_LYRICS_FILENAME = lovePopHappy.txt
    
    # if INPUT_MUSIC_FILENAME is blank then MarkMelGen processes all the .mxl files in the INPUT_MUSIC_PATH directory.
    # INPUT_MUSIC_FILENAME = Music.mxl
    INPUT_MUSIC_FILENAME =
    
    
    
    
    [markmelgen]
    # The key options for the MarMelGen program.
    
    # CADENCE_ALTERNATE_PHRASE_END - if True a cadence is forced on every second line.
    CADENCE_ALTERNATE_PHRASE_END = False
    # CADENCE_ALTERNATE_PHRASE_END = True
    
    # CADENCE_DUR_MIN - the minimum duration of the cadence final note.
    CADENCE_DUR_MIN = 3.0
    
    # CADENCE_SECTION_END - if True a cadence is forced on every section end.
    CADENCE_SECTION_END = False
    # CADENCE_SECTION_END = True
    
    # CADENCE_TONE_FREQUENCY is a list of cadence tone name and frequency pairs, where the tone name is A to G, and the frequency count is 1 or more.
    # if not blank then it overrides the derived Cadence Markov Chain.
    # Note: A cadence may be considered as "weak" or "strong" depending on the impression of finality it gives.
    CADENCE_TONE_FREQUENCY =
    #
    # Examples of CADENCE_TONE_FREQUENCY for modes.
    # Mode A (Aeolian - minor) -----------------------------------------------------------------------------------------
    # A5 (making a chord from the cadence notes)
    # CADENCE_TONE_FREQUENCY = [['A', 9], ['E', 6]]
    # Am
    # CADENCE_TONE_FREQUENCY = [['A', 4], ['C', 5], ['E', 11]]
    # A7
    # CADENCE_TONE_FREQUENCY = [['A', 6], ['E', 3], ['G', 2]]
    # Am7s4
    # CADENCE_TONE_FREQUENCY = [['A', 3], ['C', 2], ['D', 2], ['E', 2], ['G', 4]]
    # Am and Em
    # CADENCE_TONE_FREQUENCY = [['A', 6], ['B', 1], ['C', 1], ['E', 4], ['G', 2]]
    # Am and Em7
    # CADENCE_TONE_FREQUENCY = [['A', 3], ['B', 7], ['C', 4], ['E', 2], ['G', 1]]
    # Mode B (Locrian - discordant tri-tone) --------------------------------------------------------------------------
    # CADENCE_TONE_FREQUENCY = [['B', 6], ['F', 3]]
    # Mode C (Ionian - major) -----------------------------------------------------------------------------------------
    # C9
    # CADENCE_TONE_FREQUENCY = [['C', 1], ['D', 2], ['E', 5], ['G', 2]]
    # C9
    # CADENCE_TONE_FREQUENCY = [['C', 2], ['D', 1], ['F', 2], ['G', 2]]
    # C
    # CADENCE_TONE_FREQUENCY = [['A', 1], ['C', 5], ['D', 1],  ['E', 2], ['F', 1], ['G', 3]]
    # C
    # CADENCE_TONE_FREQUENCY = [['B', 1], ['C', 6], ['D', 2],  ['E', 1], ['F', 2], ['G', 3]]
    # Mode D (Dorian - serious,	any feeling	happy, taming the passions) -----------------------------------------------
    # D9
    # CADENCE_TONE_FREQUENCY = [['A', 3], ['D', 10], ['E', 8], ['G', 1]]
    # D
    # CADENCE_TONE_FREQUENCY = [['A', 3], ['C', 1], ['D', 4], ['G', 1]]
    # Dm & Am
    # CADENCE_TONE_FREQUENCY = [['A', 7], ['C', 7], ['D', 3], ['E', 9], ['F', 2]]
    # Mode E (Phrygian - mystic, vehement, inciting anger) ------------------------------------------------------------
    # Em
    # CADENCE_TONE_FREQUENCY = [['E', 8], ['G', 4]]
    # Em7
    # CADENCE_TONE_FREQUENCY = [['B', 3], ['D', 1], ['E', 4], ['G', 1]]
    # Mode F (Lydian - happy, happy, happy) ---------------------------------------------------------------------------
    # CADENCE_TONE_FREQUENCY = [['A', 1], ['C', 1], ['F', 4], ['G', 1]]
    # Mode G (Mixolydian - angelical, of youth, uniting pleasure and sadness) -----------------------------------------
    # CADENCE_TONE_FREQUENCY = [['A', 1], ['D', 3], ['E', 1], ['G', 4]]
    #
    # Test example with all pitch frequency=1
    # CADENCE_TONE_FREQUENCY = [['C-', 1], ['C', 1], ['C#', 1], ['D-', 1], ['D', 1], ['D#', 1], ['E-', 1], ['E', 1], ['E#', 1], ['F-', 1], ['F', 1], ['F#', 1], ['G-', 1], ['G', 1], ['G#', 1], ['A-', 1], ['A', 1], ['A#', 1], ['B-', 1], ['B', 1], ['B#', 1]]
    
    # Display graphs of pitch, pitch class, durations and a piano roll.
    DISPLAY_GRAPHS = True
    # DISPLAY_GRAPHS = False
    
    # Display the score in another application (MuseScore).
    DISPLAY_SCORE = True
    # DISPLAY_SCORE = False
    
    # DURATION_EQ is is a list of duration name and frequency factor pairs, and the frequency multiplier factor is a positive real number > 0.0.
    # if not blank then it allows the Markov selection of each duration to be increased when the frequency multiplier factor is > 1.0 or decreased when > 0.0 and < 1.0.
    # Only durations present in the input music can be adjusted.
    DURATION_EQ =
    #
    # Examples of DURATION_EQ to bias desired durations without losing others completely
    # to increase half notes, and reduce whole notes:
    #DURATION_EQ = [['0.5', 100.0], ['1.0', 0.5]]
    # to increase quarter-note triplets, and reduce whole notes:
    #DURATION_EQ = [['Fraction(1, 3)', 130.0], ['1.0', 0.5]]
    
    # DURATION_SET - a set of musical durations, ordered by length, starting on shortest duration.
    # A duration can only be picked if it appears in the INPUT_MUSIC (see the Input histogram Quarter Length graph).
    # Note: if you want a tuplet (e.g. '1.3') in your DURATION_SET ensure:
    #       DUR_RATIONAL is False globally or in desired song section;
    #       Tuplet is within DUR_LEAST - DUR_LONGEST.
    # DURATION_SET = []
    DURATION_SET = ['0.25', '0.5', '1.0', '1.5']
    # DURATION_SET = ['1/6', '1/3', '2/3', '1.0']
    
    # DUR_LEAST - The minimum duration. 0 = not checked.
    # Use a fraction if the duration is inexpressible exactly as a float.  A fraction is defined with slash e.g. 2/3
    DUR_LEAST = 0
    # DUR_LEAST = 1
    # DUR_LEAST = 0.25
    # DUR_LEAST = 1/6
    
    # DUR_LONGEST - The maximum duration. 0 = not checked.
    DUR_LONGEST = 0
    # DUR_LONGEST = 2.0
    # DUR_LONGEST = 2/3
    
    # DUR_PREV_DIFF - compare duration with previous duration.
    # e.g. where 2, duration is valid when >= 1/2 previous and <= 2 x previous etc ,
    # where 0 or <= 1, do not compare with previous duration.
    DUR_PREV_DIFF = 0
    # DUR_PREV_DIFF = 2.0
    
    # DUR_RATIONAL if True any simple rational (beat divides into 2) duration is valid. This can avoid output corruption.
    DUR_RATIONAL = True
    # DUR_RATIONAL = False
    
    # DUR_TUPLET if True any complex (e.g. beat divides into 3) duration is valid.
    DUR_TUPLET = False
    # DUR_TUPLET = True
    
    # INSTRUMENT
    # Full list of instruments at https://raw.githubusercontent.com/cuthbertLab/music21/master/music21/instrument.py
    # right click Save as... and search for instrumentName e.g.
    # find "self.instrumentName =" instrument.py
    # find "self.instrumentName =" instrument.py | find "Piano"
    INSTRUMENT = Piano
    # INSTRUMENT = Accordion
    # INSTRUMENT = Acoustic Bass
    # INSTRUMENT = Acoustic Guitar
    # INSTRUMENT = Alto
    # INSTRUMENT = Alto Saxophone
    # INSTRUMENT = Banjo
    # INSTRUMENT = Baritone
    # INSTRUMENT = Baritone Saxophone
    # # voice.bass
    # INSTRUMENT = Bass
    # INSTRUMENT = Bassoon
    # INSTRUMENT = Bass Trombone
    # INSTRUMENT = Brass
    # INSTRUMENT = Celesta
    # INSTRUMENT = Clarinet
    # INSTRUMENT = Clavichord
    # INSTRUMENT = Contrabass
    # INSTRUMENT = Contrabassoon
    # INSTRUMENT = Dulcimer
    # INSTRUMENT = Electric Bass
    # INSTRUMENT = Electric Guitar
    # INSTRUMENT = Electric Piano
    # INSTRUMENT = English Horn
    # INSTRUMENT = Flute
    # INSTRUMENT = Glockenspiel
    # INSTRUMENT = Guitar
    # INSTRUMENT = Harmonica
    # INSTRUMENT = Harp
    # INSTRUMENT = Kalimba
    # INSTRUMENT = Koto
    # INSTRUMENT = Lute
    # INSTRUMENT = Marimba
    # INSTRUMENT = Oboe
    # INSTRUMENT = Ocarina
    # INSTRUMENT = Pan Flute
    # INSTRUMENT = Piccolo
    # INSTRUMENT = Recorder
    # INSTRUMENT = Reed Organ
    # INSTRUMENT = Saxophone
    # INSTRUMENT = Shamisen
    # INSTRUMENT = Sitar
    # INSTRUMENT = Soprano
    # INSTRUMENT = Soprano Saxophone
    # INSTRUMENT = Tenor
    # INSTRUMENT = Tenor Saxophone
    # INSTRUMENT = Timpani
    # INSTRUMENT = Trombone
    # INSTRUMENT = Trumpet
    # INSTRUMENT = Tuba
    # INSTRUMENT = Tubular Bells
    # INSTRUMENT = Ukulele
    # INSTRUMENT = Vibraphone
    # INSTRUMENT = Violin
    # INSTRUMENT = Violoncello
    # INSTRUMENT = Voice
    # INSTRUMENT = Xylophone
    # # ----------------------------  percussion - unpitched (not melodic, but fun!)
    # # On MuseScore 3.6.2 you can change instruments by right clicking a staff,
    # # choose staff/part properties, click "Change instruments", select the new instrument and click OK.
    # INSTRUMENT = Castanets
    # INSTRUMENT = Maracas
    
    # MAX_PHRASE_REST - when analysing rests, ignore rests longer than MAX_PHRASE_REST e.g. ignore initial rests, instrumental solo rests, end of song rests
    # MAX_PHRASE_REST = 4.0
    MAX_PHRASE_REST = 8.0
    
    # REST_NOTE_LINE_OFFSET  if not blank then force given offset for each line. = 0.0 is first beat, 3.0 means start lyric on fourth beat.
    REST_NOTE_LINE_OFFSET =
    # REST_NOTE_LINE_OFFSET = 0.0
    
    
    # TEMPO_BPM when 0.0, tempo is taken from INPUT_MUSIC. If INPUT_MUSIC has no tempo, default to 120.0 otherwise use given tempo in quarter note beats per minute
    TEMPO_BPM = 0.0
    # TEMPO_BPM = 80.0
    # TEMPO_BPM = 90.0
    # TEMPO_BPM = 100.0
    # TEMPO_BPM = 110.0
    # TEMPO_BPM = 120.0
    # TEMPO_BPM = 130.0
    # TEMPO_BPM = 140.0
    
    
    # TIME_SIG_WANTED if not blank then force given time signature e.g. 4/4
    TIME_SIG_WANTED =
    # TIME_SIG_WANTED = '3/4'
    
    # Tone filters
    
    # TONE_ASCENT True triggers a sequence of notes rising in pitch when TONE_RANGE_BOTTOM is reached until the middle of the tone range is achieved.
    TONE_ASCENT = False
    # TONE_ASCENT = True
    
    # TONE_ASCENT_MIN_INTERVAL - (>=2) after TONE_ASCENT_TRIGGERED, sets minimum semitone interval from previous tone
    # 2 gives runs up scale, 3 gives ascent leaps, 4 gives ascent chord arpeggio
    # TONE_ASCENT_MIN_INTERVAL = 2
    TONE_ASCENT_MIN_INTERVAL = 5
    
    # TONE_ASCENT_TRIGGER_EVERY_N_TIMES - only trigger the ascent every Nth time the trigger tone occurs
    TONE_ASCENT_TRIGGER_EVERY_N_TIMES = 1
    # TONE_ASCENT_TRIGGER_EVERY_N_TIMES = 2
    
    # TONE_DESCENT True triggers a cascade down when TONE_RANGE_TOP is reached until the middle of the tone range is achieved.
    TONE_DESCENT = False
    # TONE_DESCENT = True
    
    # TONE_DESCENT_MAX_INTERVAL - (>=2) after TONE_DESCENT_TRIGGERED, sets maximum semitone interval from previous tone
    # 2 gives runs down scale, 3 gives descent leaps, 4 gives descent chord arpeggio
    TONE_DESCENT_MAX_INTERVAL = 2
    # TONE_DESCENT_MAX_INTERVAL = 5
    
    # TONE_DESCENT_TRIGGER_EVERY_N_TIMES - only trigger the descent every Nth time the trigger tone occurs
    TONE_DESCENT_TRIGGER_EVERY_N_TIMES = 1
    # TONE_DESCENT_TRIGGER_EVERY_N_TIMES = 4
    
    # TONE_EQ is is a list of tone name and frequency factor pairs, where the tone name is A to G, and the frequency multiplier factor is a positive real number > 0.0.
    # # if not blank then it allows the Markov selection of each pitch to be increased when > 1.0 or decreased when > 0.0 and < 1.0.
    TONE_EQ =
    #
    # Examples of TONE_EQ to simulate modes.
    # Note: here a "Mode" is a type of musical scale defined by their starting primary pitch (a final) or tonic.
    # The modal final note functions as a relational center. The dominant tone of a mode is a fifth above the final.
    # Mode A (Aeolian - minor) -----------------------------------------------------------------------------------------
    #TONE_EQ = [['A', 4.0], ['E', 3.0]]
    # Mode B (Locrian - discordant tri-tone) --------------------------------------------------------------------------
    # TONE_EQ = [['B', 4.0], ['F', 3.0]]
    # Mode C (Ionian - major) -----------------------------------------------------------------------------------------
    # TONE_EQ = [['C', 4.0], ['G', 3.0]]
    # Mode D (Dorian - serious,	any feeling	happy, taming the passions) -----------------------------------------------
    # TONE_EQ = [['D', 4.0], ['A', 3.0]]
    # Mode E (Phrygian - mystic, vehement, inciting anger) ------------------------------------------------------------
    # TONE_EQ = [['E', 4.0], ['B', 3.0]]
    # Mode F (Lydian - happy, happy, happy) ---------------------------------------------------------------------------
    # TONE_EQ = [['F', 4.0], ['C', 3.0]]
    # Mode G (Mixolydian - angelical, of youth, uniting pleasure and sadness) -----------------------------------------
    # TONE_EQ = [['G', 4.0], ['D', 3.0]]
    #
    # Test example which boosts A, C and E, with other scale tones flat, and reduces accidentals:
    # TONE_EQ = [['C-', 0.1], ['C', 4.0], ['C#', 0.1], ['D-', 0.1], ['D', 1.0], ['D#', 0.1], ['E-', 0.1], ['E', 4.0], ['E#', 0.1], ['F-', 0.1], ['F', 1.0], ['F#', 0.1], ['G-', 0.1], ['G', 1.0], ['G#', 0.1], ['A-', 0.1], ['A', 4.0], ['A#', 0.1], ['B-', 0.1], ['B', 1.0], ['B#', 0.1]]
    
    # TONE_INTERVAL = smallest | largest | random.
    # The default is smallest interval between tones e.g. choose smallest C4 to B3, not largest C4 to B4
    TONE_INTERVAL = smallest
    # TONE_INTERVAL = largest
    # TONE_INTERVAL = random
    
    # TONES_ON_KEY - if tone is in scale then tone is valid
    # TONES_ON_KEY = False
    TONES_ON_KEY = True
    
    # TONES_OFF_KEY - if tone is not in scale then tone is valid (currently NA to first/last tone)
    TONES_OFF_KEY = False
    # TONES_OFF_KEY = True
    
    # TONE_PREV_INTERVAL - maximum number of semitones between notes.
    # 0 = Off, do not compare with previous tone
    # 1 caused hang together with TONE_SCALE_SET
    # 2-3 very limited melodic movement
    # 4 limited melodic movement
    # 5 - 6 lightly limited melodic movement
    # 7 normal melodic movement
    # 8 - 9 slightly jumpy melodic movement
    # >= 10  jumpy melodic movement, use with TONE_INTERVAL = largest
    TONE_PREV_INTERVAL = 0
    # TONE_PREV_INTERVAL = 4
    
    # TONE_RANGE_BOTTOM / TONE_RANGE_TOP - change to suit the desired vocal range.
    # Note: consider "tessitura" - the best notes in your range.
    # Note: The octave number changes at C, e.g. A3, B3, C4, D4, E4 etc. C4 is middle C.
    # Female
    # Soprano:	C4 to C6
    # TONE_RANGE_BOTTOM = C4
    # TONE_RANGE_TOP = C6
    # Mezzo-soprano: A3 to A5
    # TONE_RANGE_BOTTOM = A3
    # TONE_RANGE_TOP = A5
    # Contralto F3 to F5
    # TONE_RANGE_BOTTOM = F3
    # TONE_RANGE_TOP = F5
    # Male:
    # Tenor: B2 to B4
    # TONE_RANGE_BOTTOM = B2
    # TONE_RANGE_TOP = B4
    # Baritone: G2 to G4
    # TONE_RANGE_BOTTOM = G2
    # TONE_RANGE_TOP = G4
    # Bass: E2 to E4
    # TONE_RANGE_BOTTOM = E2
    # TONE_RANGE_TOP = E4
    # One octave range
    # TONE_RANGE_BOTTOM = C4
    # TONE_RANGE_TOP = B4
    # My Modal range (from free Piano tuner app)
    # TONE_RANGE_BOTTOM = C2
    # TONE_RANGE_TOP = C4
    # My Falsetto range - Falsetto (adult male head voice) is Italian for false soprano
    # TONE_RANGE_BOTTOM = C4
    # TONE_RANGE_TOP = C5
    # My Modal and Falsetto range
    # TONE_RANGE_BOTTOM = C2
    # TONE_RANGE_TOP = C5
    # Male-Female joint range
    # TONE_RANGE_BOTTOM = C2
    # TONE_RANGE_TOP = C6
    # Greensleeves range:
    # TONE_RANGE_BOTTOM = E4
    # TONE_RANGE_TOP = G5
    TONE_RANGE_BOTTOM = C3
    TONE_RANGE_TOP = C5
    
    # TONE_SCALE_SET - a set of musical notes, ordered by fundamental frequency, starting on the note upon which the scale is built.
    # A pitch can only be picked if it appears in the INPUT_MUSIC (see the Input histogram Pitch Class graph).
    # TONE_SCALE_SET empty list (when not required):
    TONE_SCALE_SET = []
    # TONE_SCALE_SET with all tones (no tone filtering on input music). Note: filtering is enharmonic so no need to put C# and D- etc in filter:
    # TONE_SCALE_SET = ['C-', 'C', 'C#', 'D-', 'D', 'D#', 'E-', 'E', 'E#', 'F-', 'F', 'F#', 'G-', 'G', 'G#', 'A-', 'A', 'A#', 'B-', 'B', 'B#']
    # Six note Blues Scale built on A,      Degrees(relative to the A minor scale): 1 3 4 4# 5 7            Intervals: 3H-W-H-H-3H-W        Pitch classes: 6
    # TONE_SCALE_SET = ['A', 'C', 'D', 'D#', 'E', 'G']
    # Nine note Blues Scale built on C,     Degrees(relative to the C major scale): 1 2 3- 3 4 5 6 7- 7     Intervals: W-H-H-H-H-W-W-H-H    Pitch classes: 9
    # TONE_SCALE_SET = ['C', 'D', 'E-', 'E', 'F', 'G', 'A', 'B-', 'B']
    
    # TONE_SCALE_ON_ANHEMITONIC - if True, valid scale tones are [1, 2, 4, 5, 6]
    TONE_SCALE_ON_ANHEMITONIC = False
    # TONE_SCALE_ON_ANHEMITONIC = True
    
    # TONE_SCALE_ON_HEMITONIC - if True, valid scale tones are [1, 3, 4, 5, 7]
    TONE_SCALE_ON_HEMITONIC = False
    # TONE_SCALE_ON_HEMITONIC = True
    
    
    
    
    
    
    # Song sections with optional key values.
    # uncomment (remove #) and change values if you want to change the options for a song section.
    # The song structure is determined by the section headers in the lyrics file.
    #
    # Example song structures:
    # AAA       verse-verse-verse
    # ABA       verse-chorus-verse or chorus-verse-chorus
    # AABA      verse-verse-chorus-verse
    # ABAB      verse-chorus-verse-chorus
    #
    # ABA form may be combined with AABA form, in compound AABA forms.
    # That means that every A section or B section can consist of more than one section (for example Verse-Chorus).
    # In that way the modern popular song structure can be viewed as a AABA form, where the B is the bridge.
    # AABA      {verse-chorus}{verse-chorus}-bridge-{verse-chorus}
    # or
    # ABABCB    verse-chorus-verse-chorus-bridge-chorus
    #
    # Other sections can be added e.g. intro, outro
    # ABBCBD    intro-{verse-chorus}{verse-chorus}-bridge-{verse-chorus}-outro
    
    
    
    [song_intro]
    # The introduction establishes melodic, harmonic or rhythmic material related to the main body of a piece.
    # The intro is usually only used once at the beginning of the piece.
    # Generally speaking, an introduction contains just music and no words.
    
    # intro key value example 1
    DURATION_SET = ['0.25', '0.5', '0.75', '1.0', '2.0', '3.0', '4.0']
    DUR_LEAST = 0.25
    DUR_LONGEST = 4.0
    DUR_PREV_DIFF = 12.0
    DUR_RATIONAL = True
    DUR_TUPLET = False
    REST_NOTE_LINE_OFFSET = 0.0
    TONES_ON_KEY = True
    TONE_PREV_INTERVAL = 3
    TONE_RANGE_BOTTOM = C5
    TONE_RANGE_TOP = F5
    TONE_SCALE_SET = ['C', 'D', 'E', 'F']
    
    
    [song_verse]
    # A verse is a repeated section of a song that typically features a new set of lyrics on each repetition.
    # The verse is usually played before the chorus.  It may be 64 or 32 beats long.
    
    # verse key value example 1
    # DURATION_SET = ['0.25', '0.5', '0.75', '1.0', '1.5', '2.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 2.0
    # DUR_PREV_DIFF = 8.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 0.0
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 5
    # TONE_RANGE_BOTTOM = G3
    # TONE_RANGE_TOP = A4
    # TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'G']
    
    # verse key value example 2
    # DURATION_SET = ['0.25', '0.5', '1.0', '2.0', '3.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 3.0
    # DUR_PREV_DIFF = 8.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 3.0
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 7
    # TONE_RANGE_BOTTOM = B4
    # TONE_RANGE_TOP = D6
    # TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    
    # verse key value example 3
    # DURATION_SET = ['0.125', '0.25', '0.5', '0.75', '1.0', '1.5', '1/3', '2.0', '2/3', '3.0']
    # DUR_LEAST = 0.125
    # DUR_LONGEST = 3.0
    # DUR_PREV_DIFF = 12.0
    # DUR_RATIONAL = False
    # DUR_TUPLET = True
    # REST_NOTE_LINE_OFFSET = 0.0
    # TONES_ON_KEY = False
    # TONE_PREV_INTERVAL = 5
    # TONE_RANGE_BOTTOM = A4
    # TONE_RANGE_TOP = C6
    # TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'F', 'F#', 'G', 'G#']
    
    # verse key value example 4
    # DURATION_SET = ['0.25', '0.5', '1.5', '2.0', '3.0', '4.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 4.0
    # DUR_PREV_DIFF = 16.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 1.0
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 2
    # TONE_RANGE_BOTTOM = B3
    # TONE_RANGE_TOP = D4
    # TONE_SCALE_SET = ['B', 'C', 'D']
    
    # verse key value example 5
    # DURATION_SET = ['0.25', '0.5', '1.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 1.0
    # DUR_PREV_DIFF = 4.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 1.0
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 12
    # TONE_RANGE_BOTTOM = G3
    # TONE_RANGE_TOP = B4
    # TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    
    # verse key value example 6
    DURATION_SET = ['0.5', '0.75', '1.5', '3.0']
    DUR_LEAST = 0.5
    DUR_LONGEST = 3.0
    DUR_PREV_DIFF = 6.0
    DUR_RATIONAL = True
    DUR_TUPLET = False
    REST_NOTE_LINE_OFFSET = 3.0
    TONES_ON_KEY = True
    TONE_PREV_INTERVAL = 3
    TONE_RANGE_BOTTOM = G4
    TONE_RANGE_TOP = C5
    TONE_SCALE_SET = ['A', 'C', 'G']
    
    # verse key value example 7
    # DURATION_SET = ['0.25', '0.5', '0.75', '1.0', '1.5', '1/3', '1/6', '2.0', '2/3', '4.0']
    # DUR_LEAST = 1/6
    # DUR_LONGEST = 4.0
    # DUR_PREV_DIFF = 16.0
    # # DUR_RATIONAL = False
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # # DUR_TUPLET = True
    # REST_NOTE_LINE_OFFSET = 3.75
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 9
    # TONE_RANGE_BOTTOM = G4
    # TONE_RANGE_TOP = G5
    # TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'G']
    
    [song_prechorus]
    # The prechorus connects the verse and chorus.
    # Also known as a "build", "channel", or "transitional bridge",
    # The prechorus typically uses the subdominant (usually built on the IV chord or ii chord),
    # which in the key of C Major would be an F Major or D minor chord.
    
    # prechorus key value example 1
    # DURATION_SET = ['0.25', '0.5', '0.75', '1.0', '1.5', '2.0', '4.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 4.0
    # DUR_PREV_DIFF = 5.333333333333333
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 2.0
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 5
    # TONE_RANGE_BOTTOM = G4
    # TONE_RANGE_TOP = E5
    # TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'G']
    
    # prechorus key value example 4
    # DURATION_SET = ['0.25', '0.5', '0.75', '1.0', '1.5', '2.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 2.0
    # DUR_PREV_DIFF = 8.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 0.0
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 5
    # TONE_RANGE_BOTTOM = G4
    # TONE_RANGE_TOP = F5
    # TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    
    # prechorus key value example 5
    # DURATION_SET = ['0.25', '0.5']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 0.5
    # DUR_PREV_DIFF = 2.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 2.5
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 4
    # TONE_RANGE_BOTTOM = C4
    # TONE_RANGE_TOP = F4
    # TONE_SCALE_SET = ['C', 'D', 'E', 'F']
    
    # prechorus key value example 6
    DURATION_SET = ['0.125', '0.25', '0.375', '0.5', '0.75', '1.0', '1/3', '1/6', '2.0']
    DUR_LEAST = 0.125
    DUR_LONGEST = 2.0
    DUR_PREV_DIFF = 16.0
    # DUR_RATIONAL = False
    DUR_RATIONAL = True
    DUR_TUPLET = False
    # DUR_TUPLET = True
    REST_NOTE_LINE_OFFSET = 3.0
    TONES_ON_KEY = True
    TONE_PREV_INTERVAL = 5
    TONE_RANGE_BOTTOM = G4
    TONE_RANGE_TOP = A5
    TONE_SCALE_SET = ['A', 'C', 'D', 'E', 'G']
    
    # prechorus key value example 7
    # DURATION_SET = ['0.25', '0.5', '0.75', '1.0', '1.5', '2.0', '3.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 3.0
    # DUR_PREV_DIFF = 12.0
    # # DUR_RATIONAL = True
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 0.0
    # TONES_ON_KEY = False
    # TONE_PREV_INTERVAL = 4
    # TONE_RANGE_BOTTOM = B-4
    # TONE_RANGE_TOP = G5
    # TONE_SCALE_SET = ['B-', 'C', 'D', 'E-', 'F', 'G']
    
    [song_chorus]
    # The chorus usually retains the same set of lyrics every time its music appears.
    # The chorus is the part that contains the hook or the "main idea" of a song's lyrics and music,
    # A refrain is a repetitive phrase or phrases that serve the function of a chorus lyrically,
    # but are not in a separate section or long enough to be a chorus.
    
    # chorus key value example 1
    # DURATION_SET = ['0.25', '0.5', '0.75', '1.0', '1.5', '2.0', '4.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 4.0
    # DUR_PREV_DIFF = 6.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 0.0
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 7
    # TONE_RANGE_BOTTOM = A4
    # TONE_RANGE_TOP = E5
    # TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E']
    
    # chorus key value example 2
    # DURATION_SET = ['0.125', '0.25', '0.5', '0.75', '1.0', '2.0']
    # DUR_LEAST = 0.125
    # DUR_LONGEST = 2.0
    # DUR_PREV_DIFF = 8.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 0.75
    # TONES_ON_KEY = False
    # TONE_PREV_INTERVAL = 12
    # TONE_RANGE_BOTTOM = C5
    # TONE_RANGE_TOP = D6
    # TONE_SCALE_SET = ['A', 'B', 'B-', 'C', 'D', 'E', 'F', 'G']
    
    # chorus key value example 3
    # DURATION_SET = ['0.5', '1.0', '1.5', '1/3', '2.0', '2/3', '4.0', '4/3']
    # DUR_LEAST = 1/3
    # DUR_LONGEST = 4.0
    # DUR_PREV_DIFF = 6.0
    # DUR_RATIONAL = False
    # DUR_TUPLET = True
    # REST_NOTE_LINE_OFFSET = 0.0
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 5
    # TONE_RANGE_BOTTOM = E5
    # TONE_RANGE_TOP = C6
    # TONE_SCALE_SET = ['A', 'B', 'C', 'E', 'F', 'G']
    
    # chorus key value example 4
    # DURATION_SET = ['0.25', '0.5', '0.75', '1.0', '2.0', '3.0', '4.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 4.0
    # DUR_PREV_DIFF = 16.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 3.5
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 9
    # TONE_RANGE_BOTTOM = G4
    # TONE_RANGE_TOP = E5
    # TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'G']
    
    # chorus key value example 5
    # DURATION_SET = ['0.25', '0.5', '1.5']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 1.5
    # DUR_PREV_DIFF = 3.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 1.5
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 10
    # TONE_RANGE_BOTTOM = D4
    # TONE_RANGE_TOP = C5
    # TONE_SCALE_SET = ['A', 'C', 'D', 'F', 'G']
    
    # chorus key value example 6
    DURATION_SET = ['0.0625', '0.125', '0.25', '0.375', '0.5', '0.75', '1.0', '1/3', '1/5', '1/6', '2.0', '2/3', '2/5', '4.0', '6/5']
    DUR_LEAST = 0.0625
    DUR_LONGEST = 4.0
    DUR_PREV_DIFF = 10.666666666666666
    # DUR_RATIONAL = False
    DUR_RATIONAL = True
    DUR_TUPLET = False
    # DUR_TUPLET = True
    REST_NOTE_LINE_OFFSET = 0.5
    TONES_ON_KEY = True
    TONE_PREV_INTERVAL = 12
    TONE_RANGE_BOTTOM = A4
    TONE_RANGE_TOP = A5
    TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    
    # chorus key value example 7
    # DURATION_SET = ['0.25', '0.5', '1.0', '1/24', '1/6', '3.0']
    # DUR_LEAST = 1/24
    # DUR_LONGEST = 3.0
    # DUR_PREV_DIFF = 12.0
    # # DUR_RATIONAL = False
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # # DUR_TUPLET = True
    # REST_NOTE_LINE_OFFSET = 0.0
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 12
    # TONE_RANGE_BOTTOM = A4
    # TONE_RANGE_TOP = C6
    # TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'F']
    
    [song_solo]
    # A solo or instrumental break is often found after the middle chorus part.
    # In pop music, there may be a guitar solo, or a solo may be performed by a synthesizer player or sax player.
    # A solo is a section designed to showcase an instrumentalist.
    
    # solo key value example 1
    # DURATION_SET = ['0.25', '0.5', '0.75', '2.0', '4.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 4.0
    # DUR_PREV_DIFF = 4.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 3.0
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 2
    # TONE_RANGE_BOTTOM = B4
    # TONE_RANGE_TOP = D5
    # TONE_SCALE_SET = ['B', 'C', 'D']
    
    # solo key value example 2
    DURATION_SET = ['0.25', '0.5', '1.0', '2.0']
    DUR_LEAST = 0.25
    DUR_LONGEST = 2.0
    DUR_PREV_DIFF = 8.0
    DUR_RATIONAL = True
    DUR_TUPLET = False
    REST_NOTE_LINE_OFFSET = 3.0
    TONES_ON_KEY = False
    TONE_PREV_INTERVAL = 7
    TONE_RANGE_BOTTOM = B4
    TONE_RANGE_TOP = C7
    TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'E-', 'F', 'F#', 'G']
    
    [song_bridge]
    # A bridge section usually appears after the second chorus.
    # A bridge is also known as a "middle eight". The bridge is usually only used once.
    # It contrasts with the verse usually ends on the dominant.
    # The bridge breaks up the repetitive pattern of the song and keep the listener's attention.
    # In a bridge, the pattern of the words and music change."
    
    # bridge key value example 1
    # DURATION_SET = ['0.25', '0.5', '0.75', '2.0', '4.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 4.0
    # DUR_PREV_DIFF = 4.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 3.0
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 2
    # TONE_RANGE_BOTTOM = B4
    # TONE_RANGE_TOP = D5
    # TONE_SCALE_SET = ['B', 'C', 'D']
    
    # bridge key value example 2
    # DURATION_SET = ['0.25', '0.5', '1.0', '2.0', '3.0', '4.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 4.0
    # DUR_PREV_DIFF = 12.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 0.0
    # TONES_ON_KEY = False
    # TONE_PREV_INTERVAL = 7
    # TONE_RANGE_BOTTOM = C5
    # TONE_RANGE_TOP = D6
    # TONE_SCALE_SET = ['A', 'B-', 'C', 'D', 'E', 'G']
    
    # bridge key value example 3
    # DURATION_SET = ['0.25', '0.5', '1.0', '2.0', '4.0']
    # DUR_LEAST = 0.25
    # DUR_LONGEST = 4.0
    # DUR_PREV_DIFF = 4.0
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # REST_NOTE_LINE_OFFSET = 0.0
    # TONES_ON_KEY = True
    # TONE_PREV_INTERVAL = 5
    # TONE_RANGE_BOTTOM = A4
    # TONE_RANGE_TOP = E5
    # TONE_SCALE_SET = ['A', 'C', 'D', 'E']
    
    # bridge key value example 5
    # DURATION_SET = ['0.25', '0.5', '1.0']
    DUR_LEAST = 0.25
    DUR_LONGEST = 1.0
    DUR_PREV_DIFF = 4.0
    DUR_RATIONAL = True
    DUR_TUPLET = False
    REST_NOTE_LINE_OFFSET = 3.0
    TONES_ON_KEY = False
    TONE_PREV_INTERVAL = 11
    TONE_RANGE_BOTTOM = D4
    TONE_RANGE_TOP = C#5
    TONE_SCALE_SET = ['A', 'C#', 'D', 'F', 'G']
    
    # bridge key value example 7
    # DURATION_SET = ['0.25', '0.5', '0.75', '1.0', '1.5', '1/24', '1/3', '1/5', '1/6', '2.0', '2/3', '2/5', '3.0', '4/5']
    # DUR_LEAST = 1/24
    # DUR_LONGEST = 3.0
    # DUR_PREV_DIFF = 12.0
    # # DUR_RATIONAL = False
    # DUR_RATIONAL = True
    # DUR_TUPLET = False
    # # DUR_TUPLET = True
    # REST_NOTE_LINE_OFFSET = 3.25
    # TONES_ON_KEY = False
    # TONE_PREV_INTERVAL = 12
    # TONE_RANGE_BOTTOM = G4
    # TONE_RANGE_TOP = C6
    # TONE_SCALE_SET = ['A', 'B', 'B-', 'C', 'D', 'E', 'E-', 'F', 'G']
    
    [song_outro]
    # The outro (also called a "coda") is usually only used once at the end.
    # The outro or conclusion is a way of finishing or completing the song.
    # It signals to the listeners that the song is nearing its close.
    # if a song just ended at the last bar of a section, such as on the last verse or the last chorus,
    # this might feel too abrupt for listeners.

    # outro key value example 1
    DURATION_SET = ['0.25', '0.5', '0.75', '1.0', '2.0', '3.0', '4.0']
    DUR_LEAST = 0.25
    DUR_LONGEST = 4.0
    DUR_PREV_DIFF = 12.0
    DUR_RATIONAL = True
    DUR_TUPLET = False
    REST_NOTE_LINE_OFFSET = 0.0
    TONES_ON_KEY = True
    TONE_PREV_INTERVAL = 3
    TONE_RANGE_BOTTOM = C5
    TONE_RANGE_TOP = F5
    TONE_SCALE_SET = ['C', 'D', 'E', 'F']




    

If the INPUT_MUSIC_FILENAME is blank then MarkMelGen processes 
all the music XML (.mxl) files in the INPUT_MUSIC_PATH directory.

Edit MarkMelGen.conf configuration as desired,
later sections are commented out with # at the beginning of the line.


* Use different configuration files to get different output e.g.

      MarkMelGen.py -c conf/test/TIME_SIG_WANTED-12-8.conf

## InputLyrics

### Create an INPUT_LYRICS_FILENAME
 If you have some lyrics then manually add desired section names:
 intro, verse, prechorus, chorus, solo, bridge, or outro.
 otherwise you can use a website such as https://theselyricsdonotexist.com/

 Given lyrics with section headers, you can use a website to split the lyrics into syllables,
 such as 
 * https://www.hyphenation24.com/ (can paste whole song into field) or
 * https://melobytes.com/en/app/syllabication
 * or for a python module for syllabifying English see https://github.com/kylebgorman/syllabify or https://github.com/gerazov/syllabify

 Then remove hyphens added to section names to get syllabifyied lyrics:
e.g. 

    Verse 1
    So I'm still in love with you
    Yet is in love with you e-nough
    Yet in love with you I am too
    Yet I love you true-ly


### INPUT_LYRICS_FILENAME functions
Comments beginning with # can be added to each lyric filename line.
A Comment can contain a function to apply to the melody.  The functions can only be used on the first occurrence of each section.
Section references can only be backwards to previous lines.  It is better to refer to a line that has the same number of syllables
as the comment line.


e.g. 
* copy( Section, Line)  
  * where Section is  ['intro', 'verse', 'prechorus', 'chorus', 'solo', 'bridge', 'outro'] 
* transpose( Section, Line, GenericInterval )
  * where GenericInterval range is -32 to 32, Note: 0 illegal
* invert( Section, Line, Invert_Pitch)
  * where the Line is inverted diatonically around the Invert_Pitch e.g. C4 
* reverse( Section, Line)

Note: Generally an invert is more recognisable than a reverse, and a reverse is more recognisable than a reverse invert.


    INTRO
    1 2 3 4
    1 2 3 4							# 	reverse(intro,1)
    
    VERSE 1
    So I'm still in love with you                           # 7 syllables
    Yet is in love with you e-nough                         # 8 syllables
    Yet in love with you I am                               #   copy(verse,1)
    Yet I do love you so true-ly                            #   copy(verse,2)
    
    PRECHORUS 1
    When you love your tick-et o                            # 7 syllables
    But you love your life too o                            # 	transpose(prechorus,1,-2)
    
    CHORUS 1
    Love stand-ing still, love stand strong                 # 7 syllables
    Love stand though the na-tions rise                     #   copy(chorus,1)
    Love stand-ing still, love stand strong                 # 	transpose(chorus,1, 5)
    And say the grea-test love of all                       # 8 syllables
    
    VERSE 2
    Oh, now eve-ry-bod-y sing,                              # 7,8,7,8 syllables
    I, I, I feel good a-bout love
    To-geth-er we went like this
    Yes I do love you so hon-ey
    
    PRECHORUS 2
    Than the way you love me now                            # 7 syllables
    Than the way you love me now                            # 7 syllables
    
    CHORUS 2
    Love stand-ing still, love stand strong                 # 7,7,7,8 syllables
    Love stand though the na-tions rise
    Love stand-ing still, love stand strong
    And say the grea-test love of all
    
    SOLO                                                    # invert more recognisable than reverse, and reverse more recognisable than reverse invert
    1 2 3 4 5 6 7 8
    1 2 3 4 5 6 7 8              		                    #   invert(solo, 1, C5)
    1 2 3 4 5 6 7 8            	                            #   reverse(solo, 1)
    1 2 3 4 5 6 7 8           	                            #   invert(solo, 3, C5)
    
    BRIDGE 1
    Eve-ry time you feel a-lone out there in the night      # 12 syllables
    I pull you in and love you so just as you like          #   copy(bridge, 1)
    
    CHORUS 3
    Love stand-ing still, love stand strong                 # 7,7,7,8 syllables
    Love stand though the na-tions rise
    Love stand-ing still, love stand strong
    And say the grea-test love of all
    
    CHORUS 4
    Love stand-ing still, love stand strong                 # 7,7,7,8 syllables
    Love stand though the na-tions rise
    Love stand-ing still, love stand strong
    And say the grea-test love of all
    
    OUTRO 1
    1 2 3 4					# 	copy(intro,1)
    1 2 3 4					# 	transpose(outro,1,2)
    1 2 3 4					# 	transpose(outro,1,4)
    1 2 3 4					# 	transpose(outro,1,8)


### How to markup a lyric file

* Add sections: VERSE, CHORUS etc
* For each line append: # ? syllables and replace ? with number of syllables in the line
* If desired, adjust number of syllables in lyric lines or add rhymes
* Given number of syllables decide on suitable line functions e.g. on verse line 2 append:  #   copy(verse,1)

   
### After running MarkMelGen, check program output for warnings 
e.g. Lyric syllable count different in Verse 2:

      Verse 2 ...
  
      section_line_num 1
      Warning: less notes than syllables in later section. note_num, number_of_syllables  5 7
      sect Section.VERSE

---

## InputMusic
### Edit INPUT_MUSIC_FILENAME to have only the melody in one key

Starting from a midi file, open the .mid in MuseScore.
To find the melody channel / stave in MuseScore, View>Mixer (F10),
Play, click S to toggle Solo. MIDI channel shown in top right of Mixer.

Starting from a Music XML file, 
e.g. on windows C:\Users\<username>\AppData\Local\Programs\Python\Python39\Lib\site-packages\music21\corpus , 
open the .mxl in MuseScore.

#### Delete unwanted staves:

Edit>Instruments, select unwanted stave, Remove from Score.

#### Delete unwanted clefs:
If the melody is on a piano stave, and you want to delete the bass clef or a harmony clef.
Press i for the instruments' dialog.
Click Stave 2 on the piano then the "Remove from score" button in the middle of the box.
Click OK and the staff will be gone.
Any unwanted extra notes/rests may be selected and Deleted.

#### Delete unwanted bars:
For example bars in a different key signature . In MuseScore 3: In top ribbon, select "Page View". Page Down to 2nd key signature.
To select a range of measures:
1. Click on a blank space in the first desired measure;
2. Hold down Shift, then click on a space in the last measure of the desired range.

Then select Tools → Remove Selected Range or press Ctrl + Del (Mac: ⌘ + Backspace )

#### Save as MusicXML:
Finally, save your edits with File>Export, Export To: MusicXML, Export... (or File > Save as and change file extension to .mxl). 

---

## Output

The standard output includes progress and debug information.

How to read text streams in output for 4/4 time with triplets:

    offset 0.0000 	 bar 1.0000 	 o 0.0 	 + ql 1.0 	 = o_end 1.0000 	 note qLen lyric:	 G4 	 1.0 	 1
    offset 1.0000 	 bar 1.2500 	 o 1.0 	 + ql 1/6 	 = o_end 1.1667 	 note qLen lyric:	 F4 	 1/6 	 2
    offset 1.1667 	 bar 1.2917 	 o 7/6 	 + ql 1/6 	 = o_end 1.3333 	 note qLen lyric:	 C4 	 1/6 	 3
    offset 1.3333 	 bar 1.3333 	 o 4/3 	 + ql 1/6 	 = o_end 1.5000 	 note qLen lyric:	 E4 	 1/6 	 4
    offset 1.5000 	 bar 1.3750 	 o 1.5 	 + ql 1/6 	 = o_end 1.6667 	 note qLen lyric:	 C4 	 1/6 	 5
    offset 1.6667 	 bar 1.4167 	 o 5/3 	 + ql 1/6 	 = o_end 1.8333 	 note qLen lyric:	 G3 	 1/6 	 6
    offset 1.8333 	 bar 1.4583 	 o 11/6 	 + ql 1/6 	 = o_end 2.0000 	 note qLen lyric:	 G3 	 1/6 	 7
    offset 2.0000 	 bar 1.5000 	 o 2.0 	 + ql 1/6 	 = o_end 2.1667 	 note qLen lyric:	 D3 	 1/6 	 8
    offset 2.1667 	 bar 1.5417 	 o 13/6 	 + ql 11/6 	 = o_end 4.0000 	 rest quarterLength: 11/6
    offset 4.0000 	 bar 2.0000 	 o 4.0 	 + ql 1.0 	 = o_end 5.0000 	 note qLen lyric:	 F4 	 1.0 	 1

* offset  - starts at 0.0000 and increases by 1.0000 per beat, so offset 4.0000 is the start of bar 2.0000
* bar     - starts at 1.0000 and increases by 0.2500 per beat, so bar 1.5000 half way though the first bar
* o       - e.g. o 7/6 is the fractional version of the float offset 1.1667
* ql      - is the length of the note or rest in quarter lengths e.g. 1 beat = 1.0, a sixth of a beat =  1/6
* o_end   - is the float offset of the end of a note or rest e.g. o 13/6 	 + ql 11/6 	 = o_end 4.0000 is a rest to end of bar (which museScore will expand to and appropriate number of squiggles and dots)
* if note then e.g. note qLen lyric:	 D3 	 1/6 	 Love
* if rest then e.g. rest quarterLength: 11/6

### Play output with Metronome
 If using MuseScore, you can add a metronome by
 View > Play Panel (F11 toggle) and  by Metronome, click the right icon for play metronome.

### Avoid output problems by changing the configuration.
If the INPUT_MUSIC_FILENAME is blank then MarkMelGen 
processes all the music XML (.mxl) files in the INPUT_MUSIC_PATH directory.
Using more than one input music file means more configuration filters may be required
to get desired output.

If output is corrupted when opening in MuseScore (e.g. Load Error...File corrupted. Show Details..., Cancel, Ignore) , 
or score shows grey rests, or metronome skips , or there is a duration exception from MarkMelGen, try clicking Ignore or rerunning or 
amending the configuration to have 
 DUR_RATIONAL = True.

Alternatively, check the output in other (free) score writing software e.g. 
* Sibelius First https://my.avid.com/get/sibelius-first
* https://opensheetmusicdisplay.github.io/demo/
* https://frescobaldi.org/ Frescobaldi 3.1.3  File>Import MusicXML.


## Tools
### song_section_values


An extra program, **song_section_values**, is provided to analyse an existing song melody 
to provide section data that can be copied and pasted into a MarkMelGen configuration file.  

Here is the help for the song_section_values program:


    song_section_values.py -h
    usage: song_section_values.py [-h] [-m MXLFILE]
    
    optional arguments:
      -h, --help            show this help message and exit
      -m MXLFILE, --mxlfile MXLFILE
                            music file path, relative to current working directory e.g. input/music/sectioned/music.mxl (MusicXML files are .mxl for
                            compressed files). The MusicXML file must contain staff text words to identify the section start point: intro, verse, prechorus,
                            chorus, solo, bridge or outro. In MuseScore, to create staff text choose a location by selecting a note or rest and then use the
                            menu option Add → Text → Staff Text, or use the shortcut Ctrl+T.

There is example music with sections supplied e.g.

    song_section_values.py -m input\music\_sectioned\mozart-k156-1.mxl

Here is an example run of **song_section_values**.
    
    C:\Users\pawda\AppData\Local\Programs\Python\Python39\python.exe D:/My_Documents/paul_cucuron/bin/github/MarkMelGen/pycharm/song_section_values.py -m private/input/music/_sectioned/xxx.mxl

    mxlfile fully qualified      : private/input/music/_sectioned/xxx.mxl
    Input song raw song_key.tonic.name, song_key.mode =  G major
    Need to normalise to C major or A minor.
    Transposed (if required) input song interval song_key.tonic.name, song_key.mode =  <music21.interval.Interval P-5> C major
    mxlfile_normalised_output      : .\private/input/music/_sectioned\xxx_in_C.mxl
    Reading mxlfile_normalised...
    Looking for sections: intro, verse, prechorus, chorus, solo, bridge, or outro... 
    # ------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------
    
    # section 1 name      = Verse 1
    [song_verse]
    DURATION_SET = ['0.25', '0.5', '1.0']
    DUR_LEAST = 0.25
    DUR_LONGEST = 1.0
    DUR_PREV_DIFF = 4.0
    DUR_RATIONAL = True
    DUR_TUPLET = False
    REST_NOTE_LINE_OFFSET = 1.0
    TONES_ON_KEY = True
    TONE_PREV_INTERVAL = 12
    TONE_RANGE_BOTTOM = G3
    TONE_RANGE_TOP = B4
    TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    
    # ------------------------------------------------------------------------------------------------------
    
    # section 2 name      = prechorus 1
    [song_prechorus]
    DURATION_SET = ['0.25', '0.5']
    DUR_LEAST = 0.25
    DUR_LONGEST = 0.5
    DUR_PREV_DIFF = 2.0
    DUR_RATIONAL = True
    DUR_TUPLET = False
    REST_NOTE_LINE_OFFSET = 2.5
    TONES_ON_KEY = True
    TONE_PREV_INTERVAL = 4
    TONE_RANGE_BOTTOM = C4
    TONE_RANGE_TOP = F4
    TONE_SCALE_SET = ['C', 'D', 'E', 'F']
    
    # ------------------------------------------------------------------------------------------------------
    
    # section 3 name      = Verse 2
    [song_verse]
    DURATION_SET = ['0.25', '0.5', '0.75', '1.0']
    DUR_LEAST = 0.25
    DUR_LONGEST = 1.0
    DUR_PREV_DIFF = 4.0
    DUR_RATIONAL = True
    DUR_TUPLET = False
    REST_NOTE_LINE_OFFSET = 1.0
    TONES_ON_KEY = True
    TONE_PREV_INTERVAL = 12
    TONE_RANGE_BOTTOM = G3
    TONE_RANGE_TOP = B4
    TONE_SCALE_SET = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    
    # ------------------------------------------------------------------------------------------------------
    
    # section 4 name      = prechorus 2
    [song_prechorus]
    DURATION_SET = ['0.25', '0.5']
    DUR_LEAST = 0.25
    DUR_LONGEST = 0.5
    DUR_PREV_DIFF = 2.0
    DUR_RATIONAL = True
    DUR_TUPLET = False
    REST_NOTE_LINE_OFFSET = 2.25
    TONES_ON_KEY = True
    TONE_PREV_INTERVAL = 5
    TONE_RANGE_BOTTOM = C4
    TONE_RANGE_TOP = F4
    TONE_SCALE_SET = ['C', 'D', 'E', 'F']
    
    # ------------------------------------------------------------------------------------------------------
    
    # section 5 name      = Chorus 1
    [song_chorus]
    DURATION_SET = ['0.25', '0.5', '1.5']
    DUR_LEAST = 0.25
    DUR_LONGEST = 1.5
    DUR_PREV_DIFF = 3.0
    DUR_RATIONAL = True
    DUR_TUPLET = False
    REST_NOTE_LINE_OFFSET = 1.5
    TONES_ON_KEY = True
    TONE_PREV_INTERVAL = 10
    TONE_RANGE_BOTTOM = D4
    TONE_RANGE_TOP = C5
    TONE_SCALE_SET = ['A', 'C', 'D', 'F', 'G']
    
    # ------------------------------------------------------------------------------------------------------
    
    # section 6 name      = bridge 1
    [song_bridge]
    DURATION_SET = ['0.25', '0.5', '1.0']
    DUR_LEAST = 0.25
    DUR_LONGEST = 1.0
    DUR_PREV_DIFF = 4.0
    DUR_RATIONAL = True
    DUR_TUPLET = False
    REST_NOTE_LINE_OFFSET = 3.0
    TONES_ON_KEY = False
    TONE_PREV_INTERVAL = 11
    TONE_RANGE_BOTTOM = D4
    TONE_RANGE_TOP = C#5
    TONE_SCALE_SET = ['A', 'C#', 'D', 'F', 'G']
    
    ...

    # ------------------------------------------------------------------------------------------------------
    # number_of_sections_found = 8
    # song structure:
    # long    = Verse 1-prechorus 1-Verse 2-prechorus 2-Chorus 1-bridge 1-Verse 3-Chorus 2
    # name    = verse-prechorus-verse-prechorus-chorus-bridge-verse-chorus
    # initial = vpvpcbvc
    # letter  = ABABCDAC

---

## Workflow

Example Song Writing Workflow.

### Input lyrics
* Choose/write lyrics.

If using https://theselyricsdonotexist.com/
* Choose a song topic word e.g. perambulate, lyrics Genre and Mood, press the "Generate My Lyrics" button.

* Divide words into syllables e.g.https://melobytes.com/en/app/syllabication (will need to manually check and correct)

### Input music
* Choose Music you would like the song to use.
* Find MIDI file of desired music. Edit file so it only contains the melody. e.g. in MuseScore:
View>Mixer (F10), solo tracks to find melody instrument.
Edit>Instruments (I), select each unwanted stave, Remove from Score.  File>Export, Export To: MusicXML, Export.
* If you have two or more input music files consider putting them in a folder and using that.
* Copy an example an MarkMelGen.conf file and edit to use the above Lyrics and Music files.
Ensure Lyrics file has desired section headings e.g. verse 1, prechorus 1, chorus 1, bridge etc.

* Perform an initial run of MarkMelGen to check lyric syllable consistency. Search output for "Warning:Lyric".  e.g.
"Warning:Lyric-First Section.VERSE line 1 has a lyric at note 9 but later verse 2 has no lyric there."
Correct Lyric file and rerun.

* if desired, get example MarkMelGen.conf section settings using a separate utility program called song_section_values.
Prepare the input music to add section text before running the song_section_values program.
Open the input music in Musescore, select the first section note, Ctrl+T enter section name e.g. verse 1, press Escape etc.
If the input music appears to only have a verse and chorus structure,
for analysis purposes consider splitting the verse to end in a prechorus by choosing a note in the verse where the music changes.
Similarly the chorus can be split to end in a bridge.
Run song_section_values and copy the section output and paste into the section parts of your MarkMelGen.conf.

### Output song with lyrics and melody
* Run MarkMelGen to get output song with lyrics and melody.
* Adjust MarkMelGen.conf to improve song e.g. desired DURATION_SET and TONE_RANGE for each section.
* Consider if you want to repeat a chorus or add sections e.g. intro, solo, outro.
Add these to the input lyrics file e.g.


    intro
    1 2 3
    1 2 3 4 5 6

### Add Chords

Use another program to add chords to the MarkMelGen melody e.g.

* Band in a Box can take a melody and generate chords. 
The re-harmonist will generate a chord progression, given a melody, 
in a style of your choosing e.g. Jazz or New Age. 
* VeeHarmGen is available on GitHub. 
VeeHarmGen is a Vertical Harmony Generation program that takes an input musicxml file containing a melody and creates output musicxml files with added Chord Symbols.
