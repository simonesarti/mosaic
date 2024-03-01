import os


"""
Wrapper around the execution of the merge of multiple images, using the GDAL library.
"""
def gdal_merge(tiffs, bbox, output, dstnodata = None):

    filelist = 'input.txt'
    with open(filelist, 'w') as f:
        for tiff in tiffs:
            f.write(tiff+'\n')

    
    command = 'gdalwarp{args} -overwrite -s_srs EPSG:4326 -t_srs EPSG:4326 -te {min_lon} {min_lat} {max_lon} {max_lat} --optfile {tiffs} {output}'
    if(dstnodata is not None):
        args = ' -dstnodata {dstnodata}'.format(dstnodata=dstnodata)
    else:
        args = ''
    command = command.format(args = args, min_lon = bbox[0], min_lat = bbox[1], max_lon = bbox[2], max_lat = bbox[3], tiffs = filelist, output = output)

    print(command)
    os.system(command)
    os.remove(filelist)
    return(output)



