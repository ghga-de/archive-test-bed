
@download @metadata
Feature: 20 Browse Metadata
  As a user, I can browse the public metadata

  Scenario: Viewing the details of a dataset

    Given we have the state "metadata has been loaded into the system"

    When I request info on all available artifacts
    Then the response status code is "200"
    And I get the expected info on all the artifacts

    When I request info on the "embedded_public" artifact
    Then the response status code is "200"
    And I get the expected info on the "embedded_public" artifact

    When I request info on the "non_existing" artifact
    Then the response status code is "404"

    When I request the embedded public test dataset resource
    Then the response status code is "200"
    And the test dataset resource is returned in embedded form
