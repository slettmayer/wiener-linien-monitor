# Changelog

## 0.5.0

- Automate releases: version change in manifest.json triggers tag + GitHub release after validation passes
- Add dependabot auto-bump: patch version and changelog entry created automatically on Dependabot PRs
- Add gate job to Validate workflow for branch protection
- Add Dependabot config for GitHub Actions
- Add CHANGELOG.md with historical release entries

## 0.4.1

- Fix: service rejecting integer stop_id values

## 0.4.0

- Modernize repo: DataUpdateCoordinator, config flow, tests, CI
- Extract shared API helper, add const.py, improve code quality
- Repo hygiene: fix .gitignore, add LICENSE, clean up dead code

## 0.3.0

- Add English translations as fallback

## 0.2.0

- Add fetch_departures service action
- Small code polish of sensor

## 0.1.0

- Initial cleanup after fork
