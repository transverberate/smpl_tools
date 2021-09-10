import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from typing import Any, Dict, List
import numpy as np

from . import ffmpeg
from .ffmpeg import AudioFormat


class AudioStream:


    def __init__(
            self,
            src: str,
            sample_rate: int = 44100,
            num_channels: int = 1,
            out_format: AudioFormat = None, 
            codec: str = "pcm_s16le",
            buffer_duration: float = 1
    ) -> None:
        metadata = ffmpeg.get_metadata(src)
        self._parse_metadata(metadata)
        self.sample_rate = sample_rate or self.sample_rate
        self.num_channels = num_channels or num_channels
        self._pipe = ffmpeg.open_stream(
            src, 
            codec=codec,
            sampling_rate=self.sample_rate, 
            num_channels=num_channels,
            out_format=out_format
        )
        self.sample_fmt = out_format or AudioFormat()
        self.buffer_duration = buffer_duration
    

    @property
    def buffer_duration(self):
        return self._buffer_duration


    @buffer_duration.setter
    def buffer_duration(self, buffer_duration):
        self._buffer_duration   = buffer_duration
        self._buffer_ts         = int(np.ceil(buffer_duration * self.sample_rate))
        self._buffer_size       = self._buffer_ts * self.sample_fmt.num_bytes


    @property
    def buffer_ts(self):
        return self._buffer_ts

    @property
    def buffer_size(self):
        return self._buffer_size


    def _parse_metadata(self, metadata: Dict[str, Any]):
        streams_data = metadata.get("streams", [{}])
        primary_data = {} if len(streams_data) < 1 else streams_data[0]

        self.sample_rate        = int(primary_data.get("sample_rate", 44100))
        self.bits_per_sample    = int(primary_data.get("bits_per_smaple", 16))
        self.duration_ts        = int(primary_data.get("duration_ts", 0))
        self.num_channels       = int(primary_data.get("channels", 2))
        
        smaple_fmt_raw          = primary_data.get("sample_fmt", "s16le")
        self.in_sample_fmt      = AudioFormat.from_string(smaple_fmt_raw)


    def _get_next(self)->np.ndarray:
        if not self._pipe or not self._pipe.stdout:
            raise StopIteration
        
        raw_data = self._pipe.stdout.read(self._buffer_size)
        if not raw_data:
            raise StopIteration
        
        arr_data = np.frombuffer(
            raw_data, 
            dtype = self.sample_fmt.to_numpy_dtype_str()
        )
        
        return arr_data


    def __next__(self):
        return self._get_next()


    def __iter__(self):
        return self


def split_by_silence_ts(
        stream: AudioStream,
        min_duration: float = 1,
        db_cuttoff: float = -60,
        offset_correction: float = 0
):
    
    f_scale = stream.sample_fmt.get_normalization_function() 
    cuttoff_level = 10**(db_cuttoff/20) / f_scale(1) # dividing by the scale early wont work for unsigned streams

    stream.buffer_duration = min_duration
    chunk_size = stream.buffer_ts
    chunk_half_size = int(np.ceil(chunk_size / 2))
    offset_correction_samples = int(np.ceil(offset_correction * stream.sample_rate))

    def chunks_contain_silence(chunk_current, chunk_previous):
        # divide chunk into 4 partitions
        partitions = []
        if chunk_half_size < chunk_previous.size:
            partitions.append(chunk_previous[:chunk_half_size-1])
            partitions.append(chunk_previous[chunk_half_size:])
        if chunk_half_size < chunk_current.size:
            partitions.append(chunk_current[:chunk_half_size-1])
            partitions.append(chunk_current[chunk_half_size:])
        if len(partitions) > 0:
            predicate = list(map(lambda x: np.max(x) < cuttoff_level, partitions))
            return any(predicate)
        return True

    offset_to_base = 0
    carry_flag = True
    
    slices: List[int] = list()

    # read first chunk
    chunk_previous = np.abs(next(stream))    

    # determine first slice
    if chunk_previous.size > 0 and chunk_previous[0] >= cuttoff_level:
        slices.append(0)

    # process chunks
    for chunk_raw in stream:
        chunk_current = np.abs(chunk_raw)
        # chunk has sufficient silence or is part of a caryover 
        if chunks_contain_silence(chunk_previous, chunk_current) or carry_flag:
            chunk_full = np.concatenate([chunk_previous, chunk_current])
            chunk_pred = np.less(chunk_full, cuttoff_level).view(np.int8)
            chunk_diff = np.diff(chunk_pred)

            # find edges
            edge_indices = np.where(np.abs(chunk_diff) == 1)[0]
            if edge_indices.size > 0:

                new_slices = []

                # is first edge a falling edge?
                if chunk_diff[edge_indices[0]] < 0: 
                    # was this part of a carryover?
                    if carry_flag:
                        new_slices.append(int(edge_indices[0]))
                        carry_flag = False
                    # remove initial falling edge
                    edge_indices = edge_indices[1:]
                
                carrying_override = False
                # is the final edge a rising edge?
                if (int(edge_indices.size) % 2) == 1: 
                    # final rising edge was on the left
                    # half of the chunk, therefore
                    # sufficient silence has been detected
                    if edge_indices[-1] < chunk_size:
                        # initiate caryover
                        carrying_override = True
                        carry_flag = True
                    # remove the final rising edge
                    edge_indices = edge_indices[0:-1]

                n = int(edge_indices.size / 2) # number of rising/falling edge pairs
                edge_indices = edge_indices.reshape((2, n), order='F')
                pulse_widths = np.diff(edge_indices, axis=0).reshape(n) # widths of each pulse
                valid_pulses = np.greater(pulse_widths, chunk_size).view(np.int8)

                num_valid_pulses = np.sum(valid_pulses)
                if num_valid_pulses > 0:
                    # reset the caryflag if override not set
                    if not carrying_override:
                        carry_flag = False

                    new_slices += [int(edge_indices[1][i]) for i in range(valid_pulses.size) if valid_pulses[i]]

                if len(new_slices) > 0:
                    np_new_slices = np.asarray(new_slices) + 1 + offset_to_base - offset_correction_samples
                    np_new_slices[np_new_slices < 0] = 0
                    np_new_slices = np.unique(np_new_slices)
                    slices += np_new_slices.tolist()
                
        offset_to_base += chunk_size
        chunk_previous = chunk_current

    return slices


__all__ = [ 
    "AudioStream",
    "split_by_silence_ts"
]