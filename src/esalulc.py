"""
Extraction of the ESA World Cover.
https://esa-worldcover.org/en
"""

from sentinelhub import DataCollection, SentinelHubDownloadClient, MosaickingOrder
from pathlib import Path
from src import evalscripts
import rasterio
import numpy as np
from src.utils.gdal import gdal_merge
import time

from src.constants import NO_DATA_DISCRETE, RESOLUTION, CRS, ESA_LC_DEFAULT
from src.utils.sh_requests import create_image_request, get_bbox_list
from src.utils.interpolation import interpolate_tif


def download(bbox, time_interval, output, split_shape, rate_limit):

    evalscript = evalscripts.WORLDCOVER
    data_collection = DataCollection.define_byoc(collection_id="0b940c63-45dd-4e6b-8019-c3660b81b884")
    mosaicking_order = MosaickingOrder.MOST_RECENT

    # bounding box is split into grid of rows x columns bounding boxes
    bbox_list = get_bbox_list(
        bbox=bbox,
        crs=CRS,
        split_shape=split_shape
    )
    
    # create requests for each bounding box
    sh_requests = []
    for bbox in bbox_list:
        image_request = create_image_request(
            bbox=bbox, 
            resolution= RESOLUTION,
            time_interval=time_interval,
            data_collection=data_collection,
            evalscript=evalscript,
            mosaicking_order=mosaicking_order,
        )
        sh_requests.append(image_request)
    
    #dl_requests = [request.download_list[0] for request in sh_requests]
    #_ = SentinelHubDownloadClient(config=None).download(dl_requests, max_threads=5)

    for request in sh_requests:
        dl_request = request.download_list[0]
        _ = SentinelHubDownloadClient(config=None).download([dl_request], max_threads=1)
        time.sleep(rate_limit)  # Pause for the specified time delay

    data_folder = sh_requests[0].data_folder
    tiffs = [Path(data_folder) / req.get_filename_list()[0] for req in sh_requests]
    str_tiffs = [str(tiff) for tiff in tiffs]
    gdal_merge(str_tiffs, bbox, output=output, dstnodata=NO_DATA_DISCRETE)


def fix_tif(tif_path):

    with rasterio.open(tif_path, 'r') as file:
        bands = file.read()
        mask  = bands[-1,  :, :]
        bands = bands[:-1, :, :]
        profile = file.profile


    profile.update(count = bands.shape[0])
    with rasterio.open(tif_path, 'w', **profile) as file:
        bands = np.array(bands).transpose((1,2,0))

        bands[bands == 0] = NO_DATA_DISCRETE
        bands[bands == 10] = 0
        bands[bands == 20] = 1
        bands[bands == 30] = 2
        bands[bands == 40] = 3
        bands[bands == 50] = 4
        bands[bands == 60] = 5
        bands[bands == 70] = 6
        bands[bands == 80] = 7
        bands[bands == 90] = 8
        bands[bands == 95] = 9
        bands[bands == 100] = 10
        bands[mask==0] = NO_DATA_DISCRETE
        bands = np.array(bands).transpose((2,0,1))

        file.nodata = NO_DATA_DISCRETE
        file.write(bands)

    
def mosaic(
    bbox, 
    start, 
    end, 
    output, 
    max_retry, 
    split_shape, 
    rate_limit
):

    #sh_retry(
    #    max_retry, 
    #    download, 
    #    bbox = bbox, 
    #    time_interval=(start, end), 
    #    output = output, 
    #    split_shape = split_shape, 
    #    rate_limit=rate_limit
    #)
    
    download(
        bbox = bbox, 
        time_interval=(start, end), 
        output = output, 
        split_shape = split_shape, 
        rate_limit=rate_limit
    )

    fix_tif(output)

    interpolate_tif(output, default=ESA_LC_DEFAULT)
