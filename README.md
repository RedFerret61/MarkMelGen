# MarkMelGen
MarkMelGen is a Markov Melody Generation program that 
takes configuration, lyric, and example music files and 
creates a tune for the supplied words.

The latest release has been tested on: 
* Windows 10 20H2 
  - with MuseScore 3.6.2, Python 3.9.6, music21 v 7.1.0 
* macOS Big Sur 11.6.1 
  - with MuseScore 3.6.2, Python 3.10.0, music21 v 7.1.0 
* Ubuntu 20.04
  - with MuseScore 3.2.3, Python 3.8.10, music21 v 7.1.0

**Table of Contents**

1. [MarkMelGen Installation instructions for Windows](#MarkMelGen Installation instructions for Windows)
2. [MarkMelGen Installation instructions for macOS](#MarkMelGen Installation instructions for macOS)
3. [MarkMelGen Installation instructions for Ubuntu](#MarkMelGen Installation instructions for Ubuntu)
4. [Configuration](#Configuration)
5. [Input Lyrics](#Input Lyrics)
6. [Input Music](#Input Music)
7. [Output](#Output)
8. [Tools: song_section_values](#Tools)
9. [Example Song Writing Workflow](#Example Song Writing Workflow)

*Note: GitHub has a full table of contents with links in the header icon (top left of the readme.md).*

---

## MarkMelGen Installation instructions for Windows
Pre-requisites for MarkMelGen include MuseScore, Python, and Music21.

### MuseScore Windows installation
Browse to https://musescore.org/en/download
 
Download for Windows and run installer.
### Python Windows installation
 1. Firstly check python version required by Music21.
 see https://web.mit.edu/music21/doc/installing/installWindows.html

      in October 2021 this stated  "Windows users should download and install Python version 3.8 or higher."
* For example
  * Python 3.9.6 worked for me with music21 versions 6.7.1 and 7.1.0 
  * Python 3.10.0 did not work for me with music21 version 7.1.0 (numpy not compatible)

2. Browse to https://www.python.org/downloads/windows
    
    Download desired version (may not be the latest) and run.
    
    Select "Add Python to PATH". Install.


3. Check it works: Start, search, cmd, click on Command Prompt, type:
   
    python --version

    Expect the version to be displayed e.g. Python 3.9.6

### Music21 Windows installation
 
1. Music21 Installation details at https://web.mit.edu/music21/doc/installing/installWindows.html

    At command prompt:

    pip install music21

3. Check music21 version installed with:

   pip list

4. Configure with (press return to accept defaults):

   python -m music21.configure

if you have problems and want to try different versions. Uninstall music21 with:

   pip uninstall music21

Uninstall Python by opening Control Panel, Click "Uninstall a Program", Scroll down to Python and click uninstall for each version you don't want anymore.

To upgrade music21 at a later date to the latest version, 'pip uninstall music21' then 'pip install music21' again.

### MarkMelGen Windows installation

#### Install MarkMelGen on Windows
 Download release zip to desired directory for MarkMelGen and unzip with right click Extract All ...
#### Run MarkMelGen on Windows 

 In a Command Prompt window change to install directory and run MarkMelGen e.g.:

    cd C:\Users\paul\Documents\pycharm
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


#### Run MarkMelGen test files

 In a Command Prompt window type run_conf_test to run the configuration files in the conf directory e.g.:


    :: to run one conf test file without graphs:
    python MarkMelGen.py -g -c conf/test/TONE_SCALE_ON_ANHEMITONIC.conf
    :: to run all the conf test files automatically 
    :: (without Pressing Enter or Closing Windows):
    run_conf_test

To see the run_conf_test batch file results, Start File Explorer and go to the output folder in your MarkMelGen install directory.
Double-click on a musicxml file to open it in MuseScore. When finished, Close MuseScore.

---

## MarkMelGen Installation instructions for macOS
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

## MarkMelGen Installation instructions for Ubuntu
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

Ignore Fortran to Python warning:  WARNING: The scripts f2py, f2py3 and f2py3.8 are installed in 
    '/home/admin3/.local/bin' which is not on PATH.
  Consider adding this directory to PATH or, if you prefer to suppress this warning, 
  use --no-warn-script-location.



3. Check music21 version installed with:

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
    
    INPUT_MUSIC_PATH =
    # INPUT_MUSIC_PATH = input/music/
    # INPUT_MUSIC_PATH = input/music/bach/
    # INPUT_MUSIC_PATH = input/music/beethoven/
    # INPUT_MUSIC_PATH = input/music/chopin/
    # INPUT_MUSIC_PATH = input/music/essenFolksong/
    # INPUT_MUSIC_PATH = input/music/mozart/
    # INPUT_MUSIC_PATH = input/music/rachmaninov/
    # INPUT_MUSIC_PATH = input/music/trecento/
    
    OUTPUT_PATH =
    # OUTPUT_PATH = output/
    
    
    
    
    [filenames]
    # The input filenames used.
    
    INPUT_LYRICS_FILENAME = Lyrics.txt
    # INPUT_LYRICS_FILENAME = lovePopHappy.txt
    
    # if INPUT_MUSIC_FILENAME is blank then MarkMelGen processes all the .mxl files in the INPUT_MUSIC_PATH directory.
    INPUT_MUSIC_FILENAME = Music.mxl
    # INPUT_MUSIC_FILENAME =



    ... etc

If the INPUT_MUSIC_FILENAME is blank then MarkMelGen processes 
all the music XML (.mxl) files in the INPUT_MUSIC_PATH directory.

Edit MarkMelGen.conf configuration as desired,
later sections are commented out with # at the beginning of the line.


* Use different configuration files to get different output e.g.

      MarkMelGen.py -c conf/test/TIME_SIG_WANTED-12-8.conf

## Input Lyrics
### Create an INPUT_LYRICS_FILENAME
 If you have some lyrics then manually add desired section names:
 intro, verse, prechorus, chorus, break, bridge, or outro.
 otherwise you can use a website such as https://theselyricsdonotexist.com/

 Given lyrics with section headers, you can use a website to split the lyrics into syllables,
 such as https://melobytes.com/en/app/syllabication
 Then remove hyphens added to section names.

e.g. 

    Verse 1
    So I'm still in love with you
    Yet is in love with you e-nough
    Yet in love with you I am too
    Yet I love you true-ly

    Prechorus 1
    When you love your tick-et o
    But you love your life too o

    Chorus 1
    Love stand-ing still, love stand strong
    Love stand though the na-tions rise
    Love stand-ing still, love stand strong
    And say the grea-test love of all

    ...etc
### After running MarkMelGen, check program output for warnings 
e.g. Lyric syllable count different in Verse 2:

      Verse 2 ...
  
      section_line_num 1
      Warning: less notes than syllables in later section. note_num, number_of_syllables  5 7
      sect Section.VERSE

---

## Input Music
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

### Play output with Metronome
 If using MuseScore, you can add a metronome by
 View > Play Panel (F11 toggle) and  by Metronome, click the right icon for play metronome.

### Avoid output problems by changing the configuration.
If the INPUT_MUSIC_FILENAME is blank then MarkMelGen 
processes all the music XML (.mxl) files in the INPUT_MUSIC_PATH directory.
Using more than one input music file means more configuration filters may be required
to get desired output.

If output is corrupted when opening in MuseScore 3.6.2 , or there is a duration exception from MarkMelGen, try amending the configuration to have 
 DUR_RATIONAL = True.

Alternatively check the output in another score writing software e.g. 
* https://opensheetmusicdisplay.github.io/demo/
* https://frescobaldi.org/ Frescobaldi 3.1.3  File>Import MusicXML.


## Tools: song_section_values


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
                            chorus, break, bridge or outro. In MuseScore, to create staff text choose a location by selecting a note or rest and then use the
                            menu option Add → Text → Staff Text, or use the shortcut Ctrl+T.

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

## Example Song Writing Workflow

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

