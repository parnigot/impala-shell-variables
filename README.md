# impala-shell-variables

Small wrapper script that can be used to perform variable substitution for
sql queries executed with impala-shell. MIT licensed.

## Usage

The script requires two files:

* the file containing the sql query to run
* a "configuration" file with the variables

Usage:

```
$ impala-shell-variables.py [-a/--additional-options] [-v/--verbose] [-d/--dry-run] <path-to-sql-file> <path-to-configuration-file>
```

`additional-options` can be used to pass to impala-shell additional options,
like to enable kerberos authentication with `-k` or to connect to an impala
daemon with `-i impalad-hostname`.

Example:

```
$ impala-shell-wrapper.py my-query.sql my-conf.conf -a "-k -d DBNAME"
```

## SQL file syntax

To include variables in the sql file use Python's 
[`string.format()`](https://docs.python.org/2/library/string.html#formatspec) notation.

For example:

```sql
CREATE EXTERNAL TABLE {table_name} (
    id      INT,
    name    STRING)
STORED AS TEXTFILE
LOCATION '{table_location}';
```

## Configuration file syntax

Write a variable per line with the following syntax:

```
<variable_name> = <variable_value>
```

White spaces leading and trailing values will be stripped from the string.

An example configuration file for the above query could be:

```
table_name=test_impala_shell_variables
table_location=/tmp/test_impala_shell_variables/
```