# Functional tests for CKAN

Initially testing just the API.

## Setup CKAN variables

- Before running these tests you will need to setup the test data in CKAN by running `ckan datagovuk create-dgu-test-data` in the CKAN container. 

- Update `config.json` to point to the CKAN website that you want to run the tests against.
  - make sure that you set the correct version of `ckan_version` as support for v1 API was dropped in 2.9.
  - You may need to update the `ckan_mock_harvest_source` value in `config.json` if it has been remapped, the errors in the test results should give you a hint at the correct url which is normally running on port 11088. Other values that the tests need will be automatically generated in `ckan-vars.conf`. 
  - If you tear down the CKAN stack and rebuild everything it is probably a good idea to delete `ckan-vars.conf` so that it gets regenerated with the latest values.

After these steps you should be able to run the tests.

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

To run against CKAN in Integration:

 - `username`: set the basic auth username on the Integration environment.
 - `password`: set the basic auth password on the Integration environment.

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

## Troubleshooting

If some tests are failing because of the mock harvest source not matching then it's likely that 
the `vars.conf` was not updated in nginx in the `static-mock-harvest-source` container. 
Run these commands to fix it without having to rebuild the `static-mock-harvest-source` image -

```
docker exec -it static-mock-harvest-source bash
echo $'\nmap $host $mock_absolute_root_url { default "http://static-mock-harvest-source:11088/"; }' >> /etc/nginx/vars.conf
service nginx reload
```

To make these changes more permanent add this to the end of `vars.conf` in the relevant source file if `bootstrap.sh`
didn't update it, which can happen if you checked out a different branch on the `ckan-mock-harvest-sources` repo -

  map $host $mock_absolute_root_url { default "http://static-mock-harvest-source:11088/"; }

and then run the `./scripts/rebuild-ckan.sh 2.7` script (substitute 2.7 for the version you want to rebuild).

## Licence

[MIT License](LICENCE)
