#
# GridGeodLine : calculate grid and geodetic distance and azimuth over 
#                a control line. Mangenetic declication (WMM2020) is also
#                calculate. If specified date in include each line of 
#                control point ( YYYY-MM-DD )
#
import sys 
import numpy as np
import pandas as pd
import geopandas as gpd
from pygeodesy.dms import toDMS
from pyproj import Geod
import subprocess as sp
from shapely.geometry import Point, LineString
from pathlib import Path


def DistAzim( FR, TO ):
    dE = TO.Easting-FR.Easting
    dN = TO.Northing-FR.Northing
    grid_dist = np.hypot( dE, dN )
    grid_az   = np.arctan2( dE, dN )
    _,grid_az = divmod( grid_az, np.pi*2 )  # 2PI
    grid_az = np.degrees( grid_az )
    geod_az12,_,geod_dist = WGS84.inv( FR.geometry.x, FR.geometry.y, 
                      TO.geometry.x, TO.geometry.y, radians=False)

    _,geod_az12 = divmod( geod_az12, 360. )  
    return grid_dist, grid_az, geod_dist, geod_az12

##############################################################
WGS84=Geod( ellps='WGS84' )
if len(sys.argv) == 2:
    FILE = sys.argv[1]
else:
    FILE = "MWA_CK_Ctrl.csv"

print( f'Reading control file {FILE:} ...' )
df = pd.read_csv( FILE )

gdfCTRL = gpd.GeoDataFrame( df, crs='EPSG:32647', 
        geometry=gpd.points_from_xy( df.Easting, df.Northing ) )
gdfCTRL = gdfCTRL.to_crs('EPSG:4326')

line = list()
for i in range( len(gdfCTRL)//2 ):
    to = 2*i; fr = to+1
    to = gdfCTRL.iloc[ to:to+1 ].iloc[0]
    fr = gdfCTRL.iloc[ fr:fr+1 ].iloc[0]
    grid_dist, grid_az, true_dist, true_az = DistAzim( fr, to )
    LS = LineString( [ fr.geometry, to.geometry ] )
    line.append( [ fr.STATION,to.STATION, grid_dist, grid_az, toDMS(grid_az),
        true_dist, true_az, toDMS(true_az) , LS ] )
dfLine = pd.DataFrame( line , columns=['STA', 'BS', 
           'gridDist', 'gridAz', 'gridAz_', 'trueDist', 'trueAz', 'trueAz_', 'geometry']  )
gdfLine = gpd.GeoDataFrame( dfLine, crs='EPSG:4326', geometry=dfLine.geometry )
#import pdb; pdb.set_trace()

def MagDecl( row ):
    if 'Date' in row.keys():
        dt = row.Date
    else:
        dt = pd.Timestamp.now().strftime( '%Y-%m-%d' )
    cmd = f'MagneticField -n wmm2020 -p 10 --input-string "{dt:} {row.geometry.y:} {row.geometry.x:}"'
    res = sp.run( [cmd], shell=True, capture_output=True, text=True )
    decli = toDMS( float(res.stdout.split()[0]) )
    #import pdb; pdb.set_trace()
    return dt, decli
gdfCTRL[['Date','Decli']] = gdfCTRL.apply( MagDecl, axis=1, result_type='expand' ) 

print( gdfCTRL[ ['STATION', 'Northing', 'Easting', 'Date', 'Decli'] ] )
print( gdfLine[ ['STA', 'BS', 'gridDist', 'gridAz', 'gridAz_', 'trueDist', 'trueAz', 'trueAz_' ] ] )
Path('./CACHE').mkdir(parents=True, exist_ok=True)
gdfLine.to_file( './CACHE/CtrlLinePnt.gpkg', layer='CntrolLine', driver='GPKG' )
gdfCTRL.to_file( './CACHE/CtrlLinePnt.gpkg', layer='CntrolPoint', driver='GPKG' )
print( '************** end ***************')

