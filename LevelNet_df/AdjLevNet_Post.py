PROG ="""
########################################################
2_AdjLevNet_Post : Adjustment Computation of Levelling Network
                   Part-2 Post-Analysis
P.Santitamnont ( phisan.chula@gmail.com)
Faculty of Engineering, Chulalongkorn University
v. 1.0  Initial                        20 May 2017
v. 1.1  Read YAML format               13 Oct 2018
v. 1.2  Q/C and double-run handling    23 Feb 2019
v. 2.0  refractoring to Pandas          3 Feb 2021
#######################################################
"""
import sys,pickle
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, LineString
gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
sys.path.append('/home/phisan/Dev')
from Plot_Pnt_KML import *
from AdjLevNet import *
from tabulate import tabulate

##############################################################
def Report_Double_Run():
    clo_KM_mm = df_Net['W4_CloKM_mm'] # mm per sqrt(km)
    for i in df_Diff.index:
        div,mod = divmod( i, 2)
        if mod: # modulus=1
            fwd = df_Diff.iloc[i-1]
            bwd = df_Diff.iloc[i]
            if fwd.From==bwd.To and fwd.To==bwd.From : 
                fwdname = '{}<>{}'.format( fwd.From, fwd.To )
                bwdname = '{}<>{}'.format( bwd.From, bwd.To )
                df_Diff.at[i-1,'DblRun'] = fwdname 
                df_Diff.at[i  ,'DblRun'] = bwdname 
                df_Diff.at[i-1,'DblDiff_m'] = (fwd.Diff_m+(-bwd.Diff_m))/2 
                df_Diff.at[i-1,'DblClos_mm'] =\
                               1000*abs(abs(fwd.Diff_m)-abs(bwd.Diff_m))
                Avg_Dist_km = (fwd.Dist_km+bwd.Dist_km)/2
                df_Diff.at[i-1,'DblDist_km'] =  Avg_Dist_km
                df_Diff.at[i-1,'Allow_Clo_mm'] = \
                                        clo_KM_mm*np.sqrt( Avg_Dist_km ) 
            else:
                print( fwd , '\n'  , bwd )
                import pdb; pdb.set_trace()
                raise '***ERROR*** try to find its DUO double-run'
    def W4( row ):
        if abs(row.DblClos_mm)>row.Allow_Clo_mm : return '*'
    df_Diff['W4'] = df_Diff.apply( W4, axis='columns' ) 
    print(H(' double run statistics '))
    stats = list()
    for col in [ 'DblDiff_m', 'DblClos_mm' , 'DblDist_km' ]:
        stats.append( df_Diff[col].describe() )
    print( pd.concat( stats, axis=1) )

##############################################################
def MergeDblLine(df_Diff, gdf_BM):
    _result = pd.merge( df_Diff, gdf_BM , how='left', 
                        left_on='From', right_on='Name', copy=True )
    df_merge = pd.merge( _result, gdf_BM , how='left', 
                         left_on='To', right_on='Name', 
                         suffixes=('_Fr','_To'), copy=True )
    if 0:
        print(H(' FROM-points have no geometry and missing ... '))
        print( TABLE_POINT(df_merge[df_merge.Name_Fr.isnull()].From.to_list()))
        #import pdb; pdb.set_trace()
        print(H(' TO-points have no geometry and missing ... '))
        print( TABLE_POINT(df_merge[df_merge.Name_To.isnull()].To.to_list()))

    df_fr = ~df_merge.geometry_Fr.isnull()
    df_to = ~df_merge.geometry_To.isnull()
    df_line = df_merge[ df_fr & df_to ].copy()
    def two_pnt(row):
        return LineString( [ row.geometry_Fr, row.geometry_To ] )
    df_line['geometry'] = df_line.apply( two_pnt, axis='columns' )
    df_line = gpd.GeoDataFrame( df_line, crs='EPSG:4326',
                            geometry=df_line.geometry )
    df_line.drop( columns=['geometry_Fr', 'geometry_To'] , 
                   axis='columns', inplace=True)

    df_line_utm = df_line.to_crs( 'EPSG:32647' )
    df_line_utm['EucDist_km'] = df_line_utm.geometry.length/1000.
    ###################################################
    df_line['EucDist_km'] = df_line_utm['EucDist_km']

    def W5( row ):
        tol_km = df_Net['W5_DistEuc_km']
        diff = abs(row.Dist_km-row.EucDist_km) 
        row['EucDiff_km'] = diff
        if ( diff > tol_km ):
            row['W5'] = '*'
        else:
            row['W5'] = ''
        return row
    df_line = df_line.apply( W5, axis='columns' ) 
    #import pdb; pdb.set_trace()
    return df_line

