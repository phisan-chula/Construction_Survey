#
#
# Geod_netw : geodetic network solver by (lmfit) least square adjustment
#               computation The geodetic network could be intersection, 
#               resection and traverse.
#
#
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from lmfit import Minimizer, Parameters, report_fit
from pygeodesy.dms import toDMS, parseDMS
import sys
import pathlib
import yaml

def Az2PI ( FR_TO ):
    FR,TO = FR_TO
    return divmod( np.arctan2( TO[0]-FR[0] , TO[1]-FR[1] ), 2*np.pi )[1]
    
def Ang2PI( BS_STA_FS ):
    BS,STA,FS = BS_STA_FS
    azBS = Az2PI( [STA,BS] );  azFS = Az2PI( [STA,FS] )
    ang =  divmod( azFS-azBS,  2*np.pi )[1]
    return ang

#########################################################################
class TriangularAdj:
    def __init__(self, YAML):
        with open(YAML, mode='r') as f:
            self.YAML = yaml.safe_load( f )
        print( self.YAML.keys() ); print( self.YAML )
        #################################################################
        self.dfPNT = pd.DataFrame( self.YAML['PNT'].values(), 
                index=self.YAML['PNT'].keys(), columns=['X','Y'] )
        self.dfANG = pd.DataFrame( list(self.YAML['ANG'].values()) , 
                columns=[ 'BS','STA','FS', 'Ang_deg' ])

        if self.dfANG.dtypes['Ang_deg']=='object':  # "ddd:mm:ss.sss" 
            def ToRad( arg ):
                return np.radians( parseDMS( arg,sep=':') )
            self.dfANG['Ang_rad'] = self.dfANG['Ang_deg'].apply( ToRad )
        else:  # decimal degree format
            self.dfANG['Ang_rad'] = np.radians( self.dfANG['Ang_deg'] )
        #################################################################
        UNK_PAR = list()
        for pnt in list(self.YAML['UNK_PNT'].values()):
            for par in list(self.dfPNT.columns):
                UNK_PAR.append( [pnt, par, f'{pnt}_{par}' ] )
        self.dfPNT_PAR = pd.DataFrame( UNK_PAR, columns=['Pnt','Par', 'UnkPar'] )

    def DoAdjustCompu(self):
       # define objective function: returns the array to be minimized
        def fcn2min(params):
            # retriev lmfit/Parameter and update  self.dfPNT
            for idx,row in self.dfPNT_PAR.iterrows():
                self.dfPNT.loc[row.Pnt,row.Par] =params[row.UnkPar].value
            model = list()  # for each 'angle' observation
            for idx in range(len(self.dfANG)):
                pt3 = self.dfANG[['BS','STA','FS']].iloc[idx]
                BS_STA_FS = self.dfPNT.loc[pt3,['X','Y']].to_numpy().tolist()
                model.append( Ang2PI( BS_STA_FS ) )
            self.dfANG['Ang_model'] = model
            self.dfANG['model_data'] = self.dfANG['Ang_model'] - self.dfANG['Ang_rad']
            return self.dfANG['model_data']

        # reate a set of Parameters ; copy UNK_PNT from self.dfPNT to lmfit/Parameters()
        params = Parameters()
        for idx,row in self.dfPNT_PAR.iterrows():
            params.add(row.UnkPar, value=self.dfPNT.loc[row.Pnt][row.Par],vary=True )
        # do fit, here with the default leastsq algorithm
        minner = Minimizer(fcn2min, params )
        result = minner.minimize(  )
        return result

    def PlotNet(self, PLOTFILE=None ):
        dfPNT = self.dfPNT ; dfANG = self.dfANG
        plt.scatter( dfPNT.X, dfPNT.Y )
        for idx,row in dfPNT.iterrows():
            plt.text( row.X, row.Y, s=idx)
        for idx in range(len(dfANG)):
            pt3 = dfANG[['BS','STA','FS']].iloc[idx]
            xy = dfPNT.loc[pt3,['X','Y']].to_numpy()
            plt.plot( xy[:,0], xy[:,1])
        plt.gca().set_aspect('equal', adjustable='box')
        plt.title( PLOTFILE )
        if PLOTFILE is None:
            plt.show()
        else:
            plt.savefig(PLOTFILE)

######################################################################################
######################################################################################
######################################################################################
if __name__ == "__main__":
    if len(sys.argv)==1:
        #YAML = 'Intersect_Fix3Ang4.yaml'
        YAML = 'Resect_Fix3Ang2.yaml'
    else:
        YAML = sys.argv[1]
    TA = TriangularAdj(YAML)
    STEM = pathlib.Path( YAML ).stem
    PLOTFILE = f'./CACHE/Plot_{STEM}.png'

    ####################################################################################
    res = TA.DoAdjustCompu( )
    print( report_fit(res) )
    print('Parameter    Value       Stderr')
    for name, param in res.params.items():
        if param.stderr is None:
            param.stderr=0.0
        print(f'{name:7s} {param.value:11.5f} {param.stderr:11.5f}')
    print( 'Residual (radian): \n', res.residual )
    print( 'Residual (arc-second): \n', np.degrees(res.residual)*3600 )
    TA.PlotNet( PLOTFILE )
