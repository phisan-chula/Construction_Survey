PROG ="""
########################################################
AdjLevNet : Adjustment Computation for Levelling Network
P.Santitamnont ( phisan.chula@gmail.com)
Faculty of Engineering, Chulalongkorn University
v. 1.0  Initial                        20 May 2017
v. 1.1  Read YAML format               13 Oct 2018
v. 1.2  Q/C and double-run handling    23 Feb 2019
v. 2.0  refractoring to Pandas          3 Feb 2021
########################################################
"""
import sys,os, datetime
from collections import OrderedDict,defaultdict,Counter
import yaml, yamlordereddictloader
import numpy as np
import pandas as pd
import geopandas as gpd
from natsort import index_natsorted
from tabulate import tabulate

##################################################
WARNING_DEFAULT = { 
        'W1_Diff_m'    : 5,
        'W2_DistMax_km': 2.5 , 
        'W3_Resid_mm'  : 7, 
        'W4_CloKM_mm'  : 12,
        'W5_DistEuc_km': 0.200 
        }
##################################################
def H(str,w=70,ch='='): # make column header
    ''' make a header line embbed with center "label"
       e.g.  ==========MyHeader======== 
    '''
    return '{s:{ch}^{w}}'.format(s=str,ch=ch,w=w)

##################################################
def DBG_MTX(mat_name,mat_var):
    'manually turn on or off for debugging'
    if 0:
        hdr = ' {} {} '.format( mat_name , str( mat_var.shape ) )
        print( H(hdr,ch='#') ) 
        print( mat_var )
        return

###############################################################
def TABLE_POINT( pnts_list ):
    pnts = pnts_list.copy()
    NCOLS = 5  # show points NCOLS per line
    row, rest_pnt = divmod( len(pnts), NCOLS )
    if rest_pnt:
        pnts.extend( (NCOLS-rest_pnt)*['-'] )
        row = row+1
    pnts = np.array( pnts ).reshape( row  , NCOLS )
    table = tabulate( pnts, tablefmt="pretty" )
    return table

