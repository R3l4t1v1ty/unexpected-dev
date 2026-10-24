## dev/'s fixture save tests. Both read the fixtures in dev/fixtures/; record
## one first (in a game: Tests > Fixture saves > Record this game).

## Every fixture, run through core.migrate, matches its expected result.
label test_dev_fixtures:

    return dev.fixtures_note()

## Every fixture goes through core.migrate with only a test migration (one
## version up, changing nothing): the migration runs once, the version goes up,
## made-up sections are kept and nothing else changes.
label test_dev_fixture_migration:

    return dev.migration_note()
