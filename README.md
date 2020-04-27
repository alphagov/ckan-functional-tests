# Functional tests for CKAN

Initially testing just the API.

## Installing & Running

Either use the `default.nix` file provided or, in a virtualenv, do a normal
`pip install -r requirements.txt`. Running should just be a matter of calling

```
$ pytest ckanfunctionaltests/
```

By default these will run against the staging data.gov.uk instance.

A number of settings controlling behaviour can be configured in the file `config.json`,
notably this includes:

 - `inc_sync_sensitive`: Set to `false`, this will skip assertions which could be sensitive to
   e.g. the target instance's database and search index having un-synchronized entries.
 - `inc_fixed_data`: Set to `false`, this will skip tests that use fixed data usually
   considered "stable" to compare with results from the target. You may want to do so if e.g.
   your target instance is only filled with sparse demo data.

## Warnings

This test suite _will_ emit warnings if it is unable to complete an assertion for reasons that
don't necessarily indicate a failure. 

Examples of such cases are where an expected value is notfound in a returned list, but the returned list has the maximum allowed number of values, eg 1000 returned results when in fact there may be 1005 in total, so the result might be item 1001.

Rather than simply marking this as a "pass" and allowing a user to infer that a specific
test is definitely working, we emit a warning summarizing the problem. 

Usually these warnings are nothing to worry about, but if you do want to explicitly assert that a particular feature
is working, some tests may respond to being run repeatedly. The `-Werror` pytest option can be
used to treat these warnings as test failures.

## Skipped tests

There are also some combinations of parametrization values which will always be skipped (because
they are combinations of features which are not supported). These are nothing to worry about
either - it's just that using `pytest.skip` was the least bad way of omitting these cases.