##################################################################
class LevellingNet:
    def __init__(self, ExecDT):
        self.ExecDateTime = ExecDT
        self.dfDIFF    = pd.DataFrame( 
                             columns=['From','To','Diff_m', 'Dist_km'] )
        self.dfFIXPNT  = pd.DataFrame( columns=['Name','H_m'] )
        self.dfNEWPNT  = pd.DataFrame( columns=['Name'] )
        self.NETWORK = OrderedDict()
        self.ADJCOMP = OrderedDict()
    
    ##############################################################
    def ReadLevNetYAML(self, FileName):
        ''' read network of levelling dataset from YAML file'''
        data = yaml.load(open(FileName),Loader=yamlordereddictloader.Loader)
        self.NETWORK = data['NETWORK']
        if data['FIX_FILE'] is not None:
            df_fix1 = gpd.read_file( data['FIX_FILE'], layer='Control3D' )   
            df_fix1['H_m'] = df_fix1['MSL_TGM']
            self.dfFIXPNT = self.dfFIXPNT.append( df_fix1 [
                ['Name','H_m','Remark']], ignore_index=True )
        if data['FIX'] is not None:
            names =  list( data['FIX'].keys())
            Hs    =  list( data['FIX'].values() )
            rems  =  ['']*len(names) 
            df_fix2 = pd.DataFrame( {'Name': names, 'H_m': Hs, 'Remark':rems } )
            self.dfFIXPNT = self.dfFIXPNT.append( df_fix2, ignore_index=True  )
        #import pdb; pdb.set_trace()
        for i, (fr_to,value) in enumerate( data['DIFF'].items() ):
            try:
                fr,to = fr_to.split(',')
                fr = "".join( fr.split() ) ; to = "".join( to.split() )
                #   A,B : 1.234, 5.678  or  A,B : [ 1.234, 5.678 ] are ok!  
                if type(value) is str:  
                    value = list( map( float, value.split(',') ) )
                self.dfDIFF.loc[i] = [ fr, to, value[0], float(value[1]) ] 
            except:
                print( '***ERROR*** parsing "{} : {}"'.format( fr_to,value ) )
                raise
        ################# DEFAULT THRESHOLD ################
        NET_KEYS = list(self.NETWORK.keys())
        for warn,value in WARNING_DEFAULT.items(): 
            #import pdb; pdb.set_trace()
            if warn not in NET_KEYS: 
                self.NETWORK[ warn ] = value 
        return data
    ################################################################
    def AnalyzeParam(self):
        occu_pnt = list(self.dfDIFF.From)+list(self.dfDIFF.To)
        uniq_pnt = set( occu_pnt )
        fix_pnt  = list(self.dfFIXPNT['Name'])       # available fix pnt 
        assert( len(fix_pnt) == len(set(fix_pnt)) )  # all unique!!!
        fix_pnt_use = set(fix_pnt) & uniq_pnt 
        new_pnt = sorted( set(uniq_pnt) - set(fix_pnt) )  
        fix_pnt_out  = sorted( set(fix_pnt) - set(uniq_pnt) )  

        self.dfFIXPNT = self.dfFIXPNT[ self.dfFIXPNT.Name.isin( fix_pnt_use) ]
        self.dfFIXPNT.reset_index( drop=True, inplace=True ) 
        #import pdb; pdb.set_trace()
        if len(fix_pnt_out):
            print(f'***WARNING*** {len(fix_pnt_out)} fix BMs are not related'\
                    f' to the network and excluded')
            print( TABLE_POINT( fix_pnt_out ) )
        print( 'Number of fixed BM(s) :', len( fix_pnt_use ) )
        if len(self.dfFIXPNT):
            dfFIXPNT = self.dfFIXPNT.copy()
            dfFIXPNT.H_m = dfFIXPNT['H_m'].map('{:7.3f}'.format)
            dfFIXPNT.index += 1
            print( tabulate( dfFIXPNT, headers='keys', tablefmt='pretty' ) )
        else:
            print('*** No fix point , Free Network Solution ***')
        print( 'Number of adjusted benchmark(s)  :', len( new_pnt ) )
        #newpnt.sort_values( by='Name', inplace=True, ignore_index=True, 
        #   key=lambda x: np.argsort( index_natsorted( df_newpnt['Name'] )) )
        print( TABLE_POINT( new_pnt ) )
        self.dfNEWPNT['Name'] = new_pnt 
        ##############################
        desc1 = self.dfDIFF.Diff_m.describe()
        desc2 = self.dfDIFF.Dist_km.describe()
        print( pd.concat( [ desc1,desc2 ], axis='columns' ) ) 
        return
   
    ##############################################################
    def _Initial_BWf(self):
        B = None ; f = None ; W = None
        for i,row in self.dfDIFF.iterrows():
            fr,to         = row.From, row.To
            diff, dist_km = row.Diff_m , row.Dist_km
            #print (fr,to), (diff,dist_km)
            if self.NETWORK['Weighted'] is False:
                dist_km = 1.0     # all is equal weight
            B_ = np.zeros( len( self.dfNEWPNT ) ) ; f_ = diff
            if fr in list( self.dfFIXPNT.Name ):
                H_m = self.dfFIXPNT[ self.dfFIXPNT.Name==fr ].iloc[0].H_m
                f_ = diff + H_m
            else:
                idx = list(self.dfNEWPNT.Name).index(fr)
                B_[idx] = -1

            if to in list( self.dfFIXPNT.Name ):
                H_m = self.dfFIXPNT[ self.dfFIXPNT.Name==to ].iloc[0].H_m
                f_ = diff - H_m
            else:
                idx = list(self.dfNEWPNT.Name).index(to)
                B_[idx] = +1

            if B is None:
                B = np.copy(B_)
                f = np.array( [f_] )
                W = np.array( [1./dist_km] )
            else: 
                B = np.vstack( (B,B_) )
                f = np.vstack( (f,[f_]) )
                W = np.append( W, [1./dist_km] )
        B = np.matrix(B)    ;         DBG_MTX('B',B)
        f = np.matrix(f)    ;         DBG_MTX('f',f)
        W = np.diag( W )    ;         DBG_MTX('W',W)     # W is P in Niemeier
        #import pdb; pdb.set_trace()
        return (B,W,f)

    ##############################################################
    def SolveLSQ(self):
        B,W,f = self._Initial_BWf()
        BtW = B.transpose()*W
        N = BtW*B                 ;         DBG_MTX('N',N)
        t = BtW*f                 ;         DBG_MTX('t',t)
        if len(self.dfFIXPNT) >= 1:  # at least one point fix
            Ni = N.I
            x = Ni*t
            Qxx = Ni
        else:   # Free Network, zero constraint
            # R.E.Deaking page5 , rewrite t to -tp
            tp = np.vstack( (+t,[[0.0]]) )    ;         DBG_MTX('tp',tp)       
            # no FixPnt , inner constrain  Sum all Hi equal to 0.0 !!!
            VOne = np.ones( (1,len(self.dfNEWPNT) ) )
            Np = np.vstack( (+N,VOne) ) # R.E.Deaking page5 , rewrite Np to -Np
            # augment N with one column of '1' , except last member '0'
            VOneEx = np.ones( (len(self.dfNEWPNT)+1, 1 ) )
            VOneEx.itemset( (-1,0), 0.0 )
            Np = np.hstack( (Np ,VOneEx) )    ;       DBG_MTX('N*',Np)
            Npi = Np.I
            xk = Npi*tp   ;         DBG_MTX('xk',xk)
            x = xk[:-1]   ;         DBG_MTX('x',x)
            Qxx = Npi[0:-1, 0:-1]   # strip under-most column and right-most row
        v = B*x-f
        Sig0_2 = v.transpose()*W*v / ( len(v)-len(x)  )
        DBG_MTX('x',x)   ;  DBG_MTX('v',v)  ;  DBG_MTX('Qxx',Qxx)
        self.ADJCOMP['x']   =    x
        self.ADJCOMP['W']   =    W
        self.ADJCOMP['v']   =    v
        self.ADJCOMP['Qxx'] =    Qxx
        self.ADJCOMP['Sig0'] =  np.sqrt( Sig0_2[(0,0)] )
        return
    
    ###############################################################
    def PostProcess(self):
        self.dfDIFF['Resid_mm']= self.ADJCOMP['v']*1000 # mm

        self.dfDIFF['Resid_limit'] = self.NETWORK['W3_Resid_mm']*\
                                     np.sqrt( self.dfDIFF.Dist_km )
        def Fix_Resid(row):
            if row.Dist_km<0.75:
                return row.Resid_limit
            else:
                return row.Resid_mm
        self.dfDIFF['Resid_mm']= self.dfDIFF.apply( Fix_Resid ,axis='columns')

        def W1( row ):
            if abs(row.Diff_m)>self.NETWORK['W1_Diff_m'] : return '*'
        self.dfDIFF['W1'] = self.dfDIFF.apply( W1, axis='columns' ) 
        def W2( row ):
            if abs(row.Dist_km)>self.NETWORK['W2_DistMax_km'] : return '*'
        self.dfDIFF['W2'] = self.dfDIFF.apply( W2, axis='columns' ) 

        def W3( row ):
            if abs(row.Resid_mm)>row.Resid_limit: return '*'
        self.dfDIFF['W3'] = self.dfDIFF.apply( W3, axis='columns' ) 

        #####################################   
        self.dfNEWPNT['AdjH_m'] = self.ADJCOMP['x']
        Sig0 = self.ADJCOMP['Sig0']
        Qxx  = self.ADJCOMP['Qxx']
        sd_mm = list()
        for i  in range( len( self.dfNEWPNT ) ):
            sd_mm.append( 1000.*Sig0*np.sqrt( Qxx[(i,i)] ) )
        self.dfNEWPNT['SD_mm'] = sd_mm
   
    ###############################################################
    def PRINT_RESULT_TABLE(self):
        print('############################################################' )
        print('############## Adjustment Computation Result ###############' )
        print('############################################################' )
        df_newpnt = self.dfNEWPNT.copy()
        print( 'SD_mm statistic:' )
        print( df_newpnt['SD_mm'].describe() )
        df_newpnt['AdjH_m'] = df_newpnt['AdjH_m'].map('{:7.3f}'.format)
        df_newpnt['SD_mm']  = df_newpnt['SD_mm'].map(' \u00B1{:.1f}'.format)
        df_newpnt.sort_values( by='Name', inplace=True, ignore_index=True, 
           key=lambda x: np.argsort( index_natsorted( df_newpnt['Name'] )) )
        df_newpnt.index += 1
        tab_newpnt =  tabulate( df_newpnt, headers='keys', tablefmt='pretty' )
        print( tab_newpnt )

        df_diff = self.dfDIFF.copy()
        df_diff['Diff_m'] = df_diff['Diff_m'].map('{:+7.3f}'.format) 
        df_diff['Dist_km'] = df_diff['Dist_km'].map('{:7.3f}'.format) 
        df_diff['Resid_mm'] = df_diff['Resid_mm'].map('{:+5.1f}'.format) 
        df_diff.drop(['Resid_limit'], axis='columns', inplace=True)
        df_diff.index += 1
        tab_diff = tabulate( df_diff, headers='keys', tablefmt="pretty", 
                             numalign='right')
        print( tab_diff )
        return

