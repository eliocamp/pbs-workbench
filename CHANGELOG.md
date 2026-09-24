# Changelog


## [2.2.0] - 2026-09-24

### Added 

- `job api` now has a global option `--timeout` to set the maximum wait for PBS commands. For example `job api --timeout 2 start` will return an exception if `qsub` does not respond after 2 seconds. The default value is 10 seconds. 

- These release notes. 

