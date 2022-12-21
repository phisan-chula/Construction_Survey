#
# DiffLev.py : read differential levelling runs in YAML format
#              calculate and QC staff readings and summary results.
# 2021Dec14 : Initiate
#             Faculty of Engineering, Chulonglongkorn University
#             Phisan.Chula@gmail.com 
#
#
import pandas as pd
import numpy as np
import sys,yaml
from yaml.loader import SafeLoader
import pprint
import pathlib

###################################################################
def Step1_CalcDiff( DiffData ):
    df = pd.DataFrame.from_dict( DiffData,  orient='index',
            columns=['bsU','bsM', 'bsL', 'fsU','fsM','fsL'] )
    df.reset_index( drop=False, inplace=True )
    df.rename( columns={'index':'Sta' }, inplace=True )
    #import pdb; pdb.set_trace()
    for ic in (1,2,3):
	    df.iat[-1, ic+3 ] = df.iat[-1,ic]
	    df.iat[-1, ic   ] = np.nan
    df['bsMean'] = df[['bsU','bsM','bsL']].mean( axis=1)
    df['fsMean'] = df[['fsU','fsM','fsL']].mean( axis=1)
    return df 

###################################################################
def Step2_UMML( df):
    df['bsUMML'] =   np.abs(  np.abs( df['bsU']-df['bsM'] )
                             -np.abs( df['bsM']-df['bsL'] ) ) 
    df['fsUMML'] =   np.abs(  np.abs( df['fsU']-df['fsM'] )
                             -np.abs( df['fsM']-df['fsL'] ) ) 
    df[['bsUMMLw','fsUMMLw']] = ' ',' '
    for COL in ['bsUMML','fsUMML']:
        for i,row in df.iterrows():
            if np.isnan(row[COL]):
                continue
            elif row[COL]>=YAML['DIFF_UMML'] and \
                    ~np.isclose(row[COL], YAML['DIFF_UMML'] ):
                df.loc[i,COL+'w'] = '*'
    return df 

###################################################################
def step3_bsfsDIST( df):
    df['bsDIST'] = 100* np.abs( df['bsU']-df['bsL'] )
    df['fsDIST'] = 100* np.abs( df['fsU']-df['fsL'] )
    df['bsfsDIST'] = np.nan ;  df['bsfsDISTw'] = ' ' 
    for i,row in df.iterrows():
        if i==0:
            continue
        else:
            diff = np.abs(df.iloc[i-1].bsDIST-df.iloc[i].fsDIST)
            df.loc[i,'bsfsDIST'] = diff 
            if abs(diff)> YAML['DIFF_DIST']:
                df.loc[i,'bsfsDISTw'] = '*' 
    #import pdb; pdb.set_trace()
    return df
     
###################################################################
def Step4_sumDIST( df):
    df['accuDIST'] = np.nan ;  df['accuDISTw'] = ' '
    sumBS = 0.0; sumFS = 0.0
    for i,row in df.iterrows():
        if i==0:
            sumBS = row.bsDIST
        else:
            sumFS += row.fsDIST
            df.loc[i,'accuDIST'] = abs(sumBS-sumFS)
            if abs(sumBS-sumFS)>YAML['DIFF_SUMDIST']:
                df.loc[i,'accuDISTw'] = '*' 
            sumBS += row.bsDIST
    #import pdb; pdb.set_trace()
    return df

###################################################################
def Step5_CalcHeight(df, INIT_HEI ):
    for i,row in df.iterrows():
        if i==0:
            df.loc[0,'Height'] = INIT_HEI
        else:
            df.loc[i,'Height'] = df.loc[i-1,'Height']+\
                                 df.loc[i-1,'bsMean']-\
                                 df.loc[i,'fsMean']
    return df

