# npgqc-python

This package contains an ORM for an existing database schema, which hosts
autoqc results and manual QC outcomes for sequencing data. A Perl ORM for the
same schema is defined in [npg_qc](https://github.com/wtsi-npg/npg_qc).
Migrations for that schema are also tracked in the Perl package.

This ORM has been auto-generated with [`sqlacodegen 4.0.4`](https://pypi.org/project/sqlacodegen/4.0.4/)

```
sqlacodegen --generator declarative mysql+pymysql://user:pass@host:port/dbname > src/npgqc/db/schema.py
```

The package also contains utility functions for data retrieval.

## Development

The project follows Google code and documentation [style guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).
Linting should be performed by `ruff`.

Installation and testing:

```
pip install .[test]
pytest
```

Tests that need a MySQL server are skipped unless `NPGQC_TEST_DB_URL` is set.
The database named in the URL is created for the test run and dropped
afterwards, so do not point it at a database you want to keep:

```
docker run -d --rm --name npgqc-test-mysql -e MYSQL_ROOT_PASSWORD=test -p 13306:3306 mysql:8.0
NPGQC_TEST_DB_URL=mysql+pymysql://root:test@127.0.0.1:13306/npgqc_test pytest
```
