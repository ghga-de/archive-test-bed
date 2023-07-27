@upload @files
Feature: 12 Upload Files
  As a data steward, I can upload files to object storage

  Scenario: Uploading single file

    Given no files have been uploaded yet
    And no file metadata exists

    When a file is uploaded
    Then metadata for the file exist
    And the file exist in staging bucket

  Scenario: Batch uploading files

    Given we have the state "metadata submission is completed"
    And no files have been uploaded yet
    And no file metadata exists

    When files are uploaded
    Then metadata for each file exist

    Then set the state to "files have been uploaded"
