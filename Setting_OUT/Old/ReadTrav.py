#
#
#
#
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import pygeodesy.dms as dms


def rad2DMS( rad ):
    return dms.toDMS( np.degrees(rad), prec=1 ) 

def DDMMSS2ddRad( row ):
    ang = f'{row:.4f}'.split('.')    #   ddd.mmss
    d = float( ang[0] ) 
    m = float( ang[1][0:2])/60
    s = float( ang[1][2:4])/3600
    return np.radians(d+m+s)

class SideShot:
    def __init__( self, FILEXLS ):
        dfDATA = pd.read_excel( FILEXLS ,engine='openpyxl', sheet_name='DATA')
        dfDATA['HAngle'] = dfDATA['Hor.Angle'].apply( DDMMSS2ddRad )
        dfDATA['ZAngle'] = dfDATA['Zenith Ang'].apply( DDMMSS2ddRad )
        dfCTRL = pd.read_excel( FILETRA ,engine='openpyxl', 
                    sheet_name='Sheet2', header=None, 
                    names=['Pnt', 'North', 'East', 'Elev' ] )
        self.dfDATA = dfDATA ; self.dfCTRL = dfCTRL

    def Az2PI( self, FR,TO ):
        fr = self.dfCTRL[self.dfCTRL.Pnt==FR ].iloc[0]
        to = self.dfCTRL[self.dfCTRL.Pnt==TO ].iloc[0]
        az = np.arctan2( to.North-fr.North, to.East-fr.East )
        return  divmod( az, np.pi )[1]

    def To3DPnt( self, Az, DATA ):
        Pnt0,N0,E0,H0 = self.dfCTRL[ 
                        self.dfCTRL.Pnt== DATA['Base Point']].iloc[0]
        import pdb; pdb.set_trace()
        SlopDist = DATA['Slope Dist'] + DATA['Prism']/1000
        HDist = SlopDist*np.sin( DATA.ZAngle )
        VDist = SlopDist*np.cos( DATA.ZAngle )
        E1 = E0 + HDist*np.sin( Az )
        N1 = N0 + HDist*np.cos( Az )
        H1 = H0 + VDist
        return E1,N1,H1
         
    def SIDE_SHOT( self, BSFS, AX=None ):
        fr     = BSFS.iloc[0]['Base Point']
        to     = BSFS.iloc[0]['Tgt.Pt']
        AZ_BS  = self.Az2PI( fr,to )
        print( 'AZ_BS', rad2DMS( AZ_BS ) )
        ENH_BS = self.To3DPnt( AZ_BS, BSFS.iloc[0] )

        Ang    = BSFS.HAngle.iloc[1]-BSFS.HAngle.iloc[0]
        AZ_FS  = divmod( AZ_BS+Ang, 2*np.pi )[1] 
        ENH_FS = self.To3DPnt( AZ_FS, BSFS.iloc[1] )
        if AX is not None:
            def PlotPntTxt( E,N,TXT, s=30, c='red', ):
                AX.scatter( [E,],[N,], s, c, marker='^' )
                AX.text( E, N , TXT, color=c )
            pnt_fr = self.dfCTRL[self.dfCTRL.Pnt==fr ].iloc[0]
            pnt_to = self.dfCTRL[self.dfCTRL.Pnt==to ].iloc[0]
            PlotPntTxt( pnt_fr.East, pnt_fr.North, pnt_fr.Pnt )
            PlotPntTxt( pnt_to.East, pnt_to.North, pnt_to.Pnt )
            AX.plot( [pnt_fr.East,pnt_to.East],[pnt_fr.North,pnt_to.North] )
            PlotPntTxt( ENH_BS[0], ENH_BS[1],'Chk', c='g'  )
            PlotPntTxt( ENH_FS[0], ENH_FS[1],'New', c='g' )
            AX.set_aspect('equal', 'box') 
            AX.ticklabel_format(useOffset=False,style='plain')
            AX.tick_params(axis='x', rotation=90)
            AX.grid()
        return ENH_BS,ENH_FS 
        
#########################################################
#########################################################
#########################################################
FILETRA = r'data for traverse.xlsx'
ss = SideShot( FILETRA )

for i in range( 0, len(ss.dfDATA), 4 ):
    fig,ax = plt.subplots( nrows=1, ncols=2, figsize=(12,8) )
    SS_LR = ss.dfDATA.iloc[i:i+4]
    Pnt3FL = ss.SIDE_SHOT( SS_LR.iloc[0:2] ,      AX=ax[0] )
    Pnt3FR = ss.SIDE_SHOT( SS_LR.iloc[2:4][::-1], AX=ax[1] )
    plt.tight_layout()
    #plt.show()
    PLT =  f'CACHE/SS{i:03d}.png'
    print(f'Plotting "{PLT}" ...' )
    plt.savefig( PLT )
    if i==0:
        break

