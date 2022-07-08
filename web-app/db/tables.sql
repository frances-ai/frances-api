-- Drop all tables, Test and development environment only
DROP TABLE IF EXISTS Submissions;
DROP TABLE IF EXISTS Users;

-- Create tables
CREATE TABLE IF NOT EXISTS Users (
  UserID UUID PRIMARY KEY NOT NULL,
  FullName VARCHAR (255) NOT NULL,
  Email VARCHAR (255) NOT NULL UNIQUE,
  Password TEXT NOT NULL,
  CreatedAt TIMESTAMP WITHOUT TIME ZONE NOT NULL
    DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
  UpdatedAt TIMESTAMP WITHOUT TIME ZONE,
  Status VARCHAR (255) NOT NULL DEFAULT 'active' CHECK (Status IN ('active', 'pending', 'deleted'))
);

CREATE TABLE IF NOT EXISTS Submissions (
  SubmissionID UUID PRIMARY KEY NOT NULL,
  UserID UUID NOT NULL,
  FullName VARCHAR (255) NOT NULL,
  Result text NOT NULL,
  Error VARCHAR (255) NOT NULL,

  SubmitTime TIMESTAMP WITHOUT TIME ZONE NOT NULL
  DEFAULT (current_timestamp AT TIME ZONE 'UTC'),

  FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

