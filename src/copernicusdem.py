"""
Extraction of the Copernicus DEM.
https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model
"""

from sentinelhub import DataCollection, SentinelHubDownloadClient, MosaickingOrder
from pathlib import Path
from src import evalscripts
import rasterio
import numpy as np
from src.utils.gdal import gdal_merge
import time

from src.constants import NO_DATA_CONTINUOUS, RESOLUTION, CRS, DEM_DEFAULT
from src.utils.sh_requests import create_image_request, get_bbox_list
from src.utils.interpolation import interpolate_tif

def download(bbox, time_interval, output_path, split_shape, rate_limit):

    evalscript = evalscripts.DEM_COPERNICUS_30
    data_collection = DataCollection.DEM_COPERNICUS_30
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
    tifs = [Path(data_folder) / req.get_filename_list()[0] for req in sh_requests]
    str_tifs = [str(tif) for tif in tifs]
    gdal_merge(str_tifs, bbox, output=output_path, dstnodata=NO_DATA_CONTINUOUS)


def fix_tif(tif_path):

    with rasterio.open(tif_path, 'r') as file:
        bands = file.read()
        mask  = bands[-1,  :, :]
        bands = bands[:-1, :, :]
        profile = file.profile

    profile.update(count = bands.shape[0])
    with rasterio.open(tif_path, 'w', **profile) as file:

        bands = np.array(bands).transpose((1,2,0))
        bands[mask==0] = NO_DATA_CONTINUOUS
        bands = np.array(bands).transpose((2,0,1))

        file.nodata = NO_DATA_CONTINUOUS
        file.write(bands)


def mosaic(
    bbox,
    start,
    end,
    output_path,
    max_retry,
    split_shape,
    rate_limit
):
   
    download(
        bbox = bbox,
        time_interval=(start, end),
        output_path = output_path,
        split_shape = split_shape,
        rate_limit=rate_limit
    )

    fix_tif(output_path)

    interpolate_tif(output_path, default=DEM_DEFAULT)

