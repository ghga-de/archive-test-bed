
@download @metadata
Feature: 20 Browsing Metadata
  As a user, I can browse the public metadata

  Background:
    Given we have the state "metadata has been loaded into the system"

  Scenario: Verify searching with invalid class
    When I query documents with invalid class name
    Then the response status code is "422"

  Scenario: Filter dataset by alias
    When I filter dataset with alias
    Then the response status code is "200"
    And I get the expected results from alias filter

  Scenario: Filter dataset by study file format
    When I filter dataset with "FASTQ" study file format
    Then the response status code is "200"
    And the expected hit count is "1"

    When I filter dataset with "BAM" study file format
    Then the response status code is "200"
    And the expected hit count is "0"

  Scenario: Filter dataset for sequencing file
    When I filter dataset with sequencing file alias
    Then the response status code is "200"
    And I get the expected results from sequencing file filter
