ColumnDet - A column type detector

Copyright (C) 2020 J. Férard <https://github.com/jferard>

License: GPLv3

# Overview
Use ColumnDet to guess the type of a column in a CSV file. ColumnDet uses some 
simple and previsible methods to guess the column type (no AI). The type has to 
be valdiated by a human.

## Column types
* `bool` : a boolean
* `currency` : a currency
* `date` : a date
* `datetime` : a date and a time or a time
* `text` : some text
* `float` : a float
* `integer` : an integer
* `percentage` : a percentage

## Use case
ColumnDet is a helper for CSV file loaders.