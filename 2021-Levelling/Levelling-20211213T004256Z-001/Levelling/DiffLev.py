#
# DiffLev.py : read differential levelling runs in YAML format
#              calculate and QC staff readings and summary results.
#
import pandas as pd
import numpy as np
import yaml
from yaml.loader import SafeLoader

###################################################################
def Step1_CalcDiff( DiffData ):
    df = pd.DataFrame.from_dict( DiffData,  orient='index',
            columns=['bsU','bsM', 'bsL', 'fsU','fsM','fsL'] )
    df.reset_index( drop=False, inplace=True )
    df.rename( columns={'index':'Sta' }, inplace=True )
    LAST = df.iloc[-1].name
    df.loc[LAST,['fsU','fsM','fsL']] = df.loc[ LAST,['bsU','bsM','bsL']].values
    df.loc[ LAST,['bsU','bsM','bsL']] = np.nan
    df['bsMean'] = df[['bsU','bsM','bsL']].mean( axis=1)
    df['fsMean'] = df[['fsU','fsM','fsL']].mean( axis=1)
    return df 

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
            elif row[COL]>=YAML['DIFF_UMML'] :
                df.loc[i,COL+'w'] = '*'
    #import pdb; pdb.set_trace()
    return df 

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

def Step4_sumDIST( df):
    df['sumBSFSDIST'] = np.nan ;  df['sumBSFSDISTw'] = ' '
    sumBS = 0.0; sumFS = 0.0
    for i,row in df.iterrows():
        if i==0:
            sumBS = row.bsDIST
        else:
            sumFS += row.fsDIST
            df.loc[i,'sumBSFSDIST'] = abs(sumBS-sumFS)
            if abs(sumBS-sumFS)>YAML['DIFF_SUMDIST']:
                df.loc[i,'sumBSFSDISTw'] = '*' 
            sumBS += row.bsDIST
    #import pdb; pdb.set_trace()
    return df

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
###################################################################
###################################################################
FILE = 'SLQ1.yaml'
#FILE = 'test.yaml'

# Open the file and load the file
with open( FILE ) as f:
    YAML = yaml.load(f, Loader=SafeLoader)
    print( YAML )

for lev_run in ['FWD','BWD']:
    print(f'#################################### {lev_run} '\
          f'####################################')
    df = Step1_CalcDiff( YAML[lev_run] )
    print( df )
    df = Step2_UMML( df)
    print( df )
    df = step3_bsfsDIST( df)
    print( df.loc[:,'bsUMML':] )
    df = Step4_sumDIST( df)
    print( df.loc[:,'bsUMML':] )

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
        raise '***ERROR***  undefine key word'
    print( df[['Sta','bsMean','fsMean','Height']] )

print('############# Summary ##############')
fwd_dist = df_FWD.bsDIST.sum()+ df_FWD.fsDIST.sum()
bwd_dist = df_BWD.bsDIST.sum()+ df_BWD.fsDIST.sum()
avg_dist = (bwd_dist+fwd_dist)/2.
print('FWD Levelling line  : {:.3f} m.'.format( fwd_dist) )
print('BWD Levelling line  : {:.3f} m.'.format( bwd_dist) )
print('mean Levelling line : {:.3f} m.'.format( avg_dist ) )
print('Loop closure        : {:.3f} m.'.format( 
    abs( df_FWD.iloc[0 ].Height - df_BWD.iloc[-1].Height   ) ) )
print('Loop closure limit  : {:.3f} m.'.format( 
        YAML['CLOSURE']/1000*np.sqrt(avg_dist/1000) ) )

fwd_diff = df_FWD.bsMean.sum()- df_FWD.fsMean.sum()
bwd_diff = df_BWD.bsMean.sum()- df_BWD.fsMean.sum()
print('FWD difference  : {:+.3f} m.'.format( fwd_diff ) )
print('BWD difference  : {:+.3f} m.'.format( bwd_diff ) )
print('mean difference : {:+.3f} m.'.format( (fwd_diff-bwd_diff)/2 ) )



import pdb; pdb.set_trace()
