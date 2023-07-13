@metadata @submission
Feature: 10 Submit Metadata
  As a data steward, I can submit research metadata into local submission registry

  Scenario: Submitting metadata

    Given we start on a clean slate
    And the metadata json file exists
    And the metadata config yaml exists

    When metadata is submitted to the submission registry
    Then a submission JSON exists in registry
    And set the state to "Metadata submission is completed"
