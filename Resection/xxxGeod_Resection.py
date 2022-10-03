import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from lmfit import Minimizer, Parameters, report_fit

def Az2PI ( FR_TO ):
    FR,TO = FR_TO
    return divmod( np.arctan2( TO[0]-FR[0] , TO[1]-FR[1] ), 2*np.pi )[1]
    
def Ang2PI( BS_STA_FS ):
    BS,STA,FS = BS_STA_FS
    azBS = Az2PI( [STA,BS] );  azFS = Az2PI( [STA,FS] )
    return divmod( azFS-azBS,  2*np.pi )[1]

def Plot( dfPNT, dfANG ):
    plt.scatter( dfPNT.X, dfPNT.Y )
    for idx,row in dfPNT.iterrows():
        plt.text( row.X, row.Y, s=idx)
    for idx in range(len(dfANG)):
      #import pdb ; pdb.set_trace()
      pt3 = dfANG[['BS','STA','FS']].iloc[idx]
      xy = dfPNT.loc[pt3,['X','Y']].to_numpy()
      plt.plot( xy[:,0], xy[:,1])
    plt.gca().set_aspect('equal', adjustable='box')
    plt.savefig('PlotResect.png')
    #plt.show()

def main():
    ####################################################################################
    PNT = [ ('PX', 100.0, 0.0 ) , ('P1', 0.000, 0.000) ,
            ('P2',  0.000, 100.000), ('P3', 100.000, 100.000),
            ('P4',  0.0,    50.0) ]
    dfPNT= pd.DataFrame( PNT , columns = ['STA', 'X','Y'] )
    dfPNT.set_index('STA', inplace=True)

    ANG = [ ['P1','PX','P2',45.0], ['P2','PX','P3',45.0], ['P4','PX', 'P1', 26.56505118 ] ]
    dfANG = pd.DataFrame( ANG, columns=[ 'BS','STA','FS', 'Ang_deg' ])
    dfANG['Ang_rad'] = np.radians( dfANG['Ang_deg'] )
    #import pdb; pdb.set_trace()
    Plot( dfPNT, dfANG )
    ####################################################################################
    # define objective function: returns the array to be minimized
    def fcn2min(params):
        """Model a decaying sine wave and subtract data."""
        xySTA = [params['PX_X'].value, params['PX_Y'].value]
        model = list()
        for idx in range(len(dfANG)):
            pt3 = dfANG[['BS','STA','FS']].iloc[idx]
            xy = dfPNT.loc[pt3,['X','Y']].to_numpy()
            xyBS = xy[0].tolist(); xyFS = xy[2].tolist()
            #import pdb ;pdb.set_trace()
            model.append( Ang2PI( [xyBS,xySTA,xyFS]) )
        dfANG['Ang_model'] = model
        def DiffAng(row):
            return divmod( row.Ang_model-row.Ang_rad, 2*np.pi )[1]
        dfANG['model_data'] = dfANG.apply( DiffAng, axis=1, result_type='expand' )
        return dfANG['model_data']

    # create a set of Parameters
    params = Parameters()
    params.add('PX_X', value=dfPNT.loc['PX'].X)
    params.add('PX_Y', value=dfPNT.loc['PX'].Y)
    # do fit, here with the default leastsq algorithm
    minner = Minimizer(fcn2min, params )
    result = minner.minimize()
    # write error report
    print( report_fit(result) )
 
    print('Parameter    Value       Stderr')
    for name, param in result.params.items():
        print(f'{name:7s} {param.value:11.5f} {param.stderr:11.5f}')
    #import pdb ; pdb.set_trace()
    print( 'Residual (arc-second): \n', np.degrees(result.residual)*3600 )
    #print( np.degrees((result.residual) )*3600 )


if __name__ == "__main__":
    main()