def WriteCache():
    import pickle,os
    CACHEDIR = './CACHE'
    if os.path.isdir(CACHEDIR):
        print(f'Folder "{CACHEDIR}" already exists ...')
    else:
        os.makedirs(CACHEDIR)
        print(f'Creating folder "CACHEDIR"...')
    RESULT='AdjLevNet.pkl'
    print(f'Writing ...{CACHEDIR}/{RESULT}')
    with open( f'{CACHEDIR}/{RESULT}', 'wb' ) as handle:
        pickle.dump( {  'NETWORK' : levnet.NETWORK,
                        'FIXPNT' : levnet.dfFIXPNT,
                        'NEWPNT' : levnet.dfNEWPNT,
                        'DIFF'   : levnet.dfDIFF 
                    }, handle, protocol=pickle.HIGHEST_PROTOCOL )
   
########################################################################
if __name__ == "__main__":
    #FileName = r'data/TestSingleLine.yml'
    #FileName = r'data/Niemeier442.yml'
    #FileName = r'data/Hunter_Deakin_Level.yml'
    #FileName = r'data/Hunter_Deakin_Level_freenet.yml'
    #FileName = r'data/Loop2_Garden100yrs.yml'
    #FileName = r'Processing_PakBang/Processing/20190303_PakBang_Levelling_Final.yml'
    #FileName = '/home/phisan/Project/2021-DTrack-NKS_TAK/Levelling/Data/dl_test.asc'
    FileName = '/home/phisan/Project/2021-DTrack-NKS_TAK/Levelling/Data/DiffLev_SRT_MTKN_v9.asc'
    if len(sys.argv) <=1:
        pass
    else:
        FileName = sys.argv[1]
    print(PROG)

    print('Input YAML file  : ...{}'.format(FileName[-64:]) )
    ExecuteDT = str( datetime.datetime.now() )
    print('Computed on      : ', ExecuteDT) 
    levnet = LevellingNet( ExecuteDT )
    yaml_data = levnet.ReadLevNetYAML( FileName )
    print('Project    :', yaml_data['NETWORK']['INFO'] )
 
    print('Yaml edit on     :', yaml_data['NETWORK']['Date'] )
    if levnet.NETWORK['Weighted']:
        print('Mode : weighted least square adjustment ***')
    else:
        print('Mode : equal-weight least square adjustment ****')

    ########################################
    levnet.AnalyzeParam()
    levnet.SolveLSQ( )
    levnet.PostProcess()
    levnet.PRINT_RESULT_TABLE()

    ########################################
    print( 'Differential levelling  : {} runs.'.format( len(levnet.dfDIFF) ) )
    total_run = levnet.dfDIFF.Dist_km.sum()
    print(f'Total double-run length : {total_run:.1f} km.' )
    print(f'Total levelling length  : {total_run/2.:.1f} km.' )
    x   = levnet.ADJCOMP['x']
    Qxx = levnet.ADJCOMP['Qxx']
    if len(levnet.dfFIXPNT)==0: 
        print( 'Norm of Unknown X     : {:.3f} m.( freenet )'.format(np.sum(x)))
        print( 'L-2 Norm of Unknown X : {:.3f} m.( freenet )'.\
                                    format(np.linalg.norm(x, ord=2) )  )
    print('A posteriori Sigma0     : {:.1f} mm.'.\
                    format( 1000.0*levnet.ADJCOMP['Sig0'] ) )
    print('Trace of Qxx            : {:.1f}'.format( np.trace(Qxx)  ) )

    ##################################################################
    pd.set_option('display.max_rows', None)
    df_fmt = levnet.dfDIFF.copy()
    df_fmt['Resid_mm'] = df_fmt['Resid_mm'].map('{:5.0f}'.format) 
    df_fmt['Resid_limit'] = df_fmt['Resid_limit'].map('{:5.0f}'.format) 
    for w in ('W1_Diff_m', 'W2_DistMax_km', 'W3_Resid_mm'):
        COL = w[0:2]
        nwarns = df_fmt[COL].count()     # count '*'
        hdr1 = f': Warnings {w} : {nwarns} run(s) :'
        hdr2 = '  {} = {}  '.format( w , levnet.NETWORK[w] )
        print( H(hdr1) )
        print( H(hdr2) )
        warning =df_fmt[df_fmt[COL]=='*']
        print( warning )
        print('')

    WriteCache()
    print( '******* End of LevelNet Program ********')
 
    #import pdb; pdb.set_trace()
