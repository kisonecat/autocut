#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages(ps: [ps.numpy ps.librosa])"

import xml.etree.ElementTree as ET
from autocut.melt import movie2xml
import argparse
from autocut.parse import parse_input

def main():
    parser = argparse.ArgumentParser(description='autocut some video')
    parser.add_argument('input', default='input.xml', nargs='?')
    parser.add_argument('output', default='editlist.xml', nargs='?')

    args = parser.parse_args()
    movie = parse_input(args.input)

    # TODO: pretty print movie!
    print(movie)

    tree = movie2xml(movie)
    tree.write(args.output)
