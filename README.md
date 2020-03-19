# Functional tests for CKAN

Initially testing just the API.

## Installing & Running

Either use the `default.nix` file provided or, in a virtualenv, do a normal
`pip install -r requirements.txt`. Running should just be a matter of calling

```
$ pytest ckanfunctionaltests/
```

By default these will run against the production data.gov.uk instance.
