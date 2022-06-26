#
#
#
#
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import pygeodesy.dms as dms
from SurveyFund import *

def DDMMSS2Angu( row ):
    return Degree( row, TYPE='DMS59' )

class SideShot:
    def __init__( self, FILEXLS ):
        dfDATA = pd.read_excel( FILEXLS ,engine='openpyxl', sheet_name='DATA')
        dfDATA['HAngle'] = dfDATA['Hor.Angle'].apply( DDMMSS2Angu )
        dfDATA['ZAngle'] = dfDATA['Zenith Ang'].apply( DDMMSS2Angu )
        dfCTRL = pd.read_excel( FILETRA ,engine='openpyxl', 
                    sheet_name='Sheet2', header=None, 
                    names=['Pnt', 'North', 'East', 'Elev' ] )
        self.dfDATA = dfDATA 
        self.dfCTRL = dfCTRL

    def CheckName( self ):
        import pdb ; pdb.set_trace()
        print( self.dfCTRL.Pnt.value_counts() )
        print( self.dfData['Base Point'].value_counts() )
        print( self.dfData['Tgt.Pt'].value_counts() )
        pass

    def To3DPnt( self, DATA, PREFIX ):
        assert( DATA.iloc[0]['(TS Type)']=='BS')
        assert( DATA.iloc[1]['(TS Type)']=='SS')    #  CK's SideShot SS
        PntList = list()
        for pnt in ('Base Point','Tgt.Pt'):
            STA = DATA.iloc[0][pnt]
            bs = self.dfCTRL[ self.dfCTRL.Pnt==STA ].iloc[0]
            pnt = GeodPnt( STA, bs.East, bs.North, bs.Elev )
            PntList.append( pnt )
        SlopDist = DATA.iloc[1]['Slope Dist'] + DATA.iloc[1]['Prism']/1000
        trv = Traverse( PntList[0], PntList[1] )
        FS = DATA.iloc[1]['Tgt.Pt']
        try:
            fs = self.dfCTRL[ self.dfCTRL.Pnt==FS ].iloc[0]
        except: 
            print(f'***ERROR*** "{FS}" not found in coordinate list...')
            print(f'***ERROR*** {DATA}')
            import pdb ; pdb.set_trace()
        ang = divmod( DATA.iloc[1]['HAngle'].deg-
                      DATA.iloc[0]['HAngle'].deg, 360)[1]
        res_fs = trv.PathTo( fs.Pnt, Degree( ang ), 
                        SlopDist, AngZ=DATA.iloc[1].ZAngle ) 
        trv.PlotPathTo( PREFIX)
        return res_fs 
         
#########################################################
#########################################################
#########################################################
STOP_AT = 20
FILETRA = r'data for traverse.xlsx'
ss = SideShot( FILETRA )
result = list()
for i in range( 0, len(ss.dfDATA), 4 ):
    fig,ax = plt.subplots( nrows=1, ncols=2, figsize=(12,8) )
    SS_LR = ss.dfDATA.iloc[i:i+4]
    FL = ss.To3DPnt( SS_LR.iloc[0:2], PREFIX=f'{i:03d}' )
    print( FL )
    result.append( [FL.NAME, "FL", FL.E, FL.N, FL.H] ) 
    FR = ss.To3DPnt( SS_LR.iloc[2:4][::-1], PREFIX=f'{i+4:03d}')
    print( FR )
    result.append( [FL.NAME, "FR", FL.E, FL.N, FL.H] ) 
    print(f'Plotting  ...' )
    if i>=STOP_AT:
        break
df = pd.DataFrame( result, columns=['NAME','FACE', 'E', 'N', 'H' ] )
for name,grp in df.groupby( 'NAME' ):
    print( f'{name} meanE:{grp.E.mean():15,.3f} m    Std.E:{grp.E.std():10.3f} m' )
    print( f'{name} meanN:{grp.N.mean():15,.3f} m    Std.N:{grp.N.std():10.3f} m' )
    print( f'{name} meanH:{grp.H.mean():15,.3f} m    Std.H:{grp.H.std():10.3f} m' )
#import pdb ; pdb.set_trace()