###################################################################
import matplotlib.pyplot as plt
def Step6_StaViz( df_FWD, df_BWD ):
	STAFF = 3.0
	pathlib.Path('./pics').mkdir(parents=True, exist_ok=True)
	UML_STL = dict( xycoords='data' , textcoords='offset points', size=10, 
	    va="center", ha="center", bbox=dict(boxstyle="round4", fc="w"),
        arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=-0.2", fc="w") )
	TNP_STL = dict( size=15, ha="center",va="top",bbox=dict(boxstyle="round", 
			ec=(1., 0.5, 0.5), fc=(1., 0.8, 0.8)), alpha=0.4 )
	for df,RUN in ( [df_FWD,'FWD'], [df_BWD,'BWD'] ):
		for i in range(len(df)-1) :
			fig,ax = plt.subplots()
			BS = df.iloc[i] ; FS = df.iloc[i+1]
			ax.plot( [-df.iloc[i  ].bsDIST, +df.iloc[i+1].fsDIST ],    # L.O.S
				     [ 0, 0 ] , color='r' )
			ax.plot( [-df.iloc[i  ].bsDIST, -df.iloc[i  ].bsDIST ],    
		   		     [-df.iloc[i  ].bsM ,STAFF-df.iloc[i  ].bsM  ], 
		   		       c='gray',lw='5' )
			ax.plot( [+df.iloc[i+1].fsDIST, +df.iloc[i+1].fsDIST ],    
		   		     [-df.iloc[i+1].fsM ,STAFF-df.iloc[i+1].fsM  ], 
		   		       c='gray',lw='5' )
			ax.plot( [0], [0], marker='^', ms=30, c='orange' )
			for rdg in ['bsU','bsM','bsL']:
				ann = ax.annotate(f'{BS[rdg]:.3f}',
				     xy=(-BS.bsDIST, BS[rdg]-BS.bsM), xytext=(-50, 0), **UML_STL)
			for rdg in ['fsU','fsM','fsL']:
				ann = ax.annotate(f'{FS[rdg]:.3f}',
				     xy=(+FS.fsDIST, FS[rdg]-FS.fsM), xytext=(+50, 0),**UML_STL)
			ax.text( -BS.bsDIST , -BS.bsM   , BS.Sta , **TNP_STL )
			ax.text( +FS.fsDIST , -FS.fsM   , FS.Sta , **TNP_STL )		
			ax.get_yaxis().set_ticks([])
			ax.set_xlabel('Dist to staff (m)')
			ax.grid()
			TITLE = f'{RUN}{i:03d}_{BS.Sta}_{FS.Sta}'
			ax.set_title( TITLE )
			plt.tight_layout()
			print(f'Plotting  pics/{TITLE}.png ...')
			plt.savefig( f'./pics/{TITLE}.png' )
			#plt.show()
			plt.cla(); plt.clf(); plt.close('all')

###################################################################
def Step7_BrkLoop( df_FWD, df_BWD ):
	print('############### Loop Breaking ###############')
	LoopSta = [df_FWD.iloc[0].Sta]+YAML['BREAK_LOOP']+[df_FWD.iloc[-1].Sta]
	loops = list()
	for i in range(len(LoopSta)-1):
		FR = LoopSta[i]  ; TO = LoopSta[i+1]
		fwd_diff = df_FWD[df_FWD.Sta==TO].iloc[0].Height-\
		           df_FWD[df_FWD.Sta==FR].iloc[0].Height 
		bwd_diff = df_BWD[df_BWD.Sta==FR].iloc[0].Height-\
		           df_BWD[df_BWD.Sta==TO].iloc[0].Height 
		loop_diff = abs( abs(fwd_diff)-abs(bwd_diff) )
		loops.append( [ FR,TO, fwd_diff, bwd_diff, loop_diff ] )
	df_loop = pd.DataFrame( loops, columns=[
		    'Sta1','Sta2','FWD_diff', 'BWD_diff', 'Loop_diff'] )
	print(df_loop)
		
###################################################################
###################################################################
###################################################################
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
if len(sys.argv)==1:
    #FILE = 'SLQ1.yaml'
    FILE = 'Party10_2562.yaml'
    #FILE = 'test.yaml'
else:
    FILE = sys.argv[1] 

with open( FILE ) as f:
    YAML = yaml.load(f, Loader=SafeLoader)
    #pprint.pprint( YAML )
    
    if 'FLOAT_ROUND' in YAML.keys():
    	FLOAT_ROUND = YAML['FLOAT_ROUND']
    else:
        FLOAT_ROUND = 3  # default

for lev_run in ['FWD','BWD']:
    print(f'#################################### {lev_run} '\
          f'####################################')
    df = Step1_CalcDiff( YAML[lev_run] )
    print( df.round(FLOAT_ROUND) )
    Step2_UMML( df)
    step3_bsfsDIST( df)
    Step4_sumDIST( df)
    COLs = ['Sta', 'bsUMML',  'bsUMMLw',  'fsUMML','fsUMMLw',  'bsDIST',  'fsDIST',
            'bsfsDIST', 'bsfsDISTw',  'accuDIST', 'accuDISTw' ]
    print( df.loc[:,COLs].round(FLOAT_ROUND) )
    if lev_run == 'FWD':
        if 'BM' in YAML.keys():
            InitHei = YAML['BM'][df.iloc[0].Sta]
        else:
            InitHei = 0.0
        df = Step5_CalcHeight(df, InitHei)
        df_FWD = df.copy()
        InitHei_BWD = df.iloc[-1].Height
    elif lev_run == 'BWD':
        df = Step5_CalcHeight(df, InitHei_BWD)
        df_BWD = df.copy()
    else:
        raise '***ERROR***  undefined key word'
    print( df[['Sta','bsMean','fsMean','Height']].round(FLOAT_ROUND) )
del df # dismiss ...

#########################################################################
Step6_StaViz( df_FWD, df_BWD )
if  'BREAK_LOOP' in YAML.keys() and len(YAML['BREAK_LOOP'])>0:
	Step7_BrkLoop( df_FWD, df_BWD )

print('################## Summary ##################')
print('FWD levelling line "{}" to "{}"'.format(  
            df_FWD.iloc[0].Sta,  df_FWD.iloc[-1].Sta ) )
print('BWD levelling line "{}" to "{}"'.format(  
            df_BWD.iloc[0].Sta,  df_BWD.iloc[-1].Sta ) )

fwd_dist = df_FWD.bsDIST.sum()+ df_FWD.fsDIST.sum()
bwd_dist = df_BWD.bsDIST.sum()+ df_BWD.fsDIST.sum()
avg_dist = (bwd_dist+fwd_dist)/2.
print('FWD levelling dist  : {:.3f} m.'.format( fwd_dist) )
print('BWD levelling dist  : {:.3f} m.'.format( bwd_dist) )
print('Average levelling dist : {:.3f} m.'.format( avg_dist ) )
print('Loop closure        : {:.3f} m.'.format( 
    abs( df_FWD.iloc[0 ].Height - df_BWD.iloc[-1].Height   ) ) )
print('Loop closure limit  : {:.3f} m.'.format( 
        YAML['CLOSURE_KM']/1000*np.sqrt(avg_dist/1000) ) )

fwd_diff = df_FWD.bsMean.sum()- df_FWD.fsMean.sum()
bwd_diff = df_BWD.bsMean.sum()- df_BWD.fsMean.sum()
print('FWD difference  : {:+.3f} m.'.format( fwd_diff ) )
print('BWD difference  : {:+.3f} m.'.format( bwd_diff ) )
print('mean difference : {:+.3f} m.'.format( (fwd_diff-bwd_diff)/2 ) )
print('********* end of DiffLev.py **********')

#import pdb; pdb.set_trace()
