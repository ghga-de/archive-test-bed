@download @files
Feature: 32 Download files
  As a user, I can download files when I have a download token.

  Scenario: Downloading files

    Given we have the state "a download token has been created"
    And I have an empty working directory for the GHGA connector
    And my Crypt4GH key pair has been stored in two key files
