#
#
#
#
#
import pandas as pd 
import sys,logging
from pathlib import Path

#####################################################################################
def ConvGSheet( dfSheet ):
    dfSta = dfSheet[ ~dfSheet['Point'].isnull() ]['Point']
    if dfSheet.BS.median() < 5:  # meter reading 
        dfSheet['BS'] = 1000*dfSheet['BS']
        dfSheet['FS'] = 1000*dfSheet['FS']
    FMT_BF   = '    {:6s} : [ {:5.0f}, {:5.0f}, {:5.0f} ]'
    FMT_BSFS = '    {:6s} : [ {:5.0f}, {:5.0f}, {:5.0f}, {:5.0f}, {:5.0f}, {:5.0f} ]'
    for i,sta in dfSta.iteritems():
        #print( i ,sta )
        if sta==dfSta.iloc[0]:   # first pnt
            uml = dfSheet.iloc[i:i+3]['BS'].to_list()
            logging.info( FMT_BF.format( sta, *uml ) ) 
        elif sta==dfSta.iloc[-1]:   # last pnt
            uml = dfSheet.iloc[i:i+3]['FS'].to_list()
            logging.info( FMT_BF.format( sta, *uml ) ) 
        else:
           uml_bs = dfSheet.iloc[i:i+3]['BS'].to_list()
           uml_fs = dfSheet.iloc[i:i+3]['FS'].to_list()
           logging.info( FMT_BSFS.format( sta, *(uml_bs+uml_fs) ) ) 

########################################################################
########################################################################
########################################################################
xGSHEET = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR2ADlkSSGN4zg8OO2e2AsKVaBz9UvBUqlPVyIC5-1wx-6_R_RtW1j3ulb6OPDidNnrclwvbF24FNPc/pub?output=xlsx'

if len(sys.argv)==2:
    GSHEET = Path( sys.argv[1] )
else:
    GSHEET = Path( 'TestLevelling_2021.xlsx' )
#import pdb;pdb.set_trace()
#################################################
YAML = Path(  f'{GSHEET.stem}.yaml' )
try:
    YAML.unlink()
except OSError as e:
    print("Error: %s : %s" % (YAML, e.strerror))

level    = logging.INFO
format   = '  %(message)s'
handlers = [logging.FileHandler( YAML ), logging.StreamHandler()]
logging.basicConfig(level = level, format = format, handlers = handlers )

logging.info( """
CLOSURE_KM   :  12       # mm*sqrt(KM)
DIFF_UMML    :  0.002    # reading U-M and M-L less than 2 mm
DIFF_DIST    :  10       # statdia distance BS vs FS less than 10 meter
DIFF_SUMDIST :  20       # sum distance BS vs FS less than 20 meter
#BREAK_LOOP   : [ BMX,BMY ]
#BM:
#    BMP : xx.xxx
#""")
for sheet in ('FWD','BWD'):
    logging.info( '{}:'.format( sheet ) )
    dfSheet = pd.read_excel( GSHEET, sheet )
    print( dfSheet )
    ConvGSheet( dfSheet )

print('************** end **************')
#import pdb ; pdb.set_trace()
