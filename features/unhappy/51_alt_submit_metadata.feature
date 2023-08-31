@metadata @submission @unhappy
Feature: 51 Unhappy Submit Metadata
  As a data steward, I cannot submit with invalid config
  or submit invalid research metadata into the local submission store.

  Scenario: Submitting with an invalid config file
    Given we start on a clean slate
    And we have the "invalid" config with "valid" metadata model

    When "minimal" metadata is submitted to the submission store
    Then I get the expected error for submission with "invalid_config"

  Scenario: Submitting with an invalid metadata model
    Given we start on a clean slate
    And we have the "valid" config with "invalid" metadata model

    When "minimal" metadata is submitted to the submission store
    Then I get the expected error for submission with "invalid_model"

  Scenario: Submitting with an invalid research metadata
    Given we start on a clean slate
    And we have the "valid" config with "valid" metadata model
    And we have an invalid research metadata JSON file

    When "invalid" metadata is submitted to the submission store
    Then I get the expected error for submission with "invalid_metadata"

  Scenario: Finishing the unhappy metadata submission
    Then set the state to "unhappy metadata submission is completed"