################################################################
def MergePoint( df_FixPnt, df_NewPnt):
    df_FixPnt = pd.merge( df_FixPnt, df_BM , how='left',
       validate='1:1', left_on='Name', right_on='Name', copy=True )
    df_FIXPNT = df_FixPnt[ ~df_FixPnt.geometry.isnull() ].copy()
    if len(df_FIXPNT):
        def fp_desc( row ): 
            return  'H={:.3f}m.'.format( row.H_m )
        df_FIXPNT['Desc'] = df_FIXPNT.apply( fp_desc, axis='columns' ) 
    print('Number of fix BMs with coordinate {}/{}'.format(
                 len( df_FIXPNT ), len( df_FixPnt)) )
    Not_Found_Pnt = set(df_FixPnt.Name).difference(set(df_FIXPNT.Name))
    if len( Not_Found_Pnt):
        print('***WARNING*** points without thier own location from KML.')
        print( TABLE_POINT( list(Not_Found_Pnt) ) )
    ######################################################
    df_NewPnt = pd.merge( df_NewPnt, df_BM , how='left', 
            #validate='1:1', 
                    left_on='Name', right_on='Name', copy=True )
    df_NEWPNT = df_NewPnt[ ~df_NewPnt.geometry.isnull() ].copy()
    def np_desc( row ): 
        return  'AdjH= {:.3f}m. | SD=\u00B1 {:.0f}mm'.format( 
                row.AdjH_m, row.SD_mm )
    df_NEWPNT['Desc'] = df_NEWPNT.apply( np_desc, axis='columns' ) 
    print('Number of new points with coordinate found {}/{}'.format(
                 len( df_NEWPNT ), len( df_NewPnt)) )
    Not_Found_Pnt = set(df_NewPnt.Name).difference(set(df_NEWPNT.Name)) 
    if len( Not_Found_Pnt):
        print('***WARNING*** points without thier own location from KML.')
        print( TABLE_POINT( list(Not_Found_Pnt) ) )
    return df_FIXPNT, df_NEWPNT 

###############################################################
################################################################
################################################################
if __name__=='__main__':

    if len(sys.argv) <=1:
        print('***ERROR*** specify the KML file ...')
        sys.exit() 
    else:
        KML = sys.argv[1]
    print(PROG)
    print('Location of BMs from KML file : ', KML )
    #import pdb; pdb.set_trace()
    df_BM = gpd.read_file( KML, driver='KML' ) 
    df_BM.drop( labels=['Description'], axis='columns', inplace=True ) 
    ################################################################
    with open('CACHE/AdjLevNet.pkl', 'rb') as handle:
        df = pickle.load(handle)
    df_Net    = df['NETWORK']
    df_NewPnt = df['NEWPNT']
    df_FixPnt = df['FIXPNT']
    df_Diff   = df['DIFF']
    ################################################################

    df_FIXPNT, df_NEWPNT = MergePoint(df_FixPnt, df_NewPnt)
    Report_Double_Run()

    df_LINE = MergeDblLine(df_Diff, df_BM)
    ################################################################
    print( H( ' Euclidian Dist ' ) )
    stat = df_LINE.EucDist_km.describe()
    print( pd.concat( [stat], axis=1) )
    #################################################################
    df_LINEx = df_LINE[ [ 'DblRun', 'Dist_km', 
        'Allow_Clo_mm', 'DblClos_mm', 'DblDiff_m', 'DblDist_km',
        'EucDiff_km', 'EucDist_km',  'W4', 'W5' ] ].copy()

    df_LINEx['Allow_Clo_mm'] = df_LINEx['Allow_Clo_mm'].map('{:.1f}'.format)  
    for col in ('DblDist_km','EucDiff_km', 'EucDist_km'):
        df_LINEx[col] = df_LINEx[col].map('{:.3f}'.format)  
    #import pdb; pdb.set_trace()
    for warn in ( 'W4_CloKM_mm', 'W5_DistEuc_km' ):
        thres = df_Net[ warn ]
        print( H( f' Warning {warn} : {thres}' ) )
        COL = warn[:2]
        print(  df_LINEx[ df_LINEx[COL]=='*'] )

    # prepare KML ####################################################
    def Desc( row ):
        #import pdb; pdb.set_trace()
        desc = ('Dist. = {:.3f} km<br>\u0394H = {:.3f} m<br>'+\
                'Closure = {:.0f} mm ~ ').format( 
                row.Dist_km, row.Diff_m, row.DblClos_mm )
        for w in ('W1','W2','W3','W4'):
            if row[w]=='*': desc = desc+w+','
        if len(desc)>0: return desc[:-1]
        else: return ''
    df_LINE['Desc'] = df_LINE.apply( Desc, axis='columns' ) 
    df_LINE.rename( columns={'DblRun':'Name'}, inplace=True )
    kml = PlotPntKML('CACHE/PlotLevelNet.kml')
    kml.PlotPnt('FixBM', df_FIXPNT, MARKER=('target', Color.green, 2 ) )
    kml.PlotPnt('NewBM', df_NEWPNT, MARKER=('target', Color.red, 1.2 ) )
    kml.PlotDblLine( 'DoubleRun', df_LINE )
    kml.Save()
    #################################################################

