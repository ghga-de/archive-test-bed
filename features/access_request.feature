Feature: Access Request
  As a user, I can ask for access request to a given dataset.

Scenario: Requesting access to a dataset
  Given I am logged in as "Dr. John Doe"
  When I request access to the test dataset
  Then the response status code is "201"
  And an email has been sent to "helpdesk@ghga.de"
  And an email has been sent to "john.doe@home.org"
