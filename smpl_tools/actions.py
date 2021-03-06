import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from typing import Any, Dict, List, Union
import json
import re

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


def _determine_output_samplenames(
        destination_arg:    Union[str, List[str], None],
        source_filename:    str,
        output_files_cnt:   int
)->List[str]:

    destination_arg = destination_arg or []

    if isinstance(destination_arg, str) or len(destination_arg) < output_files_cnt:
        basename = ".".join(os.path.basename(source_filename).split(".")[:-1])
        if len(basename) <= 0:
            basename = source_filename
        
        if isinstance(destination_arg, str):
            dst_filepaths = []
            r = range(output_files_cnt)
            directory = destination_arg
        else:
            dst_filepaths = destination_arg
            r = range(len(destination_arg), output_files_cnt)
            if len(destination_arg) < 1:
                directory = os.path.dirname(source_filename)
            else:
                directory = os.path.dirname(destination_arg[-1])

        for i in r:
            new_name = os.path.join(directory, f"{basename}_{(i+1):02d}.wav")
            dst_filepaths.append(new_name)
    else:
        dst_filepaths = destination_arg

    for dst_filepath in dst_filepaths:  # Ensure every directory exists
        if dst_filepath is not None and len(dst_filepath) > 0:
            os.makedirs(os.path.dirname(dst_filepath), exist_ok=True)

    return dst_filepaths


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

    dst_filenames = _determine_output_samplenames(
        destination,
        src_filename,
        len(slices)
    )

    _save_slices(src_filename, slices, dst_filenames, ignore_indices)
    return


_REGEX_NAMING_PATTERN = re.compile(r"\%\((\w+)\)")
def _process_naming_pattern(
    naming_pattern: str,
    sample_name: str,
    track_name: str
)->str:


    def remove_wav_ext(str_in: str)-> str:
        str_out = str_in.strip()
        if str_out.lower()[-4:] == ".wav":
            str_out = str_out[:-4]
        return str_out


    sample_name = remove_wav_ext(sample_name)
    track_name = remove_wav_ext(track_name)

    naming_pattern_map = {
        "smpl": sample_name,
        "trck": track_name
    }
    
    tokens = _REGEX_NAMING_PATTERN.split(naming_pattern)

    tokens_iter = iter(tokens)
    plain = [next(tokens_iter)]
    delim = []
    while True:
        try: 
            delim.append(next(tokens_iter))
            plain.append(next(tokens_iter))
        except StopIteration:
            break
    
    delim_rpl = list(map(lambda x: naming_pattern_map.get(x, ""), delim))
    to_comb = [plain[0]]
    for i in range(len(delim)):
        to_comb.append(delim_rpl[i])
        to_comb.append(plain[i + 1])

    if plain[-1][-4:].lower() != ".wav":
        to_comb.append(".wav")
    
    result = "".join(to_comb)
    return result
    


def _split_file_by_silence_batch(
        entries:            List[Dict[str, Any]],
        source_dir:         str,
        naming_pattern:     str
):
    
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

        source_path = os.path.join(source_dir, entry["source"])
        def make_filename(filename):
            if filename is not None:
                return _process_naming_pattern(naming_pattern, filename, entry["source"])
            else:
                return ""
        destinations = [make_filename(filename) for filename in filenames]
        min_duration = entry.get("silence", 0.4)
        db_cutoff = entry.get("amplitude", -60)

        split_file_by_silence(
            source_path,
            destinations,
            min_duration=min_duration,
            db_cutoff=db_cutoff,
            ignore_indices=to_remove
        )


def split_file_by_silence_batch(
        batch_filename:     str,
        source_dir:         str,
        destination_dir:    str,
        naming_pattern:     str = None
):
    source_dir = source_dir
    destination_dir = destination_dir
    naming_pattern = naming_pattern or "%(dst)/%(smpl).wav"

    with open(batch_filename, "r") as json_file:
        json_data = json.load(json_file)

        if not isinstance(json_data, dict):
            entries = json_data
        else:
            entries = json_data.get("entries", [])
    
    naming_pattern = naming_pattern.replace(
        "%(dst)", 
        destination_dir
    )

    _split_file_by_silence_batch(
        entries,
        source_dir,
        naming_pattern
    )
        
    


__all__ = [
    "split_file_by_silence", 
    "split_file_by_silence_batch"
]