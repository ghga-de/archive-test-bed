@download @ars
Feature: 31 Access Request
  As a user, I can ask for access request to a given dataset.

  Background:
    Given the user "Dr. John Doe" is logged out
    And the session store is empty

  Scenario: Requesting access to a dataset

    Given we have the state "metadata has been loaded into the system"
    And the claims repository is empty
    And no access requests have been made yet
    And I am registered as "Dr. John Doe"

    Given I am logged in as "Dr. John Doe"
    And I am authenticated as "Dr. John Doe"
    And the response status code is "204"

    When "Dr. John Doe" requests access to the test dataset "DS_A"
    Then the response status code is "201"
    And an email has been sent to "helpdesk@ghga.de"
    And an email has been sent to "john.doe@home.org"

  Scenario: Granting access to a dataset

    Given I am logged in as "Data Steward"
    And I am authenticated as "Data Steward"
    Then the response status code is "204"

    When "Data Steward" fetches the list of access requests
    Then the response status code is "200"
    And there is one request for test dataset "DS_A" from "Dr. John Doe"
    Then the status of the request from "Dr. John Doe" is "pending"

    When "Data Steward" allows the pending request from "Dr. John Doe"
    Then the response status code is "204"

    When "Data Steward" fetches the list of access requests
    Then the status of the request from "Dr. John Doe" is "allowed"
    And set the state to "John Doe is allowed to download the test dataset"
