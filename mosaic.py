
from argparse import ArgumentParser
import datetime
import shutil
from src.utils.sh_credentials import set_SH_credentials

import src.sentinel1
import src.sentinel2
import src.esalulc
import src.dwlulc
import src.copernicusdem

def parse_arguments():

    parser = ArgumentParser()
    parser.add_argument("--image", type=str, choices=["sentinel1","sentinel2", "esalulc", "dwlulc", "copernicusdem"], default="copernicusdem", help="the image type to extract")
    parser.add_argument("--minlong", type=float, default=46.00, help="minimum value for longitude used to create the bounding box")
    parser.add_argument("--minlat", type=float, default=-16.15, help="minimum value for latitude used to create the bounding box")
    parser.add_argument("--maxlong", type=float, default=46.05, help="maximum value for longitude used to create the bounding box")
    parser.add_argument("--maxlat", type=float, default=-16.01, help="maximum value for latitude used to create the bounding box")
    parser.add_argument("--start", type=str, default="2020/10/5", help="start date, in format year/month/day")
    parser.add_argument("--end", type=str, default="2021/12/7", help="end date, in format year/month/day")
    parser.add_argument("--split_rows", type=int, default=10, help="bounding box splits in n rows")
    parser.add_argument("--split_columns", type=int, default=10, help="bounding box splits in n columns")
    parser.add_argument("--max_retry", type=int, default=10, help="maximimun number of requests for the same images")
    parser.add_argument("--output", type=str, default="./mosaic.tiff", help="output path")
    parser.add_argument("--n", type=int, default=3, help="number of periods to use, when time is relevant")
    parser.add_argument("--rate_limit", type=int, default=300, help="max requests per minute")

    args = parser.parse_args()
    
    args.bbox = (args.minlong, args.minlat, args.maxlong, args.maxlat)
    args.split_shape = (args.split_rows, args.split_columns)

    args.start = args.start.split("/")
    args.start = datetime.datetime(int(args.start[0]), int(args.start[1]), int(args.start[2]))
    args.end =  args.end.split("/")
    args.end = datetime.datetime(int(args.end[0]), int(args.end[1]), int(args.end[2]))

    args.rate_limit = args.rate_limit*0.95
    args.rate_limit = 60/args.rate_limit

    del args.minlong
    del args.minlat
    del args.maxlong
    del args.maxlat
    del args.split_rows
    del args.split_columns
    
    args = vars(args)
    return(args)


def main(args):
    
    set_SH_credentials()

    args = parse_arguments()

    if args['image'] in ["esalulc", "copernicusdem"]:
        args.pop("n")    # not temporal

    if args['image'] == "sentinel1":
        from src.sentinel1 import mosaic
    if args['image'] == "sentinel2":
        from src.sentinel2 import mosaic
    if args['image'] == "dwlulc":
        from src.dwlulc import mosaic
    if args['image'] == "esalulc":
        from src.esalulc import mosaic
    if args['image'] == "copernicusdem":
        from src.copernicusdem import mosaic

    args.pop("image")
    mosaic(**args)
    shutil.rmtree("./test_dir")



if __name__ == "__main__":
    main()

