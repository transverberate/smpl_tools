import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from typing import Any, Callable, Dict, Tuple
import subprocess as sp
import json
from enum import Enum
import enum
import re
import shutil


class FfmpegNotInPath(Exception):
    pass


FFMPEG_BIN = "ffmpeg"
_ffmpeg_path = shutil.which(FFMPEG_BIN)
if _ffmpeg_path is None:
    raise FfmpegNotInPath("FFMPEG not found in the system PATH.")


FFPROBE_BIN = "ffprobe"
_ffprobe_path = shutil.which(FFPROBE_BIN)
if _ffprobe_path is None:
    raise FfmpegNotInPath("FFMPEG not found in the system PATH.")


class AudioFormat:


    class ByteFormat(Enum):
        SIGNED      = enum.auto()
        UNSIGNED    = enum.auto()
        FLOAT       = enum.auto()
        def to_string(self):
            str_map = {
                self.SIGNED:    "s",
                self.UNSIGNED:  "u",
                self.FLOAT:     "f"
            }
            return str_map[self]
        @classmethod
        def from_string(cls, str_in: str):
            str_map = {
                "s":  cls.SIGNED,
                "u":  cls.UNSIGNED,
                "f":  cls.FLOAT
            }
            return str_map.get(str_in, cls.SIGNED)


    class ByteOrder(Enum):
        UNSPECIFIED = enum.auto()
        LITTLE      = enum.auto()
        BIG         = enum.auto()
        def to_string(self):
            str_map = {
                self.UNSPECIFIED:   "",
                self.LITTLE:        "le",
                self.BIG:           "be"
            }
            return str_map[self]
        @classmethod
        def from_string(cls, str_in: str):
            str_map = {
                "le":  cls.LITTLE,
                "be":  cls.BIG
            }
            return str_map.get(str_in, cls.UNSPECIFIED)


    def __init__(
            self,
            byte_fmt: ByteFormat = ByteFormat.SIGNED,
            bits: int = 16,
            endianess: ByteOrder = ByteOrder.LITTLE
    ) -> None:
        self.byte_fmt = byte_fmt
        self.bits = bits 
        self.endianess = endianess


    @property
    def num_bytes(self):
        return int(self.bits / 8)


    def to_string(self):
        return "".join((
            self.byte_fmt.to_string(), 
            str(self.bits), 
            self.endianess.to_string())
        )


    # TODO: This won't work for UNSIGNED, add later
    def get_normalization_function(self)->Callable[[float], float]:
        scale_amnt = 2**(self.bits-1)

        def norm_func(x: float):
            return (x / scale_amnt)
        
        return norm_func


    def to_numpy_dtype_str(self)->str:
        fmt_map: Dict[Tuple[bool, 'AudioFormat.ByteFormat'], str] = {
            (True,  self.ByteFormat.UNSIGNED):  "B",
            (True,  self.ByteFormat.SIGNED):    "b",
            (False, self.ByteFormat.UNSIGNED):  "u",
            (False, self.ByteFormat.SIGNED):    "i",
        }
        endian_map = {
            self.ByteOrder.UNSPECIFIED: "",
            self.ByteOrder.BIG:         ">",
            self.ByteOrder.LITTLE:      "<"
        }

        if self.byte_fmt is self.ByteFormat.FLOAT:
            type_id = "f"
        else:
            type_id = fmt_map.get((self.bits <=8, self.byte_fmt), "i")
        
        endian_str = endian_map.get(self.endianess, "")
        num_bytes_str = str(self.num_bytes) if self.num_bytes > 1 else "" 

        return "".join((endian_str, type_id, num_bytes_str))
        

    _TYPE_STR_REGEX = re.compile(r"(?P<type>[fsu])(?P<bits>\d+)(?P<order>([bl]e)?)")

    @classmethod
    def from_string(cls, in_str):
        match = cls._TYPE_STR_REGEX.search(in_str)
        if match is None:
            return None
        byte_fmt_str, bits_str, endianess_str = tuple(match.groups())[0:3]

        bits        = int(bits_str)
        byte_fmt    = cls.ByteFormat.from_string(byte_fmt_str)
        endianess   = cls.ByteOrder.from_string(endianess_str)

        return cls(byte_fmt, bits, endianess)


def open_stream(
        src: str,
        buff_size: int = 10**8,
        codec: str = "pcm_s16le",
        sampling_rate: int = 44100,
        num_channels: int = 2,
        out_format: AudioFormat = None
)->sp.Popen:

    out_format = out_format or AudioFormat()
    command_str = [
        FFMPEG_BIN,
        "-i", src,
        "-f", out_format.to_string(),
        "-acodec", codec,
        "-ar", str(sampling_rate), 
        "-ac", str(num_channels),
        "-nostats",
        "-loglevel", "quiet",
        "-"
    ]
    pipe = sp.Popen(command_str, stdout=sp.PIPE, bufsize=buff_size)
    return pipe


def get_metadata(
        src: str
)->Dict[str, Any]:

    command_str = [
        FFPROBE_BIN,
        "-loglevel", "quiet",
        "-show_streams",
        "-of", "json",
        src
    ]
    result = json.loads(sp.check_output(command_str))
    return result


def copy_audio_segment(
        src: str,
        dst: str,
        start,
        end = None
):
    atrim_cmd = f"atrim=start_sample={start}"
    if end:
        atrim_cmd += f":end_sample={end}"
    command_str = [
        FFMPEG_BIN,
        "-y",
        "-loglevel", "quiet",
        "-i", src,
        "-af", atrim_cmd,
        dst
    ]
    sp.run(command_str, text=True, input="y\n")


__all__ = [
    "AudioFormat",
    "open_stream",
    "get_metadata",
    "copy_audio_segment"
]