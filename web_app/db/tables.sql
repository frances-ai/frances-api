-- Create tables
CREATE TABLE IF NOT EXISTS Users (
  userID UUID PRIMARY KEY NOT NULL,
  firstName VARCHAR (255) NOT NULL,
  lastName VARCHAR (255) NOT NULL,
  email VARCHAR (255) NOT NULL UNIQUE,
  password TEXT NOT NULL,
  createdAt TIMESTAMP WITHOUT TIME ZONE NOT NULL
                                   DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
  updatedAt TIMESTAMP WITHOUT TIME ZONE,
  status VARCHAR (20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'pending', 'deleted'))
);

CREATE TABLE IF NOT EXISTS Submissions (
  submissionID UUID PRIMARY KEY NOT NULL,
  userID UUID NOT NULL,
  submissionName VARCHAR (255) NOT NULL,
  result TEXT NOT NULL,
  error VARCHAR (255) NOT NULL,

  submitTime TIMESTAMP WITHOUT TIME ZONE NOT NULL
       DEFAULT (current_timestamp AT TIME ZONE 'UTC'),

  FOREIGN KEY (userID) REFERENCES Users(userID)
);

