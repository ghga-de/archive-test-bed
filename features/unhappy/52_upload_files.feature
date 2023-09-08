@upload @files @unhappy
Feature: 52 Unhappy Upload Files
  As a data steward, I cannot upload already existing files to object storage and
  cannot ingest files different than the existing submission

  Background:
    Given we have the state "metadata submission is completed"

  Scenario: Uploading already existing files individually

    When the files for the minimal metadata are uploaded individually
    Then I get the expected existing file error

  Scenario: Ingesting files different than submission

    Given we have no unhappy file metadata

    When the files for the unhappy metadata are uploaded individually
    Then the file metadata for each uploaded unhappy file exists

    When the unhappy file metadata is ingested
    Then I get the expected accession not found error

  Scenario: Finishing the unhappy file upload
    Then set the state to "unhappy file ingest is completed"
