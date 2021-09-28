import os, sys
from smpl_tools.actions import split_file_by_silence_batch
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from typing import List, Union
from argparse import ArgumentParser

from .actions import split_file_by_silence
PACKAGE_NAME = "smpl_tools"


class IncorrectInputParameter(Exception):
    pass


def split_by_silence_cmd(argv: List[str]):


    def parse_as_negative_float(str_in: str)->float:
        result = float(str_in)
        result = -abs(result)
        return result


    def parse_file_string(str_in: str)->str:
        if not os.path.exists(str_in):
            raise FileNotFoundError(f"Could not find {str_in}.")
        return str_in


    arg_parser = ArgumentParser(
        add_help=True, 
        prog=f"{PACKAGE_NAME} split_by_silence"
    )
    arg_parser.add_argument(
        "source",
        metavar = "SOURCE_FILE",          
        type = parse_file_string
    )
    arg_parser.add_argument(
        "-s",
        "--silence_t",
        metavar = "SILENCE_DURATION",
        help = "Minimum duration of silence (in seconds) to trigger a slice.",
        type = float,   
        default = 0.4
    )
    arg_parser.add_argument(
        "-c",
        "--cutoff",
        metavar = "CUTOFF_DB", 
        help = ("Cutoff (in decibels) for which parts of "
                "the signal are considered silence. Default is -60."),
        type = parse_as_negative_float,
        default = -60
    )
    arg_parser.add_argument(
        "-o",
        "--offset",
        metavar = "OFFSET_CORRECTION",
        help = ("Number of time samples before of the onset of sound to "
                "include in the exported subsignals. \n Only needed when "
                "CUTOFF_DB is \"high\". Default is 0."),
        type = int,     
        default = 0
    )
    arg_parser.add_argument(
        "-b",
        "--batch",
        metavar = "JSON_BATCHJOB",
        help = ("A json file containing a list of track entries"
                "and the associated parameters for processing that track"
                "(e.g., sample_names, silence_duration, amplitude)."),
        type = parse_file_string,
        default = None
    )
    arg_parser.add_argument(
        "-d",
        "--destination",
        type = str,     
        default = None, 
        nargs = "*"
    )
    arg_parser.add_argument(
        "-p",
        "--pattern",
        metavar = "NAMING PATTERN",
        type = str,     
        default = None
    )
    args_namespace = arg_parser.parse_known_args(argv)[0]

    destination: Union[None, List[str], str] = args_namespace.destination
    if destination is not None and not isinstance(destination, str) and len(destination) == 1:
        destination = destination[0]

    if args_namespace.batch is not None:
        if destination is None:
            if os.path.isdir(args_namespace.source):
                destination = args_namespace.source
            else:
                destination = os.path.dirname(args_namespace.source)
                
        if not isinstance(destination, str):
            raise IncorrectInputParameter(
                "Parameter --destination must be a single directory when running a batchjob"
            )
        split_file_by_silence_batch( 
            args_namespace.batch,
            args_namespace.source,
            destination,
            args_namespace.pattern
        )
    else:
        split_file_by_silence(
            args_namespace.source,
            destination         =   destination,
            min_duration        =   args_namespace.silence_t,
            db_cutoff           =   args_namespace.cutoff,
            offset_correction   =   args_namespace.offset,
        )


def show_help_cmd(arg_parser: ArgumentParser, argv):
    arg_parser.print_help()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    arg_parser = ArgumentParser(
        add_help=False,
        prog=PACKAGE_NAME    
    )
    arg_parser.add_argument("command", default="", nargs="?")
    args_namespace, unparsed_args = arg_parser.parse_known_args(argv)

    cmd_funcs = {
        "split_by_silence": split_by_silence_cmd,
        "help": lambda x: show_help_cmd(arg_parser, x)
    }

    cmd_func = cmd_funcs.get(
        args_namespace.command,
         lambda x: show_help_cmd(arg_parser, x)
    )
    return cmd_func(unparsed_args)


if __name__ == "__main__":
    argv = sys.argv[1:]
    main(argv)
    sys.exit(0)
