#
#
# SurveyFund : surveying fundamental software
# P.Santitamnont, Chulalongkorn University
#
#
import pygeodesy as pgd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def dd2DMS( dd, PREC=1, POS=''  ):
    '''conver degree to DMS string'''
    return pgd.dms.toDMS( dd, prec=PREC,pos=POS )

def rad2DMS( rad, PREC=1, POS='' ):
    '''conver radian to DMS string'''
    return pgd.dms.toDMS( np.degrees(rad), prec=PREC, pos=POS )

class Angular:
    def __init__( self, value  ):
        pass

    def __str__(self):
        return pgd.dms.toDMS( np.degrees(self.rad), prec=1, pos='' )

class Radian( Angular ):
    def __init__( self, value ):
        self.TYPE = 'RAD'
        self.rad = value
        self.deg = np.degrees(value)

class Degree( Angular ): 
    TYPE = ['DD','DMS59']
    def __init__( self, value, TYPE='DD' ):
        assert( TYPE in self.TYPE )
        if TYPE=='DMS59':
            value = self.DMS2dd( value ) 
        elif TYPE=='DD':
            pass
        self.deg = value
        self.rad = np.radians(value)
        pass

    def DMS2dd(self, ddmmss ):
        ''' convert string or float DD.MMSS from total station 
            to decimal degree. Format DD.MMSS is often used by TS '''
        if type(ddmmss) is not str:
            ddmmss = f'{ddmmss:f}'    
        dms = ddmmss.split('.')
        d = float( dms[0] )
        SIGN = +1. if d>0.0 else -1.
        m = SIGN*float( dms[1][0:2])/60
        s = SIGN*float( dms[1][2:4])/3600
        return d+m+s

class GeodPnt:
    def __init__( self, NAME:str, EAST, NORTH, HEIGHT, HInst=0. ):
        self.NAME = NAME
        self.E = EAST; self.N = NORTH; self.H = HEIGHT
        self.HI = HInst

    def AngCW( self, dirBS:Angular, dirFS:Angular):
        self.dirBS = dirBS ; self.dirFS = dirFS
        ang_deg = divmod( dirFS.deg-dirBS.deg , 360 )[1]   # angle 0...360 deg
        self.Ang = Degree( ang_deg )
        return self.Ang 

    def PlotAngCW(self):
        #import pdb ; pdb.set_trace()
        fig,ax = plt.subplots()
        for BSFS,dir_ in (('BS',self.dirBS),('FS',self.dirFS)) :
            dx = np.sin(dir_.rad); dy = np.cos(dir_.rad)
            LINE = 'ro-' if BSFS=='BS' else 'go-'
            ax.plot( [0,dx], [0,dy], LINE, linewidth=2 ) 
            ax.text( dx,dy, f'({BSFS}) {dir_.deg:.1f}' )
        dir_mid = (self.dirBS.rad + self.Ang.rad/2)
        dx = 0.3*np.sin( dir_mid )
        dy = 0.3*np.cos( dir_mid )
        ax.annotate( f'{self.Ang.deg:0.1f}', xy=(0,0) , xycoords='data',
                xytext=(dx,dy), textcoords='data',
                arrowprops=dict(arrowstyle="->",
                                connectionstyle="arc3,rad=.2"))
        #import pdb ; pdb.set_trace()
        ax.set_xlim( -1, +1 ); ax.set_ylim( -1, +1 )
        ax.set_aspect('equal', 'box')
        ax.xaxis.set_ticklabels([]); ax.yaxis.set_ticklabels([])
        ax.grid()
        plt.title( 'Clock-wise angle' )
        plt.savefig( f'CACHE/{self.dirBS.deg:05.1f}_{self.dirFS.deg:05.1f}'\
                      f'_{self.Ang.deg:05.1f}.png' )  
        plt.clf(); plt.close()

#class Traverse:
#    def __init__(self, FrPnt, ToPnt):
#     #init__( self, NAME:str, EAST, NORTH, HEIGHT, HInst=0. ):
#        dE = ToPnt.E-FrPnt.E
#        dN = ToPnt.N-FrPnt.N
#
#    def SS_to( self )
#        return

####################################################################
if __name__=="__main__":
    for ang in ( '123.4512', 123.4512 , '-123.4512', -123.4512 ):
        ang = Degree( ang , TYPE='DMS59' )
        print( ang )

    #############################################
    import random 
    random.seed( 999 )

    print(70*'=')
    dir_bs = random.sample( range(0,360,10), 36 )
    dir_fs = random.sample( range(0,360,10), 36 )
    Apnt = GeodPnt( "TEST" , 100,500,100, 0.0)
    for bs,fs in list(zip( dir_bs,dir_fs )):
        #bs = Degree( bs ); fs=Degree( fs )
        bs = Radian( np.radians(bs) ); fs=Radian( np.radians(fs) )
        ang = Apnt.AngCW( bs,fs )
        Apnt.PlotAngCW()
        print( f'BS={bs}  FS={fs}  AngCW= {ang}' )
    #import pdb ; pdb.set_trace()


