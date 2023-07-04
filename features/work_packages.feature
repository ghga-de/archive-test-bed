Feature: Work Packages
  As a user, I can create a work package for downloading a file
  and a download token corresponding ot that work package.

Scenario: Creating a download token
  Given a dataset has been announced
  When the list of datasets is queried
  Then the response status is "200"
  And the dataset is in the response list
