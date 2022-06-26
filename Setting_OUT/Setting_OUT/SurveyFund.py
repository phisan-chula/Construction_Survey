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

####################################################################
def dd2DMS( dd, PREC=1, POS=''  ):
    '''conver degree to DMS string'''
    return pgd.dms.toDMS( dd, prec=PREC,pos=POS )
def rad2DMS( rad, PREC=1, POS='' ):
    '''conver radian to DMS string'''
    return pgd.dms.toDMS( np.degrees(rad), prec=PREC, pos=POS )
####################################################################
class Angular:
    def __init__( self, value  ):
        pass
    def __str__(self):
        return pgd.dms.toDMS( np.degrees(self.rad),
                              prec=self.PREC, pos='' )
####################################################################
class Radian( Angular ):
    def __init__( self, value, PRECISION=1 ):
        self.TYPE = 'RAD'
        self.rad = value
        self.deg = np.degrees(value)
        self.PREC = PRECISION
####################################################################
class Degree( Angular ): 
    TYPE = ['DD','DMS59']
    def __init__( self, value, TYPE='DD', PRECISION=1 ):
        assert( TYPE in self.TYPE )
        if TYPE=='DMS59':
            value = self.DMS59dd( value ) 
        self.deg = value
        self.rad = np.radians(value)
        self.PREC = PRECISION

    def DMS59dd(self, ddmmss ):
        ''' convert string or float DD.MMSS from total station 
            to decimal degree. Format DD.MMSS is often used by TS '''
        #import pdb; pdb.set_trace()
        SIGN = +1. if float(ddmmss)>=0.0 else -1.
        if type(ddmmss) is not str:
            ddmmss = f'{ddmmss:f}'    
        dms = ddmmss.split('.')
        d = float( dms[0] )
        m = SIGN*float(dms[1][0:2])/60
        s = SIGN*float(dms[1][2:])/100./3600
        return d+m+s
####################################################################
class GeodPnt:
    def __init__( self, NAME:str, EAST=0, NORTH=0, HEIGHT=0, HInst=0. ):
        self.NAME = NAME
        self.E = EAST; self.N = NORTH; self.H = HEIGHT
        self.HI = HInst
    def __str__( self ):
        return f'"{self.NAME}" E:{self.E:.3f}m N:{self.N:.3f}m'\
                f' H:{self.H:.3f}m HI={self.HI:.2f}m' 
    def AngCW( self, dirBS:Angular, dirFS:Angular):
        self.dirBS = dirBS ; self.dirFS = dirFS
        ang_deg = divmod( dirFS.deg-dirBS.deg,360 )[1]   # angle 0...360 deg
        self.Ang = Degree( ang_deg )
        return self.Ang 
    def PlotAngCW(self):
        fig,ax = plt.subplots()
        for BSFS,dir_ in (('BS',self.dirBS),('FS',self.dirFS)) :
            dx = np.sin(dir_.rad); dy = np.cos(dir_.rad)
            LINE = 'ro-' if BSFS=='BS' else 'go-'
            ax.plot( [0,dx], [0,dy], LINE, linewidth=2 ) 
            ax.text( dx,dy, f'({BSFS}) {dir_.deg:.1f}' )
        dir_mid = (self.dirBS.rad + self.Ang.rad/2)
        dx = 0.3*np.sin( dir_mid )
        dy = 0.3*np.cos( dir_mid )
        #import pdb ; pdb.set_trace()
        ax.annotate( f'{self.Ang.deg:0.1f}', xy=(0,0) , xycoords='data',
                xytext=(dx,dy), textcoords='data',
                arrowprops=dict(arrowstyle="->",
                                connectionstyle="arc3,rad=.2"))
        ax.set_xlim( -1, +1 ); ax.set_ylim( -1, +1 )
        ax.set_aspect('equal', 'box')
        ax.xaxis.set_ticklabels([]); ax.yaxis.set_ticklabels([])
        ax.grid()
        plt.title( 'Clock-wise angle' )
        plt.savefig( f'CACHE/{self.dirBS.deg:05.1f}_{self.dirFS.deg:05.1f}'\
                      f'_{self.Ang.deg:05.1f}.png' )  
        plt.clf(); plt.close()
