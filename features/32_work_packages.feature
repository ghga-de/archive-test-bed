@download @wps
Feature: 32 Work Packages
  As a user, I can create a work package for downloading a file
  and a download token corresponding ot that work package.

  Background:
    Given we have the state "John Doe is allowed to download the test dataset"
    And I am registered as "Dr. John Doe"
    And I am logged in as "Dr. John Doe"
    And I am authenticated as "Dr. John Doe"

  Scenario: Starting work package creation
    Given no work packages have been created yet
    And the test datasets have been announced

  Scenario: Creating work package for all files
    When "Dr. John Doe" lists the datasets
    Then the response status code is "200"
    And only the test dataset "A" is returned

    When "Dr. John Doe" creates a work package for "all" files in test dataset
    Then the response status code is "201"
    And the response contains a download token for "all" files

  Scenario: Creating work package for only vcf files
    When "Dr. John Doe" lists the datasets
    Then the response status code is "200"
    And only the test dataset "A" is returned

    When "Dr. John Doe" creates a work package for "vcf" files in test dataset
    Then the response status code is "201"
    And the response contains a download token for "vcf" files
