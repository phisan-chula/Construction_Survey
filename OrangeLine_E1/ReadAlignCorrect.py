#
#
# pdf2gis.py : convert pdf file of a technical map data onto dataframe 
#              and write out to geopackage
# Author : P.Santitamnont (phisan.chula@gmail.com)
#
#
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString

HDR = ['POINT', 'CHAINAGE', 'NORTH', 'EAST', 'DEFLEC', 'SPIRAL_IN', 'RADIUS',
        'SPIRAL_OUT', 'CANT', 'SPEED_KPH' ]
         
#AL_EXCEL = ( './Data/DATA_EAST_1.xlsx', './Data/DATA_EAST_2.xlsx' )
AL_EXCEL = ( r'RESULT/1-OR00-GN-2006 SETTING OUT DATA-EAST_T1.xlsx',
             r'RESULT/1-OR00-GN-2006 SETTING OUT DATA-EAST_T2.xlsx' )

#################################################################
dfs = list()
for al_excel in AL_EXCEL:
    df = pd.read_excel( al_excel, engine='openpyxl', 
        header=None, names=HDR)
    dfs.append( df )
df = pd.concat( dfs, ignore_index=True  )

###### CORRECT failed OCR ########
cur_row = df[df.NORTH==1520997122]
if len(cur_row)==1:
    cur_row.loc[ cur_row.index,'NORTH'] = cur_row.iloc[0].NORTH/1000

df.at[ 34, ['POINT','CHAINAGE', 'NORTH', 'EAST' ] ]=\
                   ['S.T.', '26+268.474','1,520,997.122','671,808.910' ] 
df.at[ 89, ['POINT','CHAINAGE', 'NORTH', 'EAST' ] ]=\
                   ['S.T.', '29+012.540', 1_521_006.844, 674_222.123 ] 
df.at[ 94, ['POINT','CHAINAGE', 'NORTH', 'EAST'] ]=\
                   ['S.T.', '29+641.315', '1521459.264',  '674,658.766' ]

################################################################
def FixFloatOCR( val ):
    if isinstance( val, str ):
        val = val.replace( ',', '')
        digit  = val.split('.')
        digits = ''.join( digit[:-1] ) + '.' + digit[-1] 
        try:
            val = float( digits)  
        except:
            print(f'Failed OCR "{val}"...')
            import pdb ; pdb.set_trace()
    return val

#################################################################
for col in ('EAST','NORTH'):
    df[col] = df[col].apply( FixFloatOCR )
print( df[['NORTH', 'EAST']].describe() )
#import pdb ; pdb.set_trace()

gdfVertex = gpd.GeoDataFrame( df , crs='EPSG:32647', 
                geometry=gpd.points_from_xy( df.EAST, df.NORTH ) )
LS = LineString( gdfVertex.geometry.to_list() )
gdfTrav = gpd.GeoDataFrame( crs='EPSG:32647', geometry=[ LS,] )
gdfVertex.to_file( r'RESULT/df_align.gpkg', driver='GPKG', layer='AlignVertex' )
gdfTrav.to_file( r'RESULT/df_align.gpkg', driver='GPKG', layer='Traverse' )
import pdb ; pdb.set_trace()
