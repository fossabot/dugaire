#!/usr/bin/env python3

""" Import comunity modules. """

import os
import sys
from click.testing import CliRunner

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, f"{HERE}/../dugaire")

""" Import custom modules. """

import dugaire
import setup_info

def test_help():
    
    cmd = ""
    cmd += "--help"

    result = CliRunner().invoke(dugaire.cli, cmd.split(" "))
    output = result.output.strip()

    assert f'Usage: cli [OPTIONS] COMMAND [ARGS]' in output

def test_version():

    cmd = ""
    cmd += "--version"

    result = CliRunner().invoke(dugaire.cli, cmd.split(" "))
    output = result.output.strip()

    setup_info_version = setup_info.get_version()
    setup_info_prog_name = setup_info.get_prog_name()

    assert f'{setup_info_prog_name}, version {setup_info_version}' == output

def test_build():
    cmd = ""
    cmd += "build -apt=curl,nano"

    result = CliRunner().invoke(dugaire.cli, cmd.split(" "))
    output = result.output.strip()

    assert 'sha256:' in output