"""
Extraction of the Sentinel-2.
https://sentinel.esa.int/web/sentinel/missions/sentinel-2
"""


from sentinelhub import SHConfig, CRS, BBox, MimeType, SentinelHubRequest, DataCollection, bbox_to_dimensions, BBoxSplitter, SentinelHubDownloadClient, MosaickingOrder
import sentinelhub
from pathlib import Path
from mosaic import evalscripts
from mosaic import clouddetection
import rasterio
import numpy as np
import shutil
import os
from mosaic.utils import shretry, gdal_merge, split_interval
import time

NO_DATA = -9999
RESOLUTION = 10
CRS = sentinelhub.CRS.WGS84


def download(bbox, time_interval, output, split_shape=(10, 10), rate_limit=1):

    def get_image(bbox, resolution):
        size = bbox_to_dimensions(bbox, resolution=resolution)
        request = SentinelHubRequest(
            data_folder="test_dir",
            evalscript=evalscripts.SENTINEL2,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L1C,
                    time_interval=time_interval,
                    mosaicking_order=MosaickingOrder.LEAST_CC
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
            bbox=bbox,
            size=size,
            config=None,
        )
        return(request)

    bbox_splitter = BBoxSplitter(
        [ BBox(bbox, crs=CRS) ], crs = CRS, split_shape = split_shape
    )  # bounding box will be split into grid of row x columns bounding boxes

    bbox_list = bbox_splitter.get_bbox_list()
    sh_requests = [get_image(bbox, RESOLUTION) for bbox in bbox_list]
    
    #dl_requests = [request.download_list[0] for request in sh_requests]
    #_ = SentinelHubDownloadClient(config=None).download(dl_requests, max_threads=5)

    for request in sh_requests:
        dl_request = request.download_list[0]
        _ = SentinelHubDownloadClient(config=None).download([dl_request], max_threads=1)
        time.sleep(rate_limit)  # Pause for the specified time delay

    data_folder = sh_requests[0].data_folder
    tiffs = [Path(data_folder) / req.get_filename_list()[0] for req in sh_requests]
    str_tiffs = [str(tiff) for tiff in tiffs]

    gdal_merge(str_tiffs, bbox, output=output, dstnodata=NO_DATA)
    for str_tiff in str_tiffs:
        os.remove(str_tiff)


def mosaic(bbox, start, end, output, n, max_retry = 10, split_shape=(10, 10), mask_clouds = True, rate_limit=1):

    slots = split_interval(start, end, n)
    model = clouddetection.Inference(all_bands=True)
    
    merged_mask = None
    merged_bands = None

    files = []
    for slot in slots:
        print(slot)
        image = './image_{start}_{end}.tiff'.format(start = slot[0], end = slot[1])
        
        shretry(max_retry, download, bbox = bbox, time_interval = slot, output = image, split_shape=split_shape, rate_limit=rate_limit)

        with rasterio.open(image, 'r') as file:
            bands = file.read()
            mask  = bands[-1,  :, :]
            bands = bands[:-1, :, :]
            profile = file.profile

        profile.update(count = bands.shape[0])
        with rasterio.open(image, 'w', **profile) as file:
            bands = np.array(bands).transpose((1,2,0))
            if(mask_clouds==True):
                tmp = bands.copy()
                tmp[tmp==NO_DATA] = 0
                tmp = tmp.astype(np.float32)/10000.0
                cloud_prob = model.predict(tmp[np.newaxis, ...])[0, :, :]
                bands[cloud_prob > 0.4] = NO_DATA

            bands[mask==0] = NO_DATA
            bands = np.array(bands).transpose((2,0,1))
            file.nodata = NO_DATA
            file.write(bands)
        
        bands = bands.astype(np.float32)
        bands[bands==NO_DATA] = np.nan
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
    merged_bands[np.isnan(merged_bands)] = NO_DATA
    merged_bands = merged_bands.astype(np.int16)

    shutil.copyfile(files[-1], output)
    with rasterio.open(output, 'r+') as file:
        file.write(merged_bands)
    os.remove(files[-1])