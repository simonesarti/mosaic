from pathlib import Path
import numpy as np
import rasterio
from scipy.interpolate import NearestNDInterpolator


def save_tif(
    output_path: Path,
    profile: dict,
    bands: np.ndarray,
    masks: np.ndarray = None,
) -> None:
   
    n_channels = bands.shape[0]

    with rasterio.open(output_path, "w", **profile) as output_file:
        for channel_idx in range(n_channels):  # Write bands to the output file
            to_write = bands[channel_idx, :, :]
            to_write_idx = channel_idx + 1
            output_file.write(to_write, to_write_idx)

        if masks is not None:
            for channel_idx in range(n_channels):
                to_write = masks[channel_idx, :, :]
                to_write_idx = n_channels + channel_idx + 1
                output_file.write(to_write, to_write_idx)


def interpolation_is_needed(
    bands: np.ndarray,
    masks: np.ndarray,
    nodata: int | float,
) -> bool:
   
    need_interpolation = (nodata in bands) or ((masks is not None) and (0 in masks))
    return need_interpolation


def interpolate_tif(
    tif_path: Path,
    interpolated_path: Path = None,
    default: int | float = 0
) -> None:
   
    with rasterio.open(tif_path, "r") as tif_image:
        tif_bands = tif_image.read()
        tif_masks = tif_image.read_masks()
        tif_profile = tif_image.profile

    # skip tif interpolation is tif already ok
    if interpolation_is_needed(tif_bands, tif_masks, tif_profile["nodata"]):
        interpolated_bands = _interpolate_bands(
            tif_bands=tif_bands,
            tif_masks=tif_masks,
            tif_dtype=tif_profile["dtype"],
            tif_nodata=tif_profile["nodata"],
            default=default,
        )
    else:
        interpolated_bands = tif_bands

    # overite original tif if output path not spcified
    if interpolated_path is None:
        interpolated_path = tif_path

    save_tif(
        output_path=interpolated_path,
        profile=tif_profile,
        bands=interpolated_bands,
        mask=None,
    )


def _interpolate_bands(
    tif_bands: np.ndarray,
    tif_masks: np.ndarray,
    tif_dtype: np.dtype,
    tif_nodata: int | float,
    default: int | float = 0,
) -> np.ndarray:
   
    interpolated_bands = []

    n_channels = tif_bands.shape[0]

    for channel in range(n_channels):
        band = tif_bands[channel, :, :]
        mask = tif_masks[channel, :, :]

        # skip band interpolation is band already ok
        if interpolation_is_needed(band, mask, tif_nodata):
            interpolated_band = _interpolate_band(
                band=band,
                mask=mask,
                tif_dtype=tif_dtype,
                tif_nodata=tif_nodata,
                default=default,
            )
        else:
            interpolated_band = band

        interpolated_bands.append(interpolated_band)

    interpolated_bands = np.stack(interpolated_bands, axis=0)

    return interpolated_bands


def _interpolate_band(
    band: np.ndarray,
    mask: np.ndarray,
    tif_dtype: np.dtype,
    tif_nodata: int | float,
    default: int | float = 0,
) -> np.ndarray:
   
    band_shape = band.shape

    band_submask = (band != tif_nodata)
    mask_submask = (mask != 0)

    submask = np.logical_and(band_submask, mask_submask)
    # True where channel band contains a valid value and the pixel is not masked

    if True in submask:  # at least one value from which to interpolate
        valid_indexes = np.where(submask)
        valid_values = band[valid_indexes]
        interp = NearestNDInterpolator(np.transpose(valid_indexes), valid_values)
        interpolated_band = interp(*np.indices(band_shape))

    else:  # assign default value everywhere
        interpolated_band = np.full(
            shape=band_shape, fill_value=default, dtype=tif_dtype
        )

    return interpolated_band