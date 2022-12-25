#
#
PROG='''
 CurvePnts.py : Generate points on a designated curve 
                from its 3-point alignment 
 Author : Phisan Santitamnont ( phisan.chula@gmail.com )
 History  25 Dec 2022 : version 0.1 
        

'''
import numpy as np 
import pandas as pd
import geopandas as gpd
from skspatial.objects import Vector
from shapely.geometry import LineString,Point
from shapely.affinity import translate, rotate
from pathlib import Path
import matplotlib.pyplot as plt
from pygeodesy import dms
from fiona.drvsupport import supported_drivers
supported_drivers['LIBKML'] = 'rw'

class CircularCurve:
    def __init__(self, CURVE_DATA,DIV=50 ):
        self.CACHE = Path( './CACHE' )
        print(f'Wrinting result "csv|pdf|png|gpkg" into ./{self.CACHE}/...')
        self.CACHE.mkdir(parents=True, exist_ok=True)
        self.LS_ALIGN, self.RADIUS = CURVE_DATA
        self.DIV = DIV
        assert( len(self.LS_ALIGN.coords) ==3 ),'***ERROR*** limit 3 points on LS_ALIGN'
        pc,pi,pt = list(self.LS_ALIGN.coords)
        vcPC = Vector.from_points( pc,pi )
        vcPI = Vector.from_points( pi,pt )
        self.sgDEFLEC = vcPI.angle_signed( vcPC )
        self.DEFLEC = abs( self.sgDEFLEC )
        self.dmsDEFL = dms.toDMS( np.degrees(self.sgDEFLEC), prec=1 )
        print( f'Deflection angle : {np.degrees(self.sgDEFLEC)} ...' )
        print( f'Deflection angle : {self.dmsDEFL} ...' )
        self.GenerateNormArc()
        lsR3 = self.RotTransNormArc()
        LS_POC = LineString( list(self.dfPnt.iloc[4:].geometry) )
        self.dfLS = gpd.GeoDataFrame( {'Type': ['Alignment', 'POC', 'O_PC', 'O_M', 'O_PT'] },
                     crs='EPSG:32647', geometry=([self.LS_ALIGN,LS_POC]+lsR3) ) 

    def GenerateNormArc(self):
        self.T = self.RADIUS*np.tan( self.DEFLEC/2 )
        self.POC = self.RADIUS*self.DEFLEC
        pc,pi,pt = list(self.LS_ALIGN.coords)
        pi_pc = LineString( [pi,pc] ).length; assert( pi_pc>=self.T ),'***ERROR** leadin PC too shore!'
        pi_pt = LineString( [pi,pt] ).length; assert( pi_pt>=self.T ),'***ERROR** leadout PT too shore!'
        print( f'Tangential Dist  : {self.T:.3f} m.' )
        print( f'Point On Curve : {self.POC:.3f} m.' )
        ndiv,rest = divmod(self.POC, self.DIV)
        pnt_div = np.linspace(rest/2,self.POC-rest/2,num=int(ndiv)+1,endpoint=True )
        pnts = np.concatenate( [np.array([0]), pnt_div, np.array([self.POC]) ] )
        dfPOC = pd.DataFrame( pnts, columns=['cvDist'] )
        def DoCurve(row, self):
            theta = row.cvDist/self.RADIUS
            x,y = self.RADIUS*np.sin(theta),self.RADIUS*np.cos(theta)
            if self.sgDEFLEC < 0.: y=-y
            return [ f'{row.cvDist:03.0f}', Point(x,y) ]
        dfPOC[['Name','geometry']] = dfPOC.apply( DoCurve, 
                axis=1, result_type='expand', args=(self,) )
        ############################################
        PC = LineString( [ pi,pc ]).interpolate( self.T, normalized=False )
        PT = LineString( [ pi,pt ]).interpolate( self.T, normalized=False )
        dfPnt = pd.DataFrame( [ [0., 'PC', PC], [0., 'PI', Point(pi)], [0., 'PT', PT ],
                  [0., 'O',  Point([0,0]) ] ], columns=['cvDist','Name', 'geometry' ] )
        self.dfPnt = pd.concat( [ dfPnt, dfPOC ], ignore_index=True )

    def RotTransNormArc(self):
        pPC  = self.dfPnt[self.dfPnt['Name']=='PC'].iloc[0].geometry
        pPI  = self.dfPnt[self.dfPnt['Name']=='PI'].iloc[0].geometry
        pPT  = self.dfPnt[self.dfPnt['Name']=='PT'].iloc[0].geometry
        p00  = self.dfPnt[self.dfPnt['Name']=='000'].iloc[0].geometry
        dx,dy = pPC.x-p00.x, pPC.y-p00.y
        PC_PI = Vector.from_points(list(pPC.coords[0]) ,list(pPI.coords[0]) )
        sgRot = Vector([1,0]).angle_signed( PC_PI )
        def RotTr(row,dx,dy,sgRot,pntPC):
            if row['Name'] in ['PC','PI','PT']:   
                return row.geometry
            else:    # point-on-curve and 'O' will be translated and rotated!
                x,y   = row.geometry.x, row.geometry.y
                x_,y_ = x+dx , y+dy
                return rotate( Point( x_,y_),sgRot, origin=(pntPC.x,pntPC.y), use_radians=True ) 
        self.dfPnt['geometry'] = self.dfPnt.apply( RotTr, axis=1, 
                            result_type='expand', args=( dx,dy,sgRot,pPC ) )
        self.dfPnt = gpd.GeoDataFrame( self.dfPnt, crs='EPSG:32647', 
                            geometry=self.dfPnt.geometry )
        ############## all rotated and translated ##################
        pO  = self.dfPnt[self.dfPnt['Name']=='O'].iloc[0].geometry
        pM  = LineString( [pO,pPI] ).interpolate( self.RADIUS, normalized=False )
        return [ LineString([pO,pPC]), LineString([pO,pM]) , LineString([pO,pPT]) ]

    def DoPlot(self, POC_TEXT=True):
        fig, ax = plt.subplots( figsize=(20,18))
        self.dfLS.plot( ax=ax ) 
        for i,row in self.dfPnt.iloc[4:].iterrows(): 
            x =  row.geometry.x ; y =  row.geometry.y
            ax.scatter( x, y, c='k', s=30, alpha=0.5 )
            if POC_TEXT:
                ax.text( x,y, s=row['Name'], c='g', fontsize=15 )
        for i,row in self.dfPnt.iloc[0:4].iterrows(): 
            x =  row.geometry.x ; y =  row.geometry.y
            ax.scatter( x, y, c='r', s=50 )
            ax.text( x,y, s=row['Name'], c='r', fontsize=20 )
        C_DATA = f'R = {self.RADIUS} m.\n\u03B4 = {self.dmsDEFL}\n'\
                 f'POC = {self.POC:.3f} m.\nTangential (T) = {self.T:.3f} m\n'\
                 f'Division: {self.DIV} m.'
        om = self.dfLS[self.dfLS.Type=='O_M'].iloc[0].geometry.centroid
        ax.text( om.x,om.y,s=C_DATA,c='r',fontsize=15, ha='center', va='center' )
        ax.tick_params(axis='x', rotation=90)
        ax.ticklabel_format( useOffset=False, style='plain' )
        plt.gca().set_aspect('equal')
        plt.grid()
        plt.savefig( self.CACHE.joinpath( 'PLOT_CURVE.png' ) )
        plt.savefig( self.CACHE.joinpath( 'PLOT_CURVE.pdf' ) )

    def WriteCurve( self ):
        self.dfPnt.iloc[0:4].to_file( self.CACHE.joinpath('Plot_Curve.gpkg'), 
                                                driver='GPKG', layer='CurveDef'  ) 
        self.dfPnt.iloc[4: ].to_file( self.CACHE.joinpath( 'Plot_Curve.gpkg'), 
                                                driver='GPKG', layer='PointOnCurve' ) 
        self.dfLS.to_file( self.CACHE.joinpath('Plot_Curve.gpkg'), 
                                                driver='GPKG', layer='Line' ) 
        pnt = self.dfPnt.copy()
        def fmtCSV(row, self):
            E = '{:.3f}'.format( row.geometry.x)
            N = '{:.3f}'.format( row.geometry.y)
            strCode = 'STN' if row.name<4 else 'PT'
            return [row.name ,E,N,0.0, strCode, row.Name ]
        TOPCON_GTS7 = ['ptno','E','N','Z', 'ptcode', 'ptstr']
        pnt[TOPCON_GTS7] = pnt.apply( fmtCSV, axis=1, result_type='expand', args=( self, ) ) 
        pnt[TOPCON_GTS7].to_csv( self.CACHE.joinpath('GTS7_Curve.csv'),header=False, index=False )
        #import pdb ; pdb.set_trace()

