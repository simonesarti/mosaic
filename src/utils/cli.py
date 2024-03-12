from argparse import ArgumentParser
from datetime import datetime
import re
from pathlib import Path
from src.constants import STATIC_IMAGES, TEMPORAL_IMAGES


def print_and_exit(string:str, exit_code:int=1):
    print(string)
    exit(exit_code)


def get_cli_arguments():

    args = parse_cli_arguments()
    args = check_cli_arguments(args)
    args = format_cli_arguments(args)
    return args


def parse_cli_arguments():

    parser = ArgumentParser()
    parser.add_argument("--image", type=str, choices=STATIC_IMAGES+TEMPORAL_IMAGES, default=STATIC_IMAGES[0], help="the image type to extract")
    parser.add_argument("--output_path", type=str, default="./mosaic.tif", help="output path")
    parser.add_argument("--min_long", type=float, default=46.00, help="minimum value for longitude used to create the bounding box")
    parser.add_argument("--min_lat", type=float, default=-16.15, help="minimum value for latitude used to create the bounding box")
    parser.add_argument("--max_long", type=float, default=46.05, help="maximum value for longitude used to create the bounding box")
    parser.add_argument("--max_lat", type=float, default=-16.01, help="maximum value for latitude used to create the bounding box")
    parser.add_argument("--start_date", type=str, default="2020/10/5", help="start date, in format year/month/day")
    parser.add_argument("--end_date", type=str, default="2021/12/7", help="end date, in format year/month/day")
    parser.add_argument("--split_rows", type=int, default=10, help="bounding box splits in n rows")
    parser.add_argument("--split_columns", type=int, default=10, help="bounding box splits in n columns")
    parser.add_argument("--num_periods", type=int, default=3, help="number of periods to use, when time is relevant")
    parser.add_argument("--max_retry", type=int, default=10, help="maximimun number of requests for the same images")
    parser.add_argument("--rate_limit", type=int, default=300, help="max requests per minute")

    args = parser.parse_args()
    return args


def check_cli_arguments(args):

    # check output path
    args.output_path = Path(args.output_path)
    if not args.output_path.suffix == ".tif":
        print_and_exit(f"Output path must have a .tif extension. Got {args.output_path}")


    # check coordinates values
    if not (-180.0 <= args.min_long < 180.0):
        print_and_exit(f"Value for 'min_long' must be in [-180, 180). Got {args.min_long}")
    if not (-180.0 < args.max_long <= 180.0):
        print_and_exit(f"Value for 'max_long' must be in (-180, 180]. Got {args.max_long}")
    if not (-90.0 <= args.min_lat < 90.0):
        print_and_exit(f"Value for 'min_lat' must be in [-90, 90). Got {args.min_lat}")
    if not (-90.0 < args.max_lat <= 90.0):
        print_and_exit(f"Value for 'max_lat' must be in (-90, 90]. Got {args.max_lat}")

    # check coordinates order
    if args.min_long >= args.max_long:
        print_and_exit(f"Value for 'min_long' must be lower than 'max_long'. Got {args.min_long} and {args.max_long} respectively")
    if args.min_lat >= args.max_lat:
        print_and_exit(f"Value for 'min_lat' must be lower than 'max_lat'. Got {args.min_lat} and {args.max_lat} respectively")

    # ceck dates
    pattern = r'^\d{4}/\d{2}/\d{2}$'
    if not re.match(pattern, args.start_date):
        print_and_exit(f"Value for 'start_date' must be in the form 'yyyy/mm/dd'. Got {args.start_date}")
    if not re.match(pattern, args.end_date):
        print_and_exit(f"Value for 'end_date' must be in the form 'yyyy/mm/dd'. Got {args.end_date}")

    try:
        args.start_date = datetime.strptime(args.start_date, '%Y/%m/%d')
    except ValueError:
        print_and_exit(f"Value for 'start_date' is and invalid date. Got {args.start_date}")

    try:
        args.end_date = datetime.strptime(args.end_date, '%Y/%m/%d')
    except ValueError:
        print_and_exit(f"Value for 'end_date' is and invalid date. Got {args.end_date}")

    if not args.start_date < args.end_date:
        print_and_exit(f"Value for 'start_date' must be lower than 'end_date'. Got {args.start_date} and {args.end_date} respectively")


    # check positive splitting values
    if not args.split_rows >= 1:
        print_and_exit(f"Value for 'split_rows' must be positive. Got {args.split_rows}")
    if not args.split_columns >= 1:
        print_and_exit(f"Value for 'split_columns' must be positive. Got {args.split_columns}")
    if not args.num_periods >= 1:
        print_and_exit(f"Value for 'num_periods' must be positive. Got {args.num_periods}")

    # check positive rates
    if not args.max_retry >= 1:
        print_and_exit(f"Value for 'max_retry' must be positive. Got {args.max_retry}")
    if not args.rate_limit >= 1:
        print_and_exit(f"Value for 'rate_limit' must be positive. Got {args.rate_limit}")

    return args


def format_cli_arguments(args):
   
    mosaic_parameters = {
        "output_path": args.output_path,
        "bbox": (args.min_long, args.min_lat, args.max_long, args.max_lat),
        "time_interval": (args.start_date, args.end_date),
        "split_shape": (args.split_rows, args.split_columns),
        "rate_limit": 60 / (args.rate_limit * 0.95),
        "max_retry": args.max_retry,
    }

    if args.image in TEMPORAL_IMAGES:
        mosaic_parameters["num_periods"]= args.num_periods

    return args.image, mosaic_parameters