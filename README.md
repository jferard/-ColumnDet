ColumnDet - A column type detector

Copyright (C) 2020 J. Férard <https://github.com/jferard>

License: GPLv3

# Overview
Use ColumnDet to guess the type of a column in a CSV file. ColumnDet uses some 
simple and previsible methods to guess the column type. The counter is that the 
type of a column has to be validated by a human.

The output format is compliant with [MetaCSV](https://github.com/jferard/MetaCSV).

# Examples
Typical use case is:

    >>> parser = Parser.create()
    >>> description = parser.parse(
            ['20200918', '20200920', '20200923', '20200927', '20200928',
             '20201001', '20201006', '20201011', '20201016', '20201021',
             '20201023', '20201024', '20201027', '20201028', '20201102',
             '20201104', '20201108', '20201111', '20201113', '20201117',
             '20201120', '20201124']))
    >>> str(description)
    'date/yyyyMMdd'

But there is a more sophisticated usage:

    >>> from columndet.tool import csv_det
    >>> meta_csv_data = csv_det("test/fixtures/csv/20201001-bal-216402149.csv")
    >>> import sys
    >>> meta_csv_data.write(sys.stdout)
    domain,key,value
    file,encoding,UTF-8-SIG
    csv,delimiter,;
    csv,double_quote,false
    data,col/3/type,integer
    data,col/7/type,float//.
    data,col/8/type,float//.
    data,col/9/type,float//.
    data,col/10/type,float//.
    data,col/12/type,date/yyyy-MM-dd

The output is a MetaCSV file. It may need a couple of changes to match 
the exact column types.

You can the load the file with [py-mcsv](https://github.com/jferard/py-mcsv).

## Summary of column types
* `bool` : a boolean
* `currency` : a currency
* `date` : a date
* `datetime` : a date and a time or a time
* `float` : a float
* `integer` : an integer
* `percentage` : a percentage
* `text` : some text

