from typing import Tuple
from sentinelhub import (
    MimeType, 
    SentinelHubRequest, 
    bbox_to_dimensions, 
    BBoxSplitter,
    BBox
)


"""
Retry multiple time the execution of a function with a set of parameters in input.
"""
def SH_retry(max_retry, fun, **args):
    for attempt in range(1,max_retry+1):
        try:
            return(fun(**args))
        except Exception as e:
            print(f"attempt {attempt} failed: {e}" )
    
    raise Exception(f'Execution unsuccessful')


def get_SH_request_input(
    time_interval,
    data_collection,
    mosaicking_order,
    other_args:dict=None,
):
    
    input_data_params = {
        "data_collection": data_collection,
        "time_interval": time_interval,
        "mosaicking_order": mosaicking_order,
    }

    if other_args is not None:
        input_data_params["other_args"] = other_args

    input_data = SentinelHubRequest.input_data(**input_data_params)
    return input_data


def create_image_request(
    bbox, 
    resolution:int,
    time_interval,
    data_collection,
    evalscript,
    mosaicking_order,
    request_additional_args:dict = None,
):
    
    size = bbox_to_dimensions(
        bbox=bbox, 
        resolution=resolution
    )

    request_input_data = get_SH_request_input(
        time_interval=time_interval,
        data_collection=data_collection,
        mosaicking_order=mosaicking_order,
        other_args=request_additional_args,
    )
    
    request = SentinelHubRequest(
        data_folder="../tmp_images",
        evalscript=evalscript,
        input_data=[request_input_data],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        size=size,
        config=None,
    )
    
    return request


def get_bbox_list(
    bbox, 
    crs, 
    split_shape,
):
    
    bbox_splitter = BBoxSplitter(
        [BBox(bbox, crs=crs)], 
        crs = crs, 
        split_shape = split_shape
    )
    bbox_list = bbox_splitter.get_bbox_list()

    return bbox_list