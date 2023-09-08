@metadata @submission @unhappy
Feature: 50 Unhappy Submit Metadata
  As a data steward, I cannot submit with unhappy config
  or submit unhappy research metadata into the local submission store.

  Scenario: Submitting with an unhappy config file
    Given we start on a clean unhappy submission registry
    And we have the "unhappy" config with "valid" metadata model

    When "minimal" metadata is submitted to the submission store
    Then I get the expected error for submission with unhappy "config"

  Scenario: Submitting with an unhappy metadata model
    Given we have the "valid" config with "unhappy" metadata model

    When "minimal" metadata is submitted to the submission store
    Then I get the expected error for submission with unhappy "model"

  Scenario: Submitting with an unhappy research metadata
    Given we have the "valid" config with "valid" metadata model
    And we have an unhappy research metadata JSON file

    When "unhappy" metadata is submitted to the submission store
    Then I get the expected error for submission with unhappy "metadata"
    And set the state to "unhappy metadata submission is completed"
