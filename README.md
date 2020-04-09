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