######################################################################
class Traverse:
    def __init__(self, PntSTA, PntBS):
        self.PntSTA = PntSTA ;  self.PntBS = PntBS
        az = np.arctan2( PntBS.N-PntSTA.N ,PntBS.E-PntSTA.E)
        try:
            self.AziBS = Radian( divmod( az, 2*np.pi )[1] )
        except:
            import pdb ; pdb.set_trace()

    def PathTo( self, NAME_TO:str, AngCW:Angular, SlopDist:float, 
            AngZ=Degree(90), HTarget=0.0 ):
        self.AngCW = AngCW
        AziFS = Degree( divmod( self.AziBS.deg + AngCW.deg, 360 )[1] )
        E = self.PntSTA.E + np.sin( AziFS.rad )*SlopDist 
        N = self.PntSTA.N + np.cos( AziFS.rad )*SlopDist 
        H = self.PntSTA.H + self.PntSTA.HI + \
                SlopDist*np.cos( AngZ.rad ) - HTarget 
        self.PntFS = GeodPnt( NAME_TO, EAST=E, NORTH=N, HEIGHT=H , HInst=0 ) 
        return self.PntFS

    def PlotPathTo( self, PREFIX ):
        fig,ax = plt.subplots( nrows=1, ncols=1, figsize=(12,8) )
        def PlotPntTxt( Pnt, s=30, c='red', ):
            ax.scatter( [Pnt.E,],[Pnt.N,], s, c, marker='^' )
            ax.text( Pnt.E, Pnt.N , Pnt.NAME, color=c )
        def PlotLineTxt( PntA, PntB, s=30, c='red', ):
            ax.plot( [PntA.E,PntB.E], [PntA.N,PntB.N] )
        PlotPntTxt( self.PntSTA ); PlotPntTxt( self.PntBS )
        PlotPntTxt( self.PntFS )
        PlotLineTxt( self.PntSTA, self.PntBS )
        PlotLineTxt( self.PntSTA, self.PntFS )
        dir_mid = self.AziBS.rad + self.AngCW.rad/2.
        dx = self.PntSTA.E + 20*np.sin( dir_mid )
        dy = self.PntSTA.N + 20*np.cos( dir_mid )
        ax.annotate( f'{str(self.AngCW)}', 
                xy=(self.PntSTA.E,self.PntSTA.N) , xycoords='data',
           xytext=(dx,dy), textcoords='data',
           arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))
        ax.set_aspect('equal', 'box')
        ax.ticklabel_format(useOffset=False,style='plain')
        ax.tick_params(axis='x', rotation=90)
        ax.grid()
        PLT = f'CACHE/{PREFIX}_{self.PntSTA.NAME}_{self.PntBS.NAME}_{self.PntFS.NAME}.png'
        print( f'Plotting {PLT}...')
        plt.savefig( PLT )

####################################################################
if __name__=="__main__":
    for ang in ( '123.4512', 123.4512 , '-123.4512', -123.4512 ):
        ang = Degree( ang , TYPE='DMS59' )
        print( ang )
    if 0:
        import random ; random.seed( 888 )
        print(70*'=')
        dir_bs = random.sample( range(0,360,10), 36 )
        dir_fs = random.sample( range(0,360,10), 36 )
        Apnt = GeodPnt( "TEST" , 100,500,100, 0.0)
        for bs,fs in list(zip( dir_bs,dir_fs )):
            bs = Degree( bs ); fs=Degree( fs )
            #bs = Radian( np.radians(bs) ); fs=Radian( np.radians(fs) )
            ang = Apnt.AngCW( bs,fs )
            Apnt.PlotAngCW()
            print( f'BS={bs}  FS={fs}  AngCW= {ang}' )

    #############################################
    PntA = GeodPnt( "A" , 5_000_000, 1_500_000 )
    PntB = GeodPnt( "B" , 5_000_100, 1_500_100 )
    trv = Traverse( PntA, PntB)
    ss = trv.PathTo( "C" , Degree(100), 50.00  )
    print( ss ) 
    trv.PlotPathTo( 'Testing' )
    #import pdb ; pdb.set_trace()


