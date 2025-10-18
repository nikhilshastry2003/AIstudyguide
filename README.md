whats this project?
-> User askes a question or promt to any related subjects, The ai what we have now (gpt, gemini, deepseeek, perplex) this gives broad answers, and the problem is we should be more specific everytime>
this project solves this, by collecting answers from all the ai models, cleans it and structres it accordingly and give back the users an proper structured guide



1. Built database using postgrsql, created few tabels for user auth, table to store raw text from ai, user promts, sessions and structred resource/guide.
2. used fast api for backend.
3. built data pipelines, which takes the user promt, sends to different ai model( for now only gemini/ others ask money).
collects all the raw information given by the gemini.
a cleanr.py file scleans the text/ removes dups and normalizes it.
and using json(which is there inside py code structres the cleaned text mahing it a proper guide.
And sends the strcutred guide to the user back

the frontend is not done yet, and each of these steps get stored in the database.

Here is the Databse tables for yout ref

-- Users table
CREATE TABLE studyguide.users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(200) UNIQUE NOT NULL,
    name VARCHAR(200),
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Subjects (a user creates subjects)
CREATE TABLE studyguide.subjects (
    subject_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES studyguide.users(user_id) ON DELETE CASCADE,
    subject_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sessions (belong to a subject)
CREATE TABLE studyguide.sessions (
    session_id SERIAL PRIMARY KEY,
    subject_id INT REFERENCES studyguide.subjects(subject_id) ON DELETE CASCADE,
    title VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Resources (optional: can belong to a subject)
CREATE TABLE studyguide.resources (
    resource_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES studyguide.users(user_id) ON DELETE CASCADE,
    subject_id INT REFERENCES studyguide.subjects(subject_id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- pdf, url, note
    file_path TEXT,                     -- uploaded file
    url TEXT,                           -- online link
    raw_text TEXT,                      -- extracted text
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Chats (belong to a session, optionally tied to a resource)
CREATE TABLE studyguide.chats (
    chat_id SERIAL PRIMARY KEY,
    session_id INT REFERENCES studyguide.sessions(session_id) ON DELETE CASCADE,
    resource_id INT REFERENCES studyguide.resources(resource_id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    answer TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);



CREATE SCHEMA IF NOT EXISTS pipeline;

CREATE TABLE pipeline.jobs (
  job_id SERIAL PRIMARY KEY,
  user_id INT REFERENCES studyguide.users(user_id) ON DELETE SET NULL,
  session_id INT REFERENCES studyguide.sessions(session_id) ON DELETE SET NULL,
  prompt TEXT NOT NULL,
  prompt_hash TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  attempt INT DEFAULT 0,
  max_attempts INT DEFAULT 3,
  result_guide_id INT,
  error TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pipeline.provider_outputs (
  output_id SERIAL PRIMARY KEY,
  job_id INT REFERENCES pipeline.jobs(job_id) ON DELETE CASCADE,
  provider VARCHAR(100) NOT NULL,
  model VARCHAR(100),
  output_json JSONB,
  output_text TEXT,
  tokens_used INT,
  latency_ms INT,
  error TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pipeline.guides (
  guide_id SERIAL PRIMARY KEY,
  job_id INT REFERENCES pipeline.jobs(job_id) ON DELETE CASCADE,
  user_id INT,
  session_id INT,
  guide_json JSONB,
  summary TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);



Anyhow the error is dict is un hashable.
and yes thats it

to dear dumboo
