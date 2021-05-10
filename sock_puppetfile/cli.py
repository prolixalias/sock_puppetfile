"""Console script for sock_puppetfile."""
import argparse
import logging
import sys

from .sock_puppetfile import SockPuppetfile
from .spinner import Spinner

diff = False

def main():
    # """Console script for sock_puppetfile."""

    parser = argparse.ArgumentParser(description='Check latest version of forge modules in Puppetfile')
    parser.add_argument('path', type=str, help='absolute or relative')
    parser.add_argument('-d', '--diff',
        action='store_true',
        dest='diff',
        default=False,
        help='add diff to end of result',
    )
    parser.add_argument('-v', '--verbose',
        action='store_const',
        dest='loglevel',
        const=logging.DEBUG,
        default=logging.WARNING,
        help='enable verbose output',
    )

    args = parser.parse_args()

    logging.basicConfig(stream=sys.stderr, level=args.loglevel)

    work = SockPuppetfile(args.path)
    logging.info(f"input file {work.puppetfile}")

    input_hash = work.get_input_hash()
    logging.info(f"input hash {input_hash}")

    with Spinner(" "):
        output_hash = work.get_output_hash()
        logging.info(f"output hash {output_hash}")

    original_puppetfile_contents = work.get_puppetfile_contents()
    logging.info(f"original puppetfile contents {original_puppetfile_contents}")

    new_puppetfile_contents = work.generate_new_puppetfile()
    logging.info(f"new puppetfile contents {new_puppetfile_contents}")
    print(*new_puppetfile_contents, end='')

    if args.diff == True:
        diff_result = work.compare_puppetfiles()
        logging.info(f"diff result {diff_result}")
        print('\n### generated diff:')
        for line in diff_result:
            print(f"#   {line}", end='')

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
