
import sys
# import argparse
from tifffile import TiffFile
from apeer_ometiff_library import io, processing, omexmlClass


def extract_image_description(ometiff):
    with TiffFile(ometiff) as tif:
        tags = tif.pages[0].tags

    desc_tag = tags.get('ImageDescription', '')
    return desc_tag


if __name__ == '__main__':
    ometiff = sys.argv[1]
    print(ometiff)
    # image_desc = extract_image_description(ometiff)
    # print(image_desc.name)
    # print(image_desc.value)

    # Using Apeer
    # image_desc = extract_image_description(ometiff)

    array, omexml = io.read_ometiff(ometiff)
    print(omexml)
