import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from typing import List, Union
import json

from . import ffmpeg
from .audio_stream import AudioStream
from .audio_stream import split_by_silence_ts


def _save_slices(
    src_filename: str, 
    slices: List[int], 
    filenames: List[str],
    ignore_indices: List[int]
):
    
    for i, start_ts in enumerate(slices):
        end_ts = None if i + 1 >= len(slices) else slices[i + 1]

        dst_filename = filenames[i]
        if i not in ignore_indices:
            ffmpeg.copy_audio_segment(
                src_filename, 
                dst_filename, 
                start_ts, 
                end_ts
            )
            print(f"Wrote: {dst_filename}")
    return


def _determine_output_filenames(
        destination_arg:    Union[str, List[str], None],
        source_filename:    str,
        output_files_cnt:   int
)->List[str]:

    destination_arg = destination_arg or []

    if isinstance(destination_arg, str) or len(destination_arg) < output_files_cnt:
        basename = ".".join(os.path.basename(source_filename).split(".")[:-1])
        
        if isinstance(destination_arg, str):
            dst_filenames = []
            r = range(output_files_cnt)
            directory = destination_arg
        else:
            dst_filenames = destination_arg
            r = range(len(destination_arg), output_files_cnt)
            if len(destination_arg) < 1:
                directory = os.path.dirname(source_filename)
            else:
                directory = os.path.dirname(destination_arg[-1])

        for i in r:
            new_name = os.path.join(directory, f"{basename}_{str(i+1):02d}.wav")
            dst_filenames.append(new_name)
    else:
        dst_filenames = destination_arg

    return dst_filenames


def split_file_by_silence(
        src_filename: str,
        destination: Union[str, List[str]] = None,
        min_duration: float = 0.4,
        db_cutoff: float = -60,
        offset_correction: float = 0,
        ignore_indices: List[int] = None
):
    print(f"Splitting {src_filename}")
    ignore_indices = ignore_indices or []

    # calculate the onset timestamps
    stream = AudioStream(src_filename)
    slices = split_by_silence_ts(
        stream, 
        min_duration=min_duration,
        db_cuttoff=db_cutoff,
        offset_correction=offset_correction
    )

    dst_filenames = _determine_output_filenames(
        destination,
        src_filename,
        len(slices)
    )

    _save_slices(src_filename, slices, dst_filenames, ignore_indices)
    return


def split_file_by_silence_batch(
        source_dir:         str,
        destination_dir:    str,
        batch_filename:     str
):
    with open(batch_filename, "r") as json_file:
        entries = json.load(json_file)
    
    for entry in entries:
        filenames = entry.get("sample_names", [])
        to_remove: List[int] = []
        for i, filename in enumerate(filenames):
            if filename is None:
                to_remove.append(i)
        
        # Check extension
        filename_in: str = entry["source"]
        tokens = filename_in.split(".")
        if len(tokens) < 1 or len(tokens[-1]) > 6:
            filename = ".".join([filename_in, "wav"])
        else:
            filename = filename_in

        source = os.path.join(source_dir, entry["source"])
        def make_filename(filename):
            if filename is not None:
                return os.path.join(destination_dir, filename)
            else:
                return ""
        destinations = [make_filename(filename) for filename in filenames]
        min_duration = entry.get("silence", 0.4)
        db_cutoff = entry.get("amplitude", -60)

        split_file_by_silence(
            source,
            destinations,
            min_duration=min_duration,
            db_cutoff=db_cutoff,
            ignore_indices=to_remove
        )


__all__ = [
    "split_file_by_silence", 
    "split_file_by_silence_batch"
]