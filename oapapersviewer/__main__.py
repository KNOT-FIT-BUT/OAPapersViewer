# -*- coding: UTF-8 -*-
"""
Created on 24.04.24
Module for OAPapers TUI viewer.

:author:     Martin Dočekal
"""
from argparse import ArgumentParser
from contextlib import nullcontext

from oapapersloader import OADataset, OARelatedWork

from oapapersviewer.viewer import Viewer


def main():

    parser = ArgumentParser(description="TUI viewer for OAPapers corpus and derived datasets.")
    parser.add_argument("dataset", help="Path to dataset file", type=str)
    parser.add_argument("-r", "--references",
                        help="Are cited documents using separate file? Use this argument to specify path to them.",
                        type=str)
    parser.add_argument("-rw", "--related_work",
                        help="The dataset uses related work format.",
                        action="store_true")
    args = parser.parse_args()

    if args is not None:
        dataset = OARelatedWork(args.dataset, args.dataset + ".index") if args.related_work \
            else OADataset(args.dataset, args.dataset + ".index")

        references = OADataset(args.references, args.references + ".index") if args.references else nullcontext()

        with dataset, references:
            Viewer.run(title="OAPapers", dataset=dataset, references_dataset=references if args.references else None)
    else:
        exit(1)


if __name__ == '__main__':
    main()
