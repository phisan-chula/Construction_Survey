#
#
PROG='''
Setting_Columns.py : read pier shedule and pier config (YAML ) and 
                 calculation columns postions for setting-out
Author:    Phisan.Chula@gmail.com , Chulalongkorn University
Version: 0.1 (5-Jan-2022)
Acknowledgement: thanks Khun SubenMukem@ITD for sample data and inspiration.
'''
#
#
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point,MultiPoint
from shapely import affinity
from pygeodesy.dms import degDMS,toDMS,parseDMS
import numpy as np
import yaml,sys

###################################################################
def CalcColumns( PIER, CHOS ):
    ''' Pier could contains many columns specified by local 
        coordinate system  e.g. type F4B-U
                       | Y
                       |
                 3+    |     +2      
                       x (PIER) -------------> X
                 4+          +1 (column number) 
    '''
    final_az = PIER['PIER AZIMUTH']+ PIER['FOOTING SKEW']
    _,rot_ang = divmod( 90.-final_az , 360 )
    rot_col = affinity.rotate( MultiPoint(list(CHOS.values())) , rot_ang, 
                      use_radians=False, origin=Point(0.0,0.0) )
    trn_col = affinity.translate( rot_col,xoff=PIER.geometry.x, yoff=PIER.geometry.y ) 
    col_data = list()
    for i in range( len(CHOS) ):
        col_data.append( (PIER['PIER NO.'], PIER['FOUNDATION TYPE'], 
                         list(CHOS.keys())[i], final_az, trn_col.geoms[i] ) )
    df =  pd.DataFrame( col_data, columns=['PierNum','PierTyp',
                        'ColNum','FinalAz', 'geometry'] )
    gdf = gpd.GeoDataFrame( df , crs='EPSG:32647', geometry='geometry')
    return gdf

###################################################################
def ExportPileSchedule( EXPORT_FILE ):
    with open(EXPORT_FILE, 'w' ) as f:
        for (PIER,TYPE,AZ),grp in df_column.groupby(
                by=['PierNum','PierTyp','FinalAz'],axis=0):
            pier = df_pier[df_pier['PIER NO.']==PIER].iloc[0]
            dms = toDMS( AZ, prec=2, sep='-' ) 
            f.write( 'CL,{:.3f},{:.3f},{},{}, {}\n'.format(
                pier.geometry.y, pier.geometry.x,PIER,dms, TYPE) )
            for j,row in grp.iterrows():
                f.write( '{}/{},{:.3f},{:.3f}\n'.format( PIER,row.ColNum,
                               row.geometry.y,row.geometry.x ) )

###################################################################
if len(sys.argv)==3:
    _,PIER_CSV,CHOS_YAML = argv
else:
    PIER_CSV,CHOS_YAML  = '01_Pier_Schedule.csv', '02_CHOS_Pier.yaml' 
###################################################################

df_pier = pd.read_csv( PIER_CSV ) 
df_pier = gpd.GeoDataFrame( df_pier, crs='EPSG:32647', 
           geometry=gpd.points_from_xy( df_pier.EASTING, df_pier.NORTHING) )
with open( CHOS_YAML ) as file:
    CHOS_YAML = yaml.load(file, Loader=yaml.FullLoader)

#################################################################
print( PROG )
print( 'Summary of number of columns for pier category :\n')
print( df_pier['FOUNDATION TYPE'].value_counts() )
df_column = None
for i,row in df_pier.iterrows():
    ftype = row['FOUNDATION TYPE'] 
    if pd.isna( ftype ):
        print( 'Ignore ... foundation type N/A :', i, row['PIER NO.'] ) 
    else:
        print( 'Column coordinates for pier : {} ({}) '.format(row['PIER NO.'],ftype))
        chos = CHOS_YAML[ row['FOUNDATION TYPE'] ]
        df_col = CalcColumns( row, chos ) 
        if df_column is None:
            df_column = df_col 
        else:
            df_column = pd.concat([df_column,df_col],axis=0,ignore_index=True )
###############################################################
GIS_OUT = '03_PierColumn.gpkg'
CSV_OUT = '04_Export_Pile_Schedule.csv'
print(f'Writing GIS file : {GIS_OUT} ...')
df_pier['LABEL']  = df_pier['PIER NO.'] + '\n'+ df_pier['FOUNDATION TYPE']
df_pier.to_file(   GIS_OUT, driver='GPKG', layer='Pier' )
df_column.to_file( GIS_OUT, driver='GPKG', layer='Columns' )
print(f'Writing Export CSV file : {CSV_OUT} ...')
ExportPileSchedule( CSV_OUT )
print('@@@@@@@@@@@@@@@@@@@@@@@@@@@ end @@@@@@@@@@@@@@@@@@@@@@@@@@@')
#import pdb ; pdb.set_trace()
