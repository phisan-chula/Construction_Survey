#
#
from PIL import Image
import pytesseract
import pandas as pd
import geopandas as gpd
import os
from pathlib import Path

PDF = r'../Data/1-OR00-GN-2006 SETTING OUT DATA-EAST.pdf'
PNG = r'CACHE/pdf2png'

if 1:
    CMD = f"pdftoppm -r 600 -png -gray -singlefile '{PDF}' {PNG}"
    print( CMD )
    os.system( CMD )

if 1:
    bitmap = f'{PNG}.png', 1424, 866, 4851, 6128 
    im = Image.open( bitmap[0] )
    im_crop = im.crop( bitmap[1:] )
    im_crop.save( r'CACHE/crop.png')

    #df = pytesseract.image_to_data( im_crop, lang='eng', 
    #        output_type='data.frame' )
    lines = pytesseract.image_to_string( im_crop, lang='eng' )
    #lines = lines.split('\n')
    #for line in lines:
    print( lines)

import pdb ;pdb.set_trace()
