from src.utils.sh_credentials import set_SH_credentials
from src.utils.cli import get_cli_arguments


def get_mosaic(image:str):

    if image == "sentinel1":
        from src.sentinel1 import mosaic
        return mosaic
    if image == "sentinel2":
        from src.sentinel2 import mosaic
        return mosaic
    if image == "dwlulc":
        from src.dwlulc import mosaic
        return mosaic
    if image == "esalulc":
        from src.esalulc import mosaic
        return mosaic
    if image == "copernicusdem":
        from src.copernicusdem import mosaic
        return mosaic

   
def main():
   
    set_SH_credentials()

    image, mosaic_args = get_cli_arguments()
    mosaic = get_mosaic(image)
    mosaic(**mosaic_args)


if __name__ == "__main__":
    main()
