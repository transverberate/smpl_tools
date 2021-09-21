# smpl_tools

A collection of python scripts useful for managing, manipulating, extracting and 
exporting '90s sample CDs.


# Installation


## Prerequisites 

This toolset requires [Python 3](https://www.python.org/download/releases/3.0/) 
and [ffmpeg](https://ffmpeg.org/download.html) to be installed and added to the
user's `PATH`. Often times, the installations of python and ffmpeg will *not*
automatically add these programs to the system `PATH`. Searching Google for questions
like 'how to add ffmpeg to my PATH' etc. usually yields good explanations on this
process.

To confirm `python` is in your system's `PATH`, open an instance of command prompt and type
`python --version` (sometimes it will be installed as `python3`, in which case 
\- every time `python` is encountered in this document, it should be replaced with `python3`).
If present, python should respond with its version number.

To confirm `ffmpeg` is in your system's `PATH`, open an instance of command prompt and type
`ffmpeg -version`. If present, ffmpeg should respond with its version number.


## Installing this tool-set

Download the contents of this repo and extract them to a convenient place on your machine.
Open an instance of command prompt and navigate to the location of you extracted the repo.
You should now be in the folder with `setup.py` and the sample `smpl_tools` directory.
Enter the command,

```
python -m pip install cython
```

to install the [Cython](https://cython.org/) to your python package library. This is needed
to compile the [numpy](https://numpy.org/) library that this tool-set makes use of.

Next, enter the command (**note the period!**),

```
python -m pip install .
```

to install `smpl_tools` to your python package library.

Finally, confirm that `smpl_tools` has been installed properly by entering the 
command,

```
python -m smpl_tools --help
```

If successfully installed, `smpl_tools` should respond with an explanation of its command usage.

## Updating this tool-set
To update these scripts having already previously installed an older version, download the
latest version from the github repo, open a command prompt/shell window in the directory in
which you downloaded the repo and run the command (**note the period!**),

```
python -m pip install .
```


# Common Tasks

## Splitting CDDA sample tracks

Many sample CDs from the '90s encoded multiple samples on a single CDDA track. 
Isolating individual samples requires that they be spliced out manually in an audio editor. 
Often, these samples were assigned names which were tabulated in a CD’s companion booklet. 
Unfortunately, the waveforms extracted from CDDA tracks do not contain any of this naming 
information - making the process of locating a particular sample by name arduous.

This tool-set provides a **split-by-silence** script that assists in the process of splitting 
CDDA tracks into individual samples by locating the silent segments of a track and splitting 
the track at the onset of sound.


### A simple splitting operation

A basic split-by-silence command has the following form

```
python -m smpl_tools split_by_silence [source] [-s duration] [-c amplitude] [-d destination]
```

In its most basic form, these parameters represent,

- `source`: A file-path to a `.wav` containing the CDDA waveform.
- `duration`: The duration of silence (in *seconds*) that should 
              be taken to indicate the start of a new sample
              (*default value*: 0.4).
- `amplitude`: The amplitude (in *decibels*) below which the waveform is 
               considered to be "silent" (*default value*: -60).
- `destination`: The directory where the extracted samples will be placed
                 (*default value is the same directory as the source*).


### Splitting multiple CDDA tracks

To split multiple tracks, place all the tracks in a single folder and call the 
`split_by_silence` command on the directory, rather than a single file. 
If the source folder contains tracks named `trackA.wav`, `trackB.wav`... etc., 
this command will produce the files 
`trackA_01.wav`, `trackA_02.wav`... `trackB_01.wav`, `trackB_02.wav`... etc.


### Batch splitting & renaming multiple CDDA tracks

Often, one wishes to split *multiple tracks* into *multiple samples* where the
filename of each sample given the name assigned to it by the CD’s sample listing.
This task is impractical to accomplish using a single command-line call. 
Rather, a separate metadata file is needed to describe the 
`split-by-silence` parameters for each track.

To call the `split_by_silence` command in batch mode, include the `-b` 
switch in the command

```
python -m smpl_tools split_by_silence [source] [-b json_batchjob] [-d destination]
```

These parameters represent

- `source`: The root directory from which script will search for the files 
            specified by the batch job. Usually, this is the folder containing the
            CDDA .wav files.
- `json_batchjob`: A path to the json file containing the metadata for 
                   this batch-job.
- `destination`: The destination directory for the files produced by the script.

Note that the parameters specifying the amplitude and duration of silence are
*not* given here. Rather, they are provided per-track in the meta-data file.


#### Contents of the metadata file

This metadata file is a json file whose top-level element is an array of *tracks*. 
Each track is a dictionary containing the keys

-	`source`: the *filename* of the track's `.wav` file
-	`silence`: The *duration of silence (in seconds)* that should be taken to 
               indicate the start of a new sample
-	`amplitude`: The *amplitude in decibels* below which the waveform is 
                 considered to be "silent"
-	`sample_names`: An *ordered array of strings* containing the file names of 
                    each sample found for this track

Technically, `source` is the only required key. If the other keys are 
left unspecified, the default values from the command definition
above will be used. The power of the metadata file lies in the
`sample_names` key. This is what allows for custom renaming of 
samples within a track in the order they are split.

To better understand the layout of a metadata file, consider the
following example file

```json
[
  {
    "source": "Track 01.wav",
    "silence": 0.95,
    "amplitude": -100,
    "sample_names": [
      "Alligator.wav",
      "Baboon.wav",
      "Caribou.wav",
      "Dalmatian.wav",
      "Elephant.wav"
    ]
  },
  {
    "source": "Track 02.wav",
    "silence": 0.4,
    "amplitude": -60,
    "sample_names": [
      "Fox.wav",
      "Gorilla.wav",
      "Hare.wav",
      "Jaguar.wav"
    ]
  },
]
```

Its top-level element is an array (indicated by the `[]`), that
contains two track entries (contained in `{}`). Each track entry
contains the keys `source`, `silence`, `amplitude` and `sample_names`.

If this metadata is placed in a file called `myjob.json` 
and ran as a batch job with the command

```
python -m smpl_tools split_by_silence cdtracks/ -b myjob.json -d output/
```

The script will search for the files `Track 01.wav` and 
`Track 02.wav` in the folder `cdtracks/`. 

It will split `Track 01.wav`
into five separate samples (if possible) using the parameters 
`-s 0.95`, and `-c -100`. Finally, it will write the samples
to the `output/` directory with the filenames `Alligator.wav`,
`Baboon.wav`, `Caribou.wav`, `Dalmatian.wav`, and `Elephant.wav`
(in that order).

It will split `Track 02.wav`
into four separate samples in a similar manner, this time,
using the parameters `-s 0.4`, and `-c -60`.


### Ignoring certain samples

Occasionally the script may detect a sample that is incorrect or unneeded.
This is often the case for repeat/duplicate samples present in some tracks
(many Zero-G CDs will have tracks that arbitrarily repeat certain samples
and not others). To ignore a sample, put `null` (not as string but as a literal)
at the position in the `sample_names` key where that sample occurs.

Consider the following track entry (as part of a larger file)

```json
{
    "source": "Track 36.wav",
    "silence": 0.4,
    "amplitude": -100,
    "sample_names": [
        "Fox.wav",
        null,
        "Gorilla.wav",
        "Hare.wav",
        "Jaguar.wav"
    ]
},
```

When the script encounters this track entry, it will attempt to split the track
waveform into **five** samples but only export **four** samples.
It will *skip* exporting the second sample it detects.


## Development and Contributing

This tool-set is in active development and has only been rigorously 
tested in Windows 10. If a bug is found, please report it as an issue.
Feature requests are welcome, but there is *no* guarantee I will 
be able to implement it.

