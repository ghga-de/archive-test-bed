
@download @metadata
Feature: 20 Browsing Metadata
  As a user, I can browse the public metadata

  Background:
    Given we have the state "metadata has been loaded into the system"

  Scenario: Verify searching with invalid class
    When I query documents with invalid class name
    Then the response status code is "422"
