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

CREATE TABLE IF NOT EXISTS DefoeQueryConfigs (
  configID UUID PRIMARY KEY NOT NULL,
  collection VARCHAR(50) NOT NULL,
  queryType VARCHAR(50) NOT NULL,
  preprocess VARCHAR(50),
  lexiconFile TEXT,
  targetSentences TEXT,
  targetFilter VARCHAR(10),
  startYear INTEGER,
  endYear INTEGER,
  hitCount VARCHAR(10),
  snippetWindow INTEGER,
  gazetteer VARCHAR(20),
  boundingBox VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS DefoeQueryTasks (
  taskID UUID PRIMARY KEY NOT NULL,
  userID UUID NOT NULL,
  configID UUID NOT NULL,
  resultFile TEXT NOT NULL,
  progress SMALLINT NOT NULL DEFAULT 0,
  errorMsg VARCHAR (255) NOT NULL,

  submitTime TIMESTAMP WITHOUT TIME ZONE NOT NULL
       DEFAULT (current_timestamp AT TIME ZONE 'UTC'),

  FOREIGN KEY (userID) REFERENCES Users(userID),
  FOREIGN KEY (configID) REFERENCES DefoeQueryConfigs(configID)
);

