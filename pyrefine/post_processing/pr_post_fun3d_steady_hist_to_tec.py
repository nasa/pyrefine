#!/usr/bin/env python
"""
A script to write the number of nodes and last line of hist data to tecplot for steady FUN3D adaptations
"""
import argparse
from pyrefine.post_processing.fun3d_file_reader import Fun3dAdaptationSteadyHistoryReader


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("project_rootname", help="Base name of files, e.g. `{project_rootname}01_hist.dat`")
    parser.add_argument("--dir", default="./Flow", help="Location of files")
    parser.add_argument("--num_meshes", default=-1, type=int, help="Number of meshes, default finds all")
    parser.add_argument("--output_file", default="adapt_hist.dat", help="Tecplot file name")
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()

    reader = Fun3dAdaptationSteadyHistoryReader(args.dir, args.project_rootname, number_of_meshes=args.num_meshes)
    reader.write_data_to_tec(args.output_file)


if __name__ == '__main__':
    main()
