@download @auth
Feature: 30 User Registration
  Users can register themselves and then login.

  Background:
    Given the user "Dr. John Doe" is logged out
    And the user "Data Steward" is logged out
    And the session store is empty
    And the TOTP token store is empty

  Scenario: Attempt to access user data before registration
    Given the user "Dr. John Doe" is not yet registered

    When "Dr. John Doe" retrieves their user data
    Then the response status code is "403"

    Given I am logged in as "Dr. John Doe"
    When "Dr. John Doe" retrieves their user data
    Then the response status code is "404"

  Scenario: Successful registration of a new user

    Given I am logged in as "Dr. John Doe"
    When "Dr. John Doe" registers as a new user
    Then the response status code is "201"
    And the user data of "Dr. John Doe" is returned

  Scenario: Access user data after authentication

    Given I am logged in as "Dr. John Doe"
    And I am registered as "Dr. John Doe"
    And I am authenticated as "Dr. John Doe"
    Then the response status code is "204"

    When "Dr. John Doe" retrieves their user data
    Then the user data of "Dr. John Doe" is returned

  Scenario: The data steward should be pre-registered

    Given I am logged in as "Data Steward"
    And I am authenticated as "Data Steward"
    Then the response status code is "204"

    When "Data Steward" retrieves their user data
    Then the response status code is "200"
    And the user data of "Data Steward" is returned
