#
#
#
#
#
import camelot
import sys

# PDF file to extract tables from (from command-line)
file = '../Data/1-OR00-GN-2006 SETTING OUT DATA-EAST.pdf'
#file = 'foo.pdf'
#file = sys.argv[1]

# extract all the tables in the PDF file
tables = camelot.read_pdf(file)

# number of tables extracted
print("Total tables extracted:", tables.n)


# print the first table as Pandas DataFrame
df = tables[0].df
print( df )


import pdb; pdb.set_trace()

