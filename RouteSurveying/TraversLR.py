#
#
# TraversLR.py :
# Author Phisan Santitamnont
# Faculty of Engineering, Chulalongkorn University (phisan.chula@gmail.com )
# version 0.21 : 20 Dec 2022
#
#
import pandas as pd
import geopandas as gpd
import numpy as np
import fiona
from shapely.geometry import Point, LineString
from pyproj import CRS, Proj
from pyproj.transformer import Transformer
from pathlib import Path
fiona.drvsupport.supported_drivers['KML'] = 'rw'

UTM = 'epsg:32647'
LL  = 'epsg:4326'
UTM_to_LL = Transformer.from_crs( UTM, 'epsg:4326' , always_xy=True )
###########################################################################
DIV = 50     # STATION DIVISION
CACHE = './CACHE'

###########################################################################
TRV = './Data/CampTravENH.csv'
df = pd.read_csv( TRV )
dfTRV = gpd.GeoDataFrame( df, crs='EPSG:32647', 
            geometry=gpd.points_from_xy( df.E, df.N ) )
print( f'Reading traversing file {TRV}...' )

LS = LineString( dfTRV[['E','N']].to_numpy() )
print( f'Length = {LS.length:,.3f} meter')
dfLS = gpd.GeoDataFrame( {'Name':['TravLine'] } , crs='EPSG:32647',
           geometry=[ LS, ] )
###########################################################################
def CalcLR( row ):
    LngLat =  UTM_to_LL.transform( row.E, row.N )
    dist = LS.project( Point(row.E,row.N ), normalized=False ) 
    sf =  Proj(LL).get_factors( *LngLat ).meridional_scale
    return LngLat[1],LngLat[0], dist, sf  
dfTRV[['Lat','Lng','dist_m', 'PSF']] = dfTRV.apply( 
                           CalcLR, axis=1, result_type='expand' )
print( dfTRV )
##########################################################################
CNT_DIV = int(LS.length/ DIV)
STA_DIV = np.arange(0, CNT_DIV*DIV+1 , DIV ) 
STA_DIV = list( STA_DIV ) + [ LS.length ]
print( STA_DIV )
sta = list()
for i in STA_DIV:
    pnt = LS.interpolate( i, normalized=False ) 
    sta.append( [ i, pnt.x, pnt.y,  pnt ] )
dfDIV = gpd.GeoDataFrame( sta, crs=UTM, 
        columns=[ 'dist_m', 'E', 'N', 'geometry' ]  )
dfDIV[['Lat','Lng','dist_m', 'PSF']] = dfDIV.apply(
                           CalcLR, axis=1, result_type='expand' )
def MakeSta( row ):
    km, mt = divmod( row, 1000) 
    if  np.isclose( [mt],[1000] ):
        #import pdb ; pdb.set_trace()
        km = km+1;  mt = 0
    sta = '{:03.0f}+{:03.0f}'.format( 1000*km, mt )
    return  sta
dfDIV['Sta'] = dfDIV['dist_m'].apply( MakeSta )
print( dfDIV )
##########################################################################
Path(f'{CACHE}/').mkdir(parents=True, exist_ok=True)
OUT_GPCK = f'{CACHE}/TravDiv_LR.gpkg'
print( f'Writing output file {OUT_GPCK:} ...' )
dfDIV.to_file( OUT_GPCK, driver='GPKG', layer='Division' )
dfTRV.to_file( OUT_GPCK, driver='GPKG', layer='TravPoint' )
dfLS.to_file( OUT_GPCK, driver='GPKG', layer='TravLine' )
ND_FLT = { 'E':3 , 'N':3 , 'H':3 , 'dist_m':3, 'PSF':7 }
for i in ND_FLT.keys():
    FMT = '{{:.{:d}f}}'.format( ND_FLT[i] )
    dfTRV[i] = dfTRV[i].map( FMT.format)
    if i =='H': continue
    dfDIV[i] = dfDIV[i].map( FMT.format)

OUT_TRV = f'{CACHE}/TravSTATION.csv'
dfTRV[['Sta','EPSG','E','N','H','dist_m','PSF' ]].to_csv( OUT_TRV, 
            index=False, index_label=None )
OUT_DIVI = f'{CACHE}/TravDIVISION.csv'
dfDIV[['Sta','E','N','dist_m','PSF' ]].to_csv( OUT_DIVI, 
            index=False, index_label=None )
print('@@@@@@@@@@@@@@@@@ end of TraversLR.py @@@@@@@@@@@@@@@@')
#import pdb ; pdb.set_trace()
