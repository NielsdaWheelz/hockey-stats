# disposable rollback needs a permitted sqlite temp directory

status: scratch red/green passes; full corrected disposable rollback remains pending root release.

the confined rollback01 command failed before rotation with `SQLITE_IOERR_GETTEMPPATH`6410. its incoming baseline copy and logs remain intact; active/previous were not created. the profile denied every ordinary sqlite temp directory. the same node sqlite scratch operation fails without `SQLITE_TMPDIR` and passes with a temp directory inside the permitted subtree. no production change is needed.

[correction and control evidence](../research/spatial-v1-08/receipts/replacement-fixture-rollback-temp-correction.json) pins the unexecuted rollback02 command/profile. it creates a dedicated permitted temp directory and uses the existing operator unchanged. resolution requires all three disposable baseline/candidate/restore operations, expected identities and costs, with no serving mutation. browser acceptance remains separate.
