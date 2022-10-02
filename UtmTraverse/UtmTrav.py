#
#
# UtmTrav : calculation of an open and cloded traverse
#           projected on planeor UTM projected grid.
#
#
from pygeodesy.dms import toDMS, parseDMS
from pygeodesy import Utm,parseUTM5,Ellipsoids
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import yaml,sys
from pathlib import Path
###############################################################
def parse_dms( dms ):
    return parseDMS( dms, sep=':')

class UTMTraverse:
    def __init__(self, YAMLFILE):
        with open(YAMLFILE,'r') as f:
        	YAML = yaml.safe_load( f )
        self.df_Sta = pd.DataFrame.from_dict(YAML['FIXPNT'] ,
            orient='index', columns=['Easting','Northing'] )
        def UtmStr(row):
            UTM_PRE = f"{YAML['ZONE']} {YAML['HEMI']} "
            return '{} {} {}'.format( UTM_PRE, row.Easting, row.Northing )
        self.df_Sta['UTMSTR'] =  self.df_Sta.apply( UtmStr, axis='columns') 
        self.df_Sta['Utm'] = self.df_Sta['UTMSTR'].apply(parseUTM5)
        self.df_Sta.drop( columns=['Easting','Northing'], axis='index', inplace=True )
        self.df_Sta['Iter'] = -1
        self.df_Sta.reset_index(inplace=True)
        self.df_Sta.rename( columns={'index':'Name'}, inplace=True)
        self.df_Sta['Name'] = self.df_Sta['Name'].astype( str )
        ##############################
        self.df_Dis = pd.DataFrame.from_dict( YAML['DIST'],orient='index',
                            columns=['dist_m'] )
        self.df_Dis['Iter'] = -1
        self.df_Dis['ScalFac'] = 0.0
        self.df_Dis.reset_index(inplace=True)
        self.df_Dis.rename( columns={'index':'Name'}, inplace=True)
        ##############################
        self.df_Ang = pd.DataFrame.from_dict( YAML['ANGL'],orient='index',
                            columns=['ang_dms'] )
        self.df_Ang['ang_deg'] = self.df_Ang['ang_dms'].apply( parse_dms )
        self.df_Ang['Iter'] = -1
        self.df_Ang[['ac_BS','ac_FS']] = [0.,0.]
        self.df_Ang['type'] = 'open'
        self.df_Ang.reset_index(inplace=True)
        self.df_Ang.rename( columns={'index':'Name'}, inplace=True)
        ##############################
        self.YAML = YAML
        #import pdb; pdb.set_trace()
        return
        
    def CalcTraverse(self,ITER):
        df_Sta = self.df_Sta[( self.df_Sta['Iter']==self.df_Sta['Iter'].max() )
                          |  (self.df_Sta['Iter']==-1) ]
        df_Dis = self.df_Dis[self.df_Dis['Iter']==-1]
        df_Ang = self.df_Ang[self.df_Ang['Iter']==-1]
        for i in range(len(df_Dis)):
            DIS_AT,DIS_TO = self.df_Dis.iloc[i]['Name'].split(',')
            DIST          = self.df_Dis.iloc[i]['dist_m']
            ANG_BS,ANG_AT,ANG_FS = self.df_Ang.iloc[i]['Name'].split(',')
            ANGL                 = self.df_Ang.loc[i]['ang_deg']
            TYPE                 = self.df_Ang.loc[i]['type']
            UtmBS = self.df_Sta[self.df_Sta['Name']==ANG_BS].iloc[-1]['Utm']
            UtmAT = self.df_Sta[self.df_Sta['Name']==ANG_AT].iloc[-1]['Utm']
            ######################################
            if ITER==0:
                k = 1.0 ; ac1 = 0.0 ; ac2 = 0.0
            else:
                UtmFS = self.df_Sta[self.df_Sta['Name']==ANG_FS].iloc[-1]['Utm']
                k   = self.LineSF( UtmAT, UtmFS)
                ac1 = self.LineAC( UtmAT, UtmBS)
                ac2 = self.LineAC( UtmAT, UtmFS)
                #ac1 = 27.17/3600; #ac2 = 20.67/3600
            BS_Azi = self.GridAz( UtmAT, UtmBS  )
            corrAng =  ANGL + (ac1-ac2 )
            FS_Azi = BS_Azi + corrAng
            _,FS_Azi = divmod( FS_Azi, +360 )
            ###################################### 
            GD = k*DIST
            ETo = UtmAT.easting  + GD*np.sin( np.radians(FS_Azi) )
            NTo = UtmAT.northing + GD*np.cos( np.radians(FS_Azi) )
            ###################################### 
            df_StaX = pd.DataFrame( { 'Name': ANG_FS,
                'UTMSTR':None, 'Utm': Utm( self.YAML['ZONE'], self.YAML['HEMI'],
                ETo,NTo),'Iter': ITER }, index=[0]  )
            self.df_Sta = pd.concat( [self.df_Sta, df_StaX], axis=0, ignore_index=True )
            df_DisX = pd.DataFrame( { 'Name':f'{DIS_AT},{DIS_TO}',
                'dist_m': GD, 'AdjAz':FS_Azi, 'Iter': ITER, 'ScalFac': k }, index=[0] )
            self.df_Dis = pd.concat( [self.df_Dis,df_DisX], axis=0, ignore_index=True )
            df_AngX= pd.DataFrame( { 'Name': f'{ANG_BS},{ANG_AT},{ANG_FS}', 
                'ang_dms': toDMS(corrAng), 'ang_deg': corrAng, 'Iter': ITER, 
                'ac_BS': ac1*3600, 'ac_FS': ac2*3600, 'type':TYPE }, index=[0] )
            self.df_Ang = pd.concat( [ self.df_Ang, df_AngX ], axis=0,ignore_index=True )
        #import pdb; pdb.set_trace()
        return self.df_Sta, self.df_Dis, self.df_Ang
        
    def GridAz( self, UtmFr, UtmTo ):
      dE = UtmTo.easting-UtmFr.easting
      dN = UtmTo.northing-UtmFr.northing
      az = np.arctan2( dE, dN )
      _,az = divmod( az, np.pi*2 )  # 2PI
      return np.degrees( az )

    def LineSF( self,StaFr,StaTo ):
        utm_mid = Utm( self.YAML['ZONE'], self.YAML['HEMI'],
                (StaFr.easting +StaTo.easting)/2,
                (StaFr.northing+StaTo.northing)/2  )
        sf_to  = StaTo.toLatLon().scale
        sf_mid = utm_mid.toLatLon().scale
        sf_fr  = StaFr.toLatLon().scale
        sf_line = (1/6)*(sf_fr+4*sf_mid+sf_to)  # quadratic mean
        #sf_line = (sf_fr+sf_to)/2  # average
        return sf_line

    def LineAC( self,StaFr,StaTo ):
        if 'ARC2CHORD' in self.YAML.keys() and self.YAML['ARC2CHORD'] is True:
            utm_mid = Utm( self.YAML['ZONE'], self.YAML['HEMI'],
                     (StaFr.easting+StaTo.easting)/2,
                        (StaFr.northing+StaTo.northing)/2  )
            rm = Ellipsoids.WGS84.rocGauss(utm_mid.toLatLon().lat)
            N2N1 = StaTo.northing-StaFr.northing
            E2E1 = (StaTo.easting-500_000) + 2*( StaFr.easting-500_000)
            del12 = np.degrees( N2N1*E2E1/(6*rm*rm) )
            return del12
        else:
            return 0.0

    def CloseTrav( self ):
        print('####### Adjust Interior Angles of the Close Traverse ########')
        self.JuncPnt = self.YAML['JUNCTION']
        df_JuncAng = self.df_Ang[self.df_Ang['Name'].str.contains( 
                                             f',{self.JuncPnt},' )]
        assert( len(df_JuncAng) == 2),\
           f"***ERROR*** {self.JuncPnt} must have 2 records in ANGL..."
        ##### partition open & close travesre #####
        df_AngCloTrv = self.df_Ang[ self.df_Ang.Name==df_JuncAng.iloc[1].Name ]
        nameAng = df_AngCloTrv.Name.str.split(',').to_list()
        nameAng = np.array( nameAng )
        idx = df_AngCloTrv.index.values.astype(int)[0]
        df_AngCloTrv = self.df_Ang.iloc[ idx: ]
        ##### angle correction due to angel excess #####
        sumAng = df_AngCloTrv.ang_deg.sum()
        sumAng_= 180*(len(df_AngCloTrv)-2)
        nAng = len( df_AngCloTrv )
        difAng = sumAng-sumAng_
        print(f'Close traverse number of angles : {nAng}')
        print(f'Close traverse angle excess (n-2)*180 : {difAng*3600:+.0f} sec.')
        self.df_Ang.loc[ idx:idx+nAng, 'ang_deg' ] = \
            self.df_Ang.loc[ idx:idx+nAng, 'ang_deg' ]-difAng/nAng  # ***ANG_ADJ***
        self.df_Ang.loc[ idx:idx+nAng, 'type' ] = 'closed'
        self.df_Ang['ang_dms'] = self.df_Ang['ang_deg'].apply( toDMS  )
        assert(np.isclose(self.df_Ang.iloc[idx:].ang_deg.sum(),sumAng_ )),"Not closed!"
        print('Close traverse sum of angels          : {:.7f} deg'.format( 
                                df_AngCloTrv.ang_deg.sum() ) )
        ##### merge junction angles #####
        jncAngSum = df_JuncAng.ang_deg.sum()
        jncAngNam = self.df_Ang.iloc[idx-1].Name+','+self.df_Ang.iloc[idx].Name
        jncAngNam = jncAngNam.split(',')
        assert( jncAngNam[1]==jncAngNam[4] or jncAngNam[2]==jncAngNam[3]),\
                      f'***ERROR*** cannot merge {jncAngNam}'
        jncAng = jncAngNam[0:2]+ [jncAngNam[-1],]
        jncAng = ",".join( jncAng )
        self.df_Ang.loc[ idx, ['Name', 'ang_deg', 'type' ] ] =\
                                       [jncAng,jncAngSum,'junction']
        self.df_Ang.drop( idx-1, axis='index', inplace=True )
        return
        
    def Clousure( self ):
        JPNT=trav.YAML['JUNCTION']
        jpnt  = df_Sta[df_Sta.Name==JPNT].iloc[0].Utm
        jpnt_ = df_Sta[df_Sta.Name==JPNT+'_'].iloc[0].Utm
        self.dE = jpnt.easting -jpnt_.easting
        self.dN = jpnt.northing-jpnt_.northing
        self.dJPNT = np.sqrt( self.dE*self.dE + self.dN*self.dN )

        print(f'Closure at junction {JPNT:6} : {self.dJPNT:+.3f} m.')
        self.idxJPNT =trav.df_Dis[trav.df_Dis.Name.str.startswith(f'{JPNT},')].iloc[-1].name
        self.sumTrv = trav.df_Dis.iloc[self.idxJPNT:].dist_m.sum()
        print(f'Sum of closed traverse      : {self.sumTrv:,.3f} m.')
        print(f'Linear closure              :  1: {self.sumTrv/self.dJPNT:,.0f} ')

    def AdjustCompassRule( self):
        dE= self.dE ;    dN=self.dN    ; dS=self.dJPNT
        df_DL = df_Dis.iloc[self.idxJPNT:].copy()
        df_DL.drop( columns=['ScalFac'], axis='index', inplace=True )
        #import pdb; pdb.set_trace() 
        df_DL['Dep'] = df_DL['dist_m']*np.sin(np.radians(df_DL['AdjAz']))
        df_DL['Lat'] = df_DL['dist_m']*np.cos(np.radians(df_DL['AdjAz']))
        sumDep = df_DL['Dep'].sum()
        sumLat = df_DL['Lat'].sum()
        sumDis = df_DL.dist_m.sum()
        df_DL['AdjDep'] = df_DL['Dep'] - sumDep*df_DL['dist_m']/sumDis
        df_DL['AdjLat'] = df_DL['Lat'] - sumLat*df_DL['dist_m']/sumDis
        df_DL_ = df_DL.copy()
        for col in ( 'Dep','Lat','AdjDep','AdjLat' ):
            df_DL_[col] = df_DL_[col].map('{:10.3f}'.format )
        print( df_DL_ )
        #import pdb; pdb.set_trace()
        sumAdjDep = df_DL['AdjDep'].sum()
        sumAdjLat = df_DL['AdjLat'].sum()
        print( f'sumDist={sumDis:.3f}m | sumDep={sumDep:+.3f}m sumLat={sumLat:+.3f}m | '\
               f'sumAdjDep={sumAdjDep:.3f}m sumAdjLat={sumAdjLat:.3f}m' )
        #####################################
        print( '=== Adjusted Coordiate by Compass Rule ===')
        print( '=Station=====Easting========Northing=====')
        FRutm = None
        for i,row in df_DL.iterrows():
            FR,TO = row.Name.split(',')
            if FRutm is None:
                FRutm = trav.df_Sta[ trav.df_Sta.Name==FR ].iloc[-1].Utm
                E,N = FRutm.easting, FRutm.northing
                print( f'{FR:6s} {E:15,.3f}  {N:15,.3f}' )
            E = E + row.AdjDep
            N = N + row.AdjLat
            print( f'{TO:6s} {E:15,.3f}  {N:15,.3f}' )

    def Plot(self, TITLE):
        df_Sta = self.df_Sta[self.df_Sta.Iter<=0]
        df_Dis = self.df_Dis[self.df_Dis.Iter==0]
        #import pdb; pdb.set_trace()
        for i,row in df_Sta.iterrows():
	        #print( i,row )
                if row.Iter==-1: ms = 20; fc='green'
                else:            ms = 10; fc='red'
                plt.plot( [row.Utm.easting], [row.Utm.northing],
                        marker="^", markersize=ms, mfc=fc, mec=fc )
                plt.text( row.Utm.easting,row.Utm.northing, row.Name )
        for i,row in df_Dis.iterrows():
	        #print( i, row )
	        FR,TO = row.Name.split(',')
	        fr = df_Sta[df_Sta.Name==FR].iloc[-1].Utm
	        to = df_Sta[df_Sta.Name==TO].iloc[-1].Utm
	        plt.plot( [fr.easting,to.easting] , [fr.northing,to.northing], '-r' )
        plt.ticklabel_format(useOffset = False, style = 'plain')
        plt.xticks(rotation=90)
        plt.gca().set_aspect("equal")
        plt.grid()
        plt.tight_layout()
        plt.title( TITLE )
        #plt.show()
        plt.savefig( TITLE )        

