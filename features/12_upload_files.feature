@upload @files
Feature: 12 Upload Files
  As a data steward, I can upload files to object storage

  Background:
    Given we have the state "metadata submission is completed"
    And no files have been uploaded yet
    And no file metadata exists

  Scenario: Uploading single file

    When a file is uploaded
    Then metadata for the file exist
    And the files exist in the staging bucket

  Scenario: Batch uploading files

    When files are uploaded
    Then metadata for each file exist
    And the files exist in the staging bucket

    Then set the state to "files have been uploaded"
