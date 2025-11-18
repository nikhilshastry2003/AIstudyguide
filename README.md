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