###############################################################################
###############################################################################
###############################################################################
USAGE = '''python3 CurvePnts.py -a [542939.592,1560557.148],[543219.123,1560612.552],[543408.493,1560534.688] -r 200 -d 20'''
###############################################################################
###############################################################################
###############################################################################
xCURVE = LineString( [ [0,0],[0,1000],[-1000,2000] ] ), 1200 # PC-PI-PT, Radius
xCURVE = LineString( [ [0,0],[0,1000],[1000,2000] ] ), 1200 # PC-PI-PT, Radius
xCURVE = LineString( [ [0,0],[1000,0],[2000,-1000] ] ), 1200 # PC-PI-PT, Radius
xCURVE = LineString( [ [0,2000],[0,0],[2000,0] ] ), 1200 # PC-PI-PT, Radius
xCURVE = LineString( [ [2000,0],[0,0],[0,2000] ] ), 1200 # PC-PI-PT, Radius
xCURVE = LineString( [ [2000,-300],[0,0],[0,2000] ] ), 1200 # PC-PI-PT, Radius
xCURVE = LineString( [ [0,0],[1000,0],[1800,-1000] ] ), 500 # PC-PI-PT, Radius
xCURVE = LineString( [ [542939.592,1560557.148],[543219.123,1560612.552],
                      [543408.493,1560534.688] ] ), 200 # PC-PI-PT, Radius
import argparse
parser = argparse.ArgumentParser(description=PROG,usage=USAGE )
parser.add_argument( '-a','--align', action='store',             
            help='3-point of alignment "[E,N],[E,N],[E,N]" for circular curve design' )
parser.add_argument( '-r','--radius', action='store',
            help='design value of the radius in meter' )
parser.add_argument( '-d','--division', action='store',
            help='desired division of the point-on-curve in meter' )
parser.add_argument( '-t','-t', action='store_true',
            help='annotate text for curve distance at each division')
args = parser.parse_args()

P3 = np.array( eval(args.align) ).tolist()
RADIUS = float(args.radius)
CURVE = [ LineString(P3), RADIUS ]
DIV = float(args.division)
cc = CircularCurve( CURVE, DIV=DIV )
#cc.DoPlot( POC_TEXT=True )
cc.DoPlot( POC_TEXT=False )
print( cc.dfPnt )
cc.WriteCurve()
print('@@@@@@@@@@@@@@@@@ end of  CurvePnt @@@@@@@@@@@@@@@@@@@@')
#import pdb; pdb.set_trace()
