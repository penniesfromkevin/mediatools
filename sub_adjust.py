#!/usr/bin/env python
"""Adjusts timing and section numbering of SRT and SMI subtitle files.
"""
import argparse
import os
import re
import sys


SMI_PATTERN = '<SYNC Start=(\d+)>'
SMI_TEMPLATE = '<SYNC Start={}>\r\n'
SRT_PATTERN = (r'(\d{2}):(\d{2}):(\d{2}),(\d{3})')
SRT_TEMPLATE = '{:0>2}:{:0>2}:{:0>2},{:0>3}'


def add_time(hours, minutes, seconds, millis, milli_offset):
    """Adds offset, in milliseconds, to the given timestamp.

    Args:
        hours: Integer hours.
        minutes: Integer minutes.
        seconds: Integer seconds.
        millis: Integer milliseconds
        milli_offset: Offset in milliseconds; can be negative.

    Returns:
        String formatted with a TIME_TEMPLATE.
    """
    millis += ((hours * 3600000) + (minutes * 60000) + (seconds * 1000)
               + milli_offset)
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    seconds, millis = divmod(millis, 1000)
    result = SRT_TEMPLATE.format(hours, minutes, seconds, millis)
    return result


def process_smi(contents, time_offset=0):
    """Process contents line-by-line.

    Args:
        contents: Contents as list of lines
        time_offset: Time in milliseconds to be added to time ranges.

    Returns:
        New contents list of lines.
    """
    time_prog = re.compile(SMI_PATTERN)
    modified = []
    for line in contents:
        result = time_prog.match(line)
        if result:
            ms_s = int(result.group(1))
            new_time = ms_s + time_offset
            line = SMI_TEMPLATE.format(new_time)
        modified.append(line)
    return modified


def process_srt(contents, section_offset=0, time_offset=0):
    """Process contents line-by-line.

    Args:
        contents: Contents as list of lines
        section_offset: Value to be added to section number.
        time_offset: Time in milliseconds to be added to time ranges.

    Returns:
        New contents list of lines.
    """
    time_prog = re.compile('{pat} --> {pat}'.format(pat=SRT_PATTERN))
    section_previous = None
    modified = []
    for line in contents:
        result = time_prog.match(line)
        if result:
            h_s = int(result.group(1))
            m_s = int(result.group(2))
            s_s = int(result.group(3))
            ms_s = int(result.group(4))
            h_e = int(result.group(5))
            m_e = int(result.group(6))
            s_e = int(result.group(7))
            ms_e = int(result.group(8))
            new_start = add_time(h_s, m_s, s_s, ms_s, time_offset)
            new_end = add_time(h_e, m_e, s_e, ms_e, time_offset)
            line = '{} --> {}\r\n'.format(new_start, new_end)
        elif line.strip().isdigit():
            section_number = int(line)
            section_number += section_offset
            if section_previous and section_number != section_previous + 1:
                section_number = section_previous + 1
            section_previous = section_number
            line = '%s\r\n' % section_number
        modified.append(line)
    return modified


def read_file(file_path):
    """Read file as list of lines.

     Args:
        file_path: Path to file to read.

    Returns:
        Contents of file as list of lines.
    """
    with open(file_path, 'r') as f_handle:
        contents = f_handle.readlines()
    return contents


def write_file(contents, file_path):
    """Save contents to a file.

    """
    with open(file_path, 'w') as f_handle:
        f_handle.writelines(contents)


def parse_args():
    """Parse command line arguments.

    Returns:
        Argments object.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Subtitle timing adjustment.')
    parser.add_argument(
        '-i', '--input_file', required=True,
        help='Path to initial subtitle file.')
    parser.add_argument(
        '-o', '--output_file',
        help='Desired name of output subtitle file.')
    parser.add_argument(
        '-t', '--millis', type=int, default=0,
        help='Synchronization time adjustment, in milliseconds.')
    parser.add_argument(
        '-s', '--section', type=int, default=0,
        help='Section number adjustment.')
    args = parser.parse_args()
    return args


def main():
    """Does the work.
    """
    contents = read_file(ARGS.input_file)
    filename, extension = os.path.splitext(ARGS.input_file)
    if extension.lower() == '.smi':
        contents = process_smi(contents, ARGS.millis)
    else:
        contents = process_srt(contents, ARGS.section, ARGS.millis)
    if not ARGS.output_file:
        output_file = '%s.adjust%s' % (filename, extension)
    else:
        output_file = ARGS.output_file
    write_file(contents, output_file)


if __name__ == '__main__':
    ARGS = parse_args()
    sys.exit(main())
