#
PROG="""
DiffLev.py : process differential levelling observations, analyze 
             quality and summarize report. Input is in YAML format.
2021Dec21  : Initial release
             Assoc.Prof.Dr. Phisan Santitamnont
             Faculty of Engineering, Chulonglongkorn University
             Phisan.Chula@gmail.com
"""
#
#
import pandas as pd
import numpy as np
import sys,yaml
from yaml.loader import SafeLoader
import matplotlib.pyplot as plt
from matplotlib.markers import MarkerStyle
import pathlib, argparse
from tabulate import tabulate

#########################################################################
class DiffLevel:
    def __init__(self, YAMLFILE ):
        self.YAMLFILE = YAMLFILE
        with open( YAMLFILE, 'r') as f:
            self.YAML = yaml.load(f, Loader=SafeLoader)
        if 'FLOAT_ROUND' not in self.YAML.keys(): self.YAML['FLT_ROUND'] = 3  # default
        if 'STAFF_LEN' not in self.YAML.keys(): self.YAML['STAFF_LEN'] = 3  # default
        self.WARN = '*'
        self.LEVRUN = list()
        for lev_run in ['FWD','BWD']:
            if lev_run in self.YAML.keys():
                print(f'{43*"#"} {lev_run} {43*"#"}')
                df = self.Step1_CalcDiff( self.YAML[lev_run] )
                self.Step2_UMML( df)
                self.step3_DIbsfs( df)
                self.Step4_sumDIST( df)
                if lev_run == 'FWD':
                    if 'BM' in self.YAML.keys():
                        InitHei = self.YAML['BM'][df.iloc[0].Sta]
                    else:
                        InitHei = 0.0
                    df = self.Step5_CalcHeight(df, InitHei)
                    self.LEVRUN.append( ('FWD' , df.copy()) )
                    InitHei_BWD = df.iloc[-1].Height
                elif lev_run == 'BWD':
                    df = self.Step5_CalcHeight(df, InitHei_BWD)
                    self.LEVRUN.append( ('BWD' , df.copy()) )
                else:
                    raise '***ERROR***  undefined key word'
                COLs = ['Sta', 'bsU', 'bsM', 'bsL', 'fsU', 'fsM', 'fsL', 'bsMean', 'fsMean', 
                        'bsUMML', 'fsUMML', 'W_bsUMML', 'W_fsUMML', 'DIbs', 'DIfs', 
                        'DIbsfs', 'W_DIbsfs', 'DIaccu', 'W_DIaccu', 'Height' ]

                TAB1 = [ "Sta","bsU","bsM","bsL","fsU","fsM","fsL","bsMean","fsMean","Height", "Sta" ]
                def flt_fmt(row):
                    for col in COLs: 
                        if (col[0:2]=='bs' or col[0:2]=='fs' ) and ( row.notna()[col] ):
                            FLT_FMT = '{{:.{}f}}'.format( self.YAML['FLT_ROUND'] )
                            row[col] = FLT_FMT.format( row[col] )
                        elif col[0:2]=='DI' and  row.notna()[col]:
                            row[col] = '{:.1f}'.format( row[col] )
                        elif col=='Height':
                            FLT_FMT = '{{:+.{}f}}'.format( self.YAML['FLT_ROUND'] )
                            row[col] = FLT_FMT.format( row[col] )
                    return row
                df = df.apply( flt_fmt, axis='columns') 
                #import pdb; pdb.set_trace()
                TAB1 = [ 'Sta', 'bsU', 'bsM', 'bsL', 'fsU', 'fsM', 'fsL', 'bsMean', 'fsMean', 'Height' ]
                print( tabulate( df[TAB1],headers=TAB1, tablefmt='pretty' ) )
                TAB2 = ['Sta', 'bsUMML', 'W_bsUMML', 'fsUMML', 'W_fsUMML', 'DIbs', 'DIfs', 
                        'DIbsfs', 'W_DIbsfs', 'DIaccu', 'W_DIaccu' ]
                TAB2_HDR = ['Sta', 'bsUMML',  'W', 'fsUMML', 'W', 'DIbs', 'DIfs', 
                        'DIbsfs', 'W', 'DIaccu', 'W' ]
                print( tabulate( df[TAB2] , headers=TAB2_HDR, tablefmt='pretty' ) )
            del df # dismiss ...

    ###################################################################
    def Step1_CalcDiff( self, DiffData ):
        df = pd.DataFrame.from_dict( DiffData,  orient='index',
                columns=['bsU','bsM', 'bsL', 'fsU','fsM','fsL'] )
        df.reset_index( drop=False, inplace=True )
        df.rename( columns={'index':'Sta' }, inplace=True )
        for col in 'bsU   bsM   bsL     fsU     fsM     fsL'.split():
            df[col]=df[col]/1000.
        for ic in (1,2,3):
                df.iat[-1, ic+3 ] = df.iat[-1,ic]
                df.iat[-1, ic   ] = np.nan
        df['bsMean'] = df[['bsU','bsM','bsL']].mean( axis=1)
        df['fsMean'] = df[['fsU','fsM','fsL']].mean( axis=1)
        return df 

    ###################################################################
    def Step2_UMML( self, df):
        df['bsUMML'] =   np.abs(  np.abs( df['bsU']-df['bsM'] )
                                 -np.abs( df['bsM']-df['bsL'] ) ) 
        df['fsUMML'] =   np.abs(  np.abs( df['fsU']-df['fsM'] )
                                 -np.abs( df['fsM']-df['fsL'] ) ) 
        df[['W_bsUMML','W_fsUMML']] = ' ',' '
        for COL in ['bsUMML','fsUMML']:
            for i,row in df.iterrows():
                if np.isnan(row[COL]):
                    continue
                elif row[COL]>= self.YAML['DIFF_UMML'] and \
                        ~np.isclose(row[COL], self.YAML['DIFF_UMML'] ):
                    df.loc[i,'W_'+COL] = self.WARN
        return df 

    ###################################################################
    def step3_DIbsfs(self, df):
        df['DIbs'] = 100* np.abs( df['bsU']-df['bsL'] )
        df['DIfs'] = 100* np.abs( df['fsU']-df['fsL'] )
        df['DIbsfs'] = np.nan ;  df['W_DIbsfs'] = '' 
        for i,row in df.iterrows():
            if i==0:
                continue
            else:
                diff = np.abs(df.iloc[i-1].DIbs-df.iloc[i].DIfs)
                df.loc[i,'DIbsfs'] = diff 
                if abs(diff)> self.YAML['DIFF_DIST']:
                    df.loc[i,'W_DIbsfs'] = self.WARN 
        #import pdb; pdb.set_trace()
        return df
         
    ###################################################################
    def Step4_sumDIST(self, df):
        df['DIaccu'] = np.nan ;  df['W_DIaccu'] = ''
        sumBS = 0.0; sumFS = 0.0
        for i,row in df.iterrows():
            if i==0:
                sumBS = row.DIbs
            else:
                sumFS += row.DIfs
                df.loc[i,'DIaccu'] = abs(sumBS-sumFS)
                if abs(sumBS-sumFS)>self.YAML['DIFF_SUMDIST']:
                    df.loc[i,'W_DIaccu'] = self.WARN 
                sumBS += row.DIbs
        #import pdb; pdb.set_trace()
        return df

    ###################################################################
    def Step5_CalcHeight(self, df, INIT_HEI ):
        for i,row in df.iterrows():
            if i==0:
                df.loc[0,'Height'] = INIT_HEI
            else:
                df.loc[i,'Height'] = \
                   df.loc[i-1,'Height']+df.loc[i-1,'bsMean']-df.loc[i,'fsMean']
        return df

    ###################################################################
    def Step6_LevelSetUpPlot(self):
        pathlib.Path('./pics').mkdir(parents=True, exist_ok=True)
        for RUN,df in self.LEVRUN:
            for i in range(len(df)-1) :
                BS = df.iloc[i] ; FS = df.iloc[i+1] 
                TITLE = f'{self.YAMLFILE.stem}_{RUN}{i:03d}'
                self._Step6_LevelSetUpPlot(BS,FS,TITLE)
                #import pdb; pdb.set_trace()                 
    
    ###################################################################
    def _Step6_LevelSetUpPlot(self, BS, FS, TITLE ):
        def UML_STL(fc):
            return  dict( xycoords='data' , textcoords='offset points', size=10, 
                va="center", ha="center", bbox=dict(boxstyle="round4", fc=fc),
                arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=-0.2", fc="w") )
        TNP_STL = dict( size=15, ha="center",va="top",bbox=dict(boxstyle="round", 
                        ec=(1., 0.5, 0.5), fc=(1., 0.8, 0.8)), alpha=0.4 )
        LEVEL = MarkerStyle(6) ; LEVEL._transform.scale(0.4, 1.5)
        fig,ax = plt.subplots()
        ax.plot( [-BS.DIbs, +FS.DIfs ], [ 0, 0 ] , color='r' )
        ax.plot( [-BS.DIbs, -BS.DIbs ],    
                [-BS.bsM ,self.YAML['STAFF_LEN']-BS.bsM  ], c='gray',lw='5' )
        ax.plot( [+FS.DIfs, +FS.DIfs ],    
                     [-FS.fsM ,self.YAML['STAFF_LEN']-FS.fsM  ], c='gray',lw='5' )
        ax.plot( [0], [0], marker=LEVEL , ms=50, c='orange' )
        #if FS.Sta=='BM-C': import pdb; pdb.set_trace()
        for rdg in ['bsU','bsM','bsL']:
            c = 'red' if BS.W_bsUMML==self.WARN else 'white'
            ann = ax.annotate(f'{BS[rdg]:.3f}',
                     xy=(-BS['DIbs'], BS[rdg]-BS['bsM']), xytext=(-50, 0), **UML_STL(c) )
        for rdg in ['fsU','fsM','fsL']:
            c = 'red' if FS.W_fsUMML==self.WARN else 'white'
            ann = ax.annotate(f'{FS[rdg]:.3f}',
                     xy=(+FS['DIfs'], FS[rdg]-FS['fsM']), xytext=(+50, 0), **UML_STL(c) )
        ax.text( -BS['DIbs'] , -BS['bsM']  , BS['Sta'] , **TNP_STL )
        ax.text( +FS['DIfs'] , -FS['fsM']  , FS['Sta'] , **TNP_STL )          
        ax.get_yaxis().set_ticks([])
        ax.set_xlabel('Dist to staff (m)')
        ax.grid()
        ax.set_title( TITLE )
        plt.tight_layout()
        print(f'Plotting  pics/{TITLE}.png ...')
        plt.savefig( f'./pics/{TITLE}.png' )
        #plt.show()
        plt.cla(); plt.clf(); plt.close('all')
        
    ###################################################################
    def Step7_BrkLoop(self):
        [ [FWD,df_FWD],[BWD,df_BWD] ] = self.LEVRUN
        LoopSta = [df_FWD.iloc[0].Sta]+self.YAML['BREAK_LOOP']+[df_FWD.iloc[-1].Sta]
        loops = list()
        for i in range(len(LoopSta)-1):
            FR = LoopSta[i];  TO = LoopSta[i+1]
            diffs = list() ; dists= list()
            for RUN,df in self.LEVRUN:
                iFR = df[df.Sta==FR].index[0]
                iTO = df[df.Sta==TO].index[0]
                diffs.append( df.iloc[iTO].Height-df.iloc[iFR].Height )
                df_dist = df[ ['Sta','DIbs','DIfs']].iloc[iFR:iTO+1].copy()
                df_dist.loc[ iFR, 'DIfs'] = np.NaN
                df_dist.loc[ iTO, 'DIbs'] = np.NaN
                dists.append( df_dist['DIbs'].sum()+df_dist['DIfs'].sum() )
                tmp=FR; FR=TO; TO=tmp
            loop_diff = abs( abs(diffs[0])-abs(diffs[1]) )
            loop_dist = (dists[0]+dists[1])/2.
            loop_limit = np.sqrt(loop_dist/1000)*self.YAML['CLOSURE_KM']/1000
            warn = self.WARN if loop_diff>loop_limit else ' ' 
            loops.append( [ FR,TO, diffs[0], diffs[1], loop_diff, loop_limit,
                            warn, dists[0], dists[1], loop_dist ] )
        COLs = ['Sta1', 'Sta2', 'FWD_diff', 'BWD_diff', 'Loop_diff', 'Loop_LIMIT', 
               'W', 'FWD_dist', 'BWD_dist', 'Loop_dist']
        df_loop = pd.DataFrame( loops, columns=COLs )
        def flt_fmt(row):
            for col in COLs: 
                if col in ['FWD_diff', 'BWD_diff', 'Loop_diff', 'Loop_LIMIT']:
                    FLT_FMT = '{{:.{}f}}'.format( self.YAML['FLT_ROUND'] )
                    row[col] = FLT_FMT.format( row[col] )
                elif col in [ 'FWD_dist', 'BWD_dist', 'Loop_dist' ]:
                    row[col] = '{:.1f}'.format( row[col] )
            return row
        df_loop = df_loop.apply( flt_fmt, axis='columns') 
        print( tabulate( df_loop, headers=COLs, tablefmt='pretty' ) )

###################################################################
###################################################################
###################################################################
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

arg =  argparse.ArgumentParser( prog='DiffLev', description=PROG )
arg.add_argument('-p', '--plot', action='store_true', 
                help='plot each level setup in "./pics" folder' )
arg.add_argument('yaml', type=pathlib.Path,
                help='input YAML differential observes file' )
ARGS = arg.parse_args()

print( PROG )
print( 'Reading YAML ...', ARGS.yaml )
difflev = DiffLevel( ARGS.yaml )
#########################################################################
if ARGS.plot:
    print('Plotting all levelling setups')
    difflev.Step6_LevelSetUpPlot()
if 'BREAK_LOOP' in difflev.YAML.keys() and len(difflev.YAML['BREAK_LOOP'])>0:
    print(f'{42*"#"} Loop Breaking {42*"#"}')
    difflev.Step7_BrkLoop()
print('#################### Summary ####################')
dists=list() ; diffs=list()
for RUN, df in difflev.LEVRUN:
    print('{} levelling line  : "{}" to "{}"'.format( RUN,df.iloc[0].Sta,df.iloc[-1].Sta ) )
    dist = df.DIbs.sum()+ df.DIfs.sum()
    print('{} levelling dist  : {:,.1f} m.'.format( RUN, dist) )
    diff = df.iloc[-1].Height - df.iloc[0].Height
    print('{} difference      : {:+.3f} m.'.format( RUN,diff ) )
    dists.append( dist )    
    diffs.append( diff )
avg_dist = (dists[0]+dists[1])/2.
print('Average levelling dist : {:,.1f} m.'.format( avg_dist ) )
loop_diff =  abs( abs(diffs[0]) - abs(diffs[1]) )
clo_lim = difflev.YAML['CLOSURE_KM']/1000*np.sqrt(avg_dist/1000)
warn = 'Over!' if loop_diff>clo_lim else 'OK!'
print('Loop closure LITMIT : {:.3f} m.'.format( clo_lim ) )
print('Loop closure        : {:.3f} m. {}'.format( loop_diff, warn ) )
print('mean difference     : {:+.3f} m.'.format( (diffs[0]-diffs[1])/2 ) )
print('############### end of DiffLev.py #################')
#import pdb; pdb.set_trace()
