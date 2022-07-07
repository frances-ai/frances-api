CREATE TABLE IF NOT EXISTS Users (
  UserID UUID PRIMARY KEY NOT NULL,
  Name varchar(255) NOT NULL,
  Email varchar(255) NOT NULL UNIQUE,
  Password varchar(255) NOT NULL,
  Status varchar(255) NOT NULL DEFAULT 'active' CHECK (Status in ('active', 'pending', 'deleted'))
);

CREATE TABLE IF NOT EXISTS Submissions (
  SubmissionID UUID PRIMARY KEY NOT NULL,
  UserID UUID NOT NULL,
  Name varchar(255) NOT NULL,
  Result text NOT NULL,
  Error varchar(255) NOT NULL,

  SubmitTime TIMESTAMP WITHOUT TIME ZONE NOT NULL
  DEFAULT (current_timestamp AT TIME ZONE 'UTC'),

  FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

