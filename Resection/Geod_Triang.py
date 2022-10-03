#
#
# Geod_Triang : geodetic triangle solver
#
#
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from lmfit import Minimizer, Parameters, report_fit
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

def PlotRESECT( dfPNT, dfANG, PLOTFILE ):
    plt.scatter( dfPNT.X, dfPNT.Y )
    for idx,row in dfPNT.iterrows():
        plt.text( row.X, row.Y, s=idx)
    for idx in range(len(dfANG)):
        #import pdb ; pdb.set_trace()
        pt3 = dfANG[['BS','STA','FS']].iloc[idx]
        xy = dfPNT.loc[pt3,['X','Y']].to_numpy()
        plt.plot( xy[:,0], xy[:,1])
    plt.gca().set_aspect('equal', adjustable='box')
    plt.title( PLOTFILE )
    plt.savefig(PLOTFILE)
    #plt.show()

def DoAdjustCompu():
   # define objective function: returns the array to be minimized
    def fcn2min(params):
        # retriev lmfit/Parameter and update pandas dfPNT
        PNT_COLUMNS = list(dfPNT.columns)
        for k,pnt in YAML['UNK_PNT'].items():
            val = list()
            for col in PNT_COLUMNS: 
                val.append( params[ f'{pnt}_{col}'].value )   
            dfPNT.loc[pnt,PNT_COLUMNS] =  val
        model = list()
        # for each 'angle' observation
        for idx in range(len(dfANG)):
            pt3 = dfANG[['BS','STA','FS']].iloc[idx]
            BS_STA_FS = dfPNT.loc[pt3,['X','Y']].to_numpy().tolist()
            model.append( Ang2PI( BS_STA_FS ) )
        dfANG['Ang_model'] = model
        dfANG['model_data'] = dfANG['Ang_model'] - dfANG['Ang_rad']        
        #import pdb ;pdb.set_trace()
        return dfANG['model_data']

    # create a set of Parameters ; copy UNK_PNT from dfPNT to lmfit/Parameters()
    params = Parameters()
    PNT_COLUMNS = list(dfPNT.columns)
    for k,pnt in YAML['UNK_PNT'].items():
        val = list()
        for col in PNT_COLUMNS: 
            params.add(f'{pnt}_{col}', value=dfPNT.loc[pnt][col], vary=True )
    # do fit, here with the default leastsq algorithm
    minner = Minimizer(fcn2min, params )
    result = minner.minimize(  )
    # write error report
    print( report_fit(result) )
 
    print('Parameter    Value       Stderr')
    for name, param in result.params.items():
        if param.stderr is None:
            param.stderr=0.0
        print(f'{name:7s} {param.value:11.5f} {param.stderr:11.5f}')
    print( 'Residual (radian): \n', result.residual )
    print( 'Residual (arc-second): \n', np.degrees(result.residual)*3600 )

######################################################################################
######################################################################################
######################################################################################
if __name__ == "__main__":
    if len(sys.argv)==1:
        #YAML = 'Intersect_Fix3Ang4.yaml'
        YAML = 'Resect_Fix3Ang2.yaml'
    else:
        YAML = sys.argv[1]
    STEM = pathlib.Path( YAML ).stem
    PLOTFILE = f'./CACHE/Plot_{STEM}.png'
    with open(YAML, mode='r') as f:
        YAML = yaml.safe_load( f )
    print( YAML.keys() )
    print( YAML )

    ####################################################################################
    dfPNT = pd.DataFrame( YAML['PNT'].values(), index=YAML['PNT'].keys(), columns=['X','Y'] )
    dfANG = pd.DataFrame( list(YAML['ANG'].values()) , columns=[ 'BS','STA','FS', 'Ang_deg' ])
    dfANG['Ang_rad'] = np.radians( dfANG['Ang_deg'] )
    #import pdb; pdb.set_trace()

    ####################################################################################
    PlotRESECT( dfPNT, dfANG, PLOTFILE )
    DoAdjustCompu()
    PlotRESECT( dfPNT, dfANG, PLOTFILE )
