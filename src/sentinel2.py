"""
Extraction of the Sentinel-2.
https://sentinel.esa.int/web/sentinel/missions/sentinel-2
"""


from sentinelhub import DataCollection, SentinelHubDownloadClient, MosaickingOrder
from pathlib import Path
from src import evalscripts
from s2cloudless import S2PixelCloudDetector
import rasterio
import numpy as np
import shutil
import os
from src.utils import sh_retry, gdal_merge, split_interval
import time

from src.constants import NO_DATA_CONTINUOUS, RESOLUTION, CRS, S2_DEFAULT
from src.utils.sh_requests import create_image_request, get_bbox_list
from src.utils.interpolation import interpolate_tif


def download(bbox, time_interval, output, split_shape, rate_limit):

    evalscript = evalscripts.SENTINEL2
    data_collection = DataCollection.SENTINEL2_L1C
    mosaicking_order = MosaickingOrder.LEAST_CC

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

    gdal_merge(str_tifs, bbox, output=output, dstnodata=NO_DATA_CONTINUOUS)


def mosaic(bbox, start, end, output, n, max_retry = 10, split_shape=(10, 10), mask_clouds = True, rate_limit=1):

    slots = split_interval(start, end, n)
    cloud_detector = S2PixelCloudDetector(threshold=None, average_over=0, dilation_size=0, all_bands=True)
   
    merged_mask = None
    merged_bands = None

    files = []
    for slot in slots:
        print(slot)
        image = './image_{start}_{end}.tif'.format(start = slot[0], end = slot[1])
       
        sh_retry(max_retry, download, bbox = bbox, time_interval = slot, output = image, split_shape=split_shape, rate_limit=rate_limit)

        with rasterio.open(image, 'r') as file:
            bands = file.read()
            mask  = bands[-1,  :, :]
            bands = bands[:-1, :, :]
            profile = file.profile

        profile.update(count = bands.shape[0])
        with rasterio.open(image, 'w', **profile) as file:
            bands = np.array(bands).transpose((1,2,0))
            if mask_clouds:
                tmp = bands.copy()
                tmp[tmp==NO_DATA_CONTINUOUS] = 0
                tmp = tmp.astype(np.float32)/10000.0
                cloud_prob = cloud_detector.get_cloud_probability_maps(tmp[np.newaxis, ...])[0, :, :]
                bands[cloud_prob > 0.4] = NO_DATA_CONTINUOUS

            bands[mask==0] = NO_DATA_CONTINUOUS
            bands = np.array(bands).transpose((2,0,1))
            file.nodata = NO_DATA_CONTINUOUS
            file.write(bands)
       
        bands = bands.astype(np.float32)
        bands[bands==NO_DATA_CONTINUOUS] = np.nan
        mask = np.ones_like(bands)
        mask[np.isnan(bands)] = 0
        bands[np.isnan(bands)] = 0
        bands = bands.astype(np.int16)

        if(merged_mask is None):
            merged_mask = mask
            merged_bands = bands
        else:
            merged_mask = merged_mask + mask
            merged_bands = merged_bands + bands
       
        files.append(image)
        if(len(files)<len(slots)):
            os.remove(image)

   
    merged_bands = merged_bands.astype(np.float32)   
    merged_mask[merged_mask==0] = np.nan
    merged_bands = merged_bands/merged_mask
    merged_bands[np.isnan(merged_bands)] = NO_DATA_CONTINUOUS
    merged_bands = merged_bands.astype(np.int16)

    shutil.copyfile(files[-1], output)
    with rasterio.open(output, 'r+') as file:
        file.write(merged_bands)
    os.remove(files[-1])