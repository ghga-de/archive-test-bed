Feature: Access Request
  As a user, I can ask for access request to a given dataset.

  Scenario: Requesting access to a dataset

    Given I am logged in as "Dr. John Doe"

    When I request access to the test dataset
    Then the response status code is "201"
    And an email has been sent to "helpdesk@ghga.de"
    And an email has been sent to "john.doe@home.org"

    Given I am logged in as "Data Steward"

    When I fetch the list of access requests
    Then the response status code is "200"
    And there is one request for the test dataset from "Dr. John Doe"
    Then the status of the request from "Dr. John Doe" is "pending"

    When I allow the pending request from "Dr. John Doe"
    Then the response status code is "204"

    When I fetch the list of access requests
    Then the status of the request from "Dr. John Doe" is "allowed"