###########################################################
###########################################################
###########################################################
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

if len(sys.argv)==2:
    YAMLFILE = Path(sys.argv[1])
else:
    YAMLFILE = Path( './Dec17_Travese_Compute/P4_Trav.yaml' )
trav = UTMTraverse( YAMLFILE )
### Case closed traverse , adjust interior angles #########
if 'JUNCTION' in trav.YAML.keys():
    trav.CloseTrav()

###########################################################
for i in range(trav.YAML['ITER']):
    print(f'========================= Iter {i} ============================')
    df_Sta,df_Dis,df_Ang = trav.CalcTraverse(ITER=i)
trav.Clousure()
###########################################################
def _toUtmStr(row):
    if row.UTMSTR is None:
        return row.Utm.toStr(prec=-3)
    else:
        return row.UTMSTR
df_Sta['UTMSTR'] = df_Sta.apply( _toUtmStr, axis='columns' )
df_Dis['ScalFac'] = df_Dis['ScalFac'].map( '{:.9f}'.format )
if 1:
    print( df_Sta )
    print( df_Dis )
    print( df_Ang )
if trav.YAML['ITER']>=2:
    dE=list(); dN=list()
    for grp,row in df_Sta.groupby('Name'):
        MAX = row.Iter.max()
        if MAX==trav.YAML['ITER']-1:
            dE.append( row.iloc[MAX].Utm.easting- row.iloc[MAX-1].Utm.easting )
            dN.append( row.iloc[MAX].Utm.northing- row.iloc[MAX-1].Utm.northing )
    print( 'Converting@{} dE : {}'.format(trav.YAML['ITER'], np.array( dE ).round(3) ) )
    print( 'Converting@{} dN : {}'.format(trav.YAML['ITER'], np.array( dN ).round(3) ) )
for fmt in ('png','pdf','svg'):
    PLOT = f'./CACHE/{YAMLFILE.stem}.{fmt}'
    print( f'Plotting {PLOT}...') 
    trav.Plot( PLOT )
#trav.Plot( (YAMLFILE.stem + '.pdf' ) )
#############################################################
trav.AdjustCompassRule()
print( '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ End of UtmTrav.py @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@') 
#import pdb; pdb.set_trace()


