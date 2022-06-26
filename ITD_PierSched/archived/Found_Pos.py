#
#
#
#
#
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point,MultiPoint
from shapely.affinity import rotate,translate
from pygeodesy.dms import toDMS,parseDMS
import matplotlib.pyplot as plt
import numpy as np


def PlotPier( ):
    fig,ax = plt.subplots(1,1,figsize=(20,20) )
    df_pier.plot.scatter( x='EASTING', y='NORTHING', c='DarkBlue', ax=ax )
    #ax.set_aspect(1.0/ax.get_data_ratio(), adjustable='box')
    ax.tick_params(axis='x', labelrotation=90)
    ax.ticklabel_format(useOffset=False, style='plain')
    if 0:
        L,R =ax.get_xlim(); T,B =ax.get_ylim()
        LR=(L+R)/2        ; TB = (T+B)/2
        size=R-L if (R-L)>(T-B) else T-B
        ax.set_xlim( LR-size/2, LR+size/2 )
        ax.set_ylim( TB-size/2, TB+size/2 )
        plt.gca().set_aspect('equal', adjustable='box')
    ax.grid()
    fig.tight_layout()
    plt.savefig('PlotPier.pdf')
    #plt.show()

###################################################################
def CalcPier( PIER, CHOS ):
    ''' Pier contains many holes e.g. type F4B-U
                 3+          +2      
                       x (PIER)
                 4+          +1 (holes) 
    '''
    _,rot = divmod( 90.-( PIER['PIER AZIMUTH']+ PIER['FOOTING SKEW'] ), 360 )
    #import pdb ; pdb.set_trace()
    hole_pos = list()
    for i,row in CHOS.iterrows():
        rot_hole = rotate( row['geometry'], rot, 
                        use_radians=False, origin=Point(0.0,0.0) )
        rot_tr_hole = translate( Point(rot_hole) ,
                       xoff=PIER['EASTING'], yoff=PIER['NORTHING'] ) 
        hole_pos.append( (PIER['PIER NO.'], row['TYPE'], row['No'], 
                          Point(rot_tr_hole) ) )
    df =  pd.DataFrame( hole_pos, columns=['PierNum','PierTyp',
                            'HoleNum','geometry'] )
    #print( hole_pos ); print( df )
    gdf = gpd.GeoDataFrame( df , crs='EPSG:32647', geometry='geometry')
    return gdf

###################################################################
def MakeHoleUV( df_chos ):
    holes=list()
    for i,row in df_chos.iterrows():
        for i in range(0,10):
            pnt = row[f'Point.{i}']
            ch = row[f'CH.{i}']
            os = row[f'OS.{i}']
            if pd.isna(ch) : break
            holes.append( [ row['TYPE'], pnt, Point(ch,os) ] )
            #import pdb ; pdb.set_trace()
    return pd.DataFrame( holes, columns=['TYPE', 'No', 'geometry'] )

def WriteYaml_CHOS( df_CHOS):
    with open("CHOS_Pier.yaml", "w") as f:
        f.write( 
'''#
#
# Chainage-Offset configuration for pier
# Format
# Pier-Type:
#     Columns_No : [ +/-chainage, +/-offset ]
#     Columns_No : [ +/-chainage, +/-offset ]
#     Columns_No : [ +/-chainage, +/-offset ]
#     Columns_No : [ +/-chainage, +/-offset ]
#
#
''')
        for i,grp in df_CHOS.groupby('TYPE'):
            print(i,grp)
            f.write( f'{i}:\n' )
            for j,row in grp.iterrows():
                print( j,row)
                f.write( 
                f'    {row.No} : [{row.geometry.x:+.3f},{row.geometry.y:+.3f}]\n')
                #import pdb ; pdb.set_trace()
    return
###################################################################
###################################################################
###################################################################
dms = toDMS(123.4567890,prec=1) 
print( dms )
dd = parseDMS("123:12:34", sep=':' )
print( dd )

##################
df_pier = pd.read_csv( 'FoundationPosition-Survey-Rev01/01_Pier_Schedule.csv') 
df_pier = gpd.GeoDataFrame( df_pier, crs='EPSG:32647', 
           geometry=gpd.points_from_xy( df_pier.EASTING, df_pier.NORTHING) )
df_chos = pd.read_csv( 'FoundationPosition-Survey-Rev01/02_CH&OS_Axis.csv') 
df_chos.rename( columns={'Point':'Point.0', 'CH':'CH.0', 'OS':'OS.0' }, inplace=True )
df_CHOS = MakeHoleUV( df_chos )
WriteYaml_CHOS( df_CHOS)

print( 'Summary of number of piers by category :\n')
print( df_pier['FOUNDATION TYPE'].value_counts() )
print( 'Summary of number of holes to be located for each pier category:\n')
print( df_CHOS['TYPE'].value_counts() )
df_holes = None
for i,row in df_pier.iterrows():
    ftype = row['FOUNDATION TYPE'] 
    if pd.isna( ftype ):
        print( 'Ignore ... foundation type N/A :', i, row['PIER NO.'] ) 
    else:
        #print( i, ftype )
        chos = df_CHOS[ df_CHOS['TYPE']==row['FOUNDATION TYPE'] ]
        hole_EN = CalcPier( row, chos ) 
        if df_holes is None:
            df_holes = hole_EN.copy()
        else:
            #print( hole_EN )
            df_holes = pd.concat( [df_holes, hole_EN], 
                    axis=0, ignore_index=True )
#PlotPier(  )
df_holes.to_file( 'df_holes.gpkg', driver='GPKG', layer='Holes' )
df_pier.to_file( 'df_holes.gpkg', driver='GPKG', layer='Pier' )
import pdb ; pdb.set_trace()
