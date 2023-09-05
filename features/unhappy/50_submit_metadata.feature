@metadata @submission @unhappy
Feature: 50 Unhappy Submit Metadata
  As a data steward, I cannot submit with invalid config
  or submit invalid research metadata into the local submission store.

  Scenario: Submitting with an invalid config file
    Given we start on a clean slate
    And we have the "invalid" config with "valid" metadata model

    When "minimal" metadata is submitted to the submission store
    Then I get the expected error for submission with invalid "config"

  Scenario: Submitting with an invalid metadata model
    Given we have the "valid" config with "invalid" metadata model

    When "minimal" metadata is submitted to the submission store
    Then I get the expected error for submission with invalid "model"

  Scenario: Submitting with an invalid research metadata
    Given we have the "valid" config with "valid" metadata model
    And we have an invalid research metadata JSON file

    When "invalid" metadata is submitted to the submission store
    Then I get the expected error for submission with invalid "metadata"
    And set the state to "unhappy metadata submission is completed"
