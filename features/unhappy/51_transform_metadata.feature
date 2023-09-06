@metadata @transformation @unhappy
Feature: 51 Unhappy Transform Metadata
  As a data steward, I cannot transform with an invalid config
  or an invalid submission JSON

  Background:
    Given we have the state "unhappy metadata submission is completed"

  Scenario: Transforming metadata with an invalid config
    Given we have the "invalid" config with "valid" metadata model

    When unhappy metadata submission is transformed
    Then I get the expected error for transformation with invalid "config"

  Scenario: Transforming metadata with an invalid model
    Given we have the "valid" config with "invalid" metadata model

    When unhappy metadata submission is transformed
    Then I get the expected error for transformation with invalid "model"

  Scenario: Transforming an invalid submission JSON
    Given we have the "valid" config with "valid" metadata model
    And we have an invalid submission JSON file in the local submission store

    When unhappy metadata submission is transformed
    Then the source_events are empty
    And set the state to "unhappy metadata transformation is completed"
