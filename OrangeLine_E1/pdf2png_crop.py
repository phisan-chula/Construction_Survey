#
# pdf2png_crop : convert an table PDF file to grey-scale png raster
#                for preparation to be OCRed.
#
# P.Santitamnont , 25 June 2022  
#
from PIL import Image
import pytesseract
import pandas as pd
import geopandas as gpd
import os
from pathlib import Path

##################################################################
PDF = Path( r'./Data/1-OR00-GN-2006 SETTING OUT DATA-EAST.pdf' )
TABLES = { 'T1': ( 1424, 866, 4851,6128) ,
           'T2': ( 5439, 792, 8896,4716)  }

##################################################################
PNG      = f'RESULT/{PDF.stem}'    # pdftoppm will add .png
if 1:
    CMD = f"pdftoppm -r 600 -png -gray -singlefile '{PDF}' '{PNG}' "
    print( CMD )
    os.system( CMD )

##################################################################
if 1:
    for table,bbox in TABLES.items():
        print(f'Cropping {table} with bbox {bbox} ...' )
        im = Image.open( f'{PNG}.png' )
        im_crop = im.crop( bbox )
        PNG_CROP = f'{PNG}_{table}.png' 
        print(f'Writing {PNG_CROP}...') 
        im_crop.save( PNG_CROP )

#import pdb ;pdb.set_trace()
