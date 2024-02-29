@download @auth
Feature: 30 User Registration
  Users can register themselves and then login.

  Scenario: Registration as a new user

    Given the user "Dr. John Doe" is logged out
    And the user "Dr. John Doe" is not yet registered

    Given I am logged in as "Dr. John Doe"
    Then a new session for the user "Dr. John Doe" is created
    When I retrieve my own user data
    Then the response status code is "403"

    Given I am logged in as "Dr. John Doe"
    When I am registered
    Then the response status code is "201"
    And I am authenticated with 2FA
    And the response status code is "204"
    And the user data of "Dr. John Doe" is returned

  Scenario: The data steward should be pre-registered

    Given I am logged in as "Data Steward"
    Then I am authenticated with 2FA
    And the response status code is "204"

    When I retrieve my own user data
    Then the response status code is "200"
    And the user data of "Data Steward" is returned
