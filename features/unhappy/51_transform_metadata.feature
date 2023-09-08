@metadata @transformation @unhappy
Feature: 51 Unhappy Transform Metadata
  As a data steward, I cannot transform with an unhappy config
  or an unhappy submission JSON

  Background:
    Given we have the state "unhappy metadata submission is completed"

  Scenario: Transforming metadata with an unhappy config
    Given we have the "unhappy" config with "valid" metadata model

    When unhappy metadata submission is transformed
    Then I get the expected error for transformation with unhappy "config"

  Scenario: Transforming metadata with an unhappy model
    Given we have the "valid" config with "unhappy" metadata model

    When unhappy metadata submission is transformed
    Then I get the expected error for transformation with unhappy "model"

  Scenario: Transforming an unhappy submission JSON
    Given we have the "valid" config with "valid" metadata model
    And we have an unhappy submission JSON file in the local submission store

    When unhappy metadata submission is transformed
    Then the source_events are empty
    And set the state to "unhappy metadata transformation is completed"
