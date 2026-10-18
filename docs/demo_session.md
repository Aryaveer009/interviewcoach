# Demo sessions (LLM: mock (offline heuristic))

## Session `first` (id 1)

**[project] On your resume, for PromptShield, you say you built an open-source CLI that runs 48 attacks across 7 categories against an LLM chatbot or RAG app and reports pass/fail mapped to the OWASP Top 10 for LLM Applications. Walk me through it: what design choices did you make (for example around LLMs), what was the hardest problem, and how did you know it worked?**

> It's a tool that tests chatbots with attacks and says if they pass. The hardest part was probably the detection, I tested it a bit.

Scores: {'correctness': 3, 'depth': 1, 'clarity': 4, 'structure': 2, 'relevance': 3} → **2.6/5**

- Strongest: clarity (4/5). Biggest opportunity: depth (1/5), focus your next attempt there.

**[follow-up (depth)] Go one level deeper: why did you choose that approach over the obvious alternative, and what trade-off did it cost you?**

> I think I would just do it a similar way again, it was basically fine.

Scores: {'correctness': 1, 'depth': 1, 'clarity': 2, 'structure': 1, 'relevance': 1} → **1.2/5**

- Strongest: clarity (2/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[project] On your resume, for ModelRouter, you say you built an OpenAI-compatible proxy that routes easy queries to a cheap model and hard queries to a strong model to cut LLM costs. Walk me through it: what design choices did you make (for example around OpenAI API), what was the hardest problem, and how did you know it worked?**

> It sends questions to a cheap model or an expensive one. It took a while to build and I think it works well.

Scores: {'correctness': 1, 'depth': 1, 'clarity': 4, 'structure': 2, 'relevance': 1} → **1.8/5**

- Strongest: clarity (4/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[follow-up (correctness)] You didn't say much about: the design and why you made the choices you did around OpenAI API, a specific hard problem and how you solved it. Can you address that directly?**

> I think I would just do it a similar way again, it was basically fine.

Scores: {'correctness': 1, 'depth': 1, 'clarity': 2, 'structure': 1, 'relevance': 1} → **1.2/5**

- Strongest: clarity (2/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[technical] How would you design a REST API for a to-do app, including the endpoints, status codes and how you would handle errors and versioning?**

> You would have endpoints for getting and adding to-dos and return an error if something goes wrong.

Scores: {'correctness': 2, 'depth': 1, 'clarity': 3, 'structure': 1, 'relevance': 2} → **1.8/5**

- Strongest: clarity (3/5). Biggest opportunity: depth (1/5), focus your next attempt there.

**[follow-up (depth)] Go one level deeper: why did you choose that approach over the obvious alternative, and what trade-off did it cost you?**

> I think I would just do it a similar way again, it was basically fine.

Scores: {'correctness': 1, 'depth': 1, 'clarity': 2, 'structure': 1, 'relevance': 1} → **1.2/5**

- Strongest: clarity (2/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[technical] What causes an LLM to hallucinate, and what practical techniques would you use to reduce it in a production feature?**

> Models sometimes make things up because they aren't perfect, so you have to be careful with what they say.

Scores: {'correctness': 1, 'depth': 1, 'clarity': 3, 'structure': 1, 'relevance': 1} → **1.4/5**

- Strongest: clarity (3/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[follow-up (correctness)] You didn't say much about: models predict likely text, not verified facts, grounding answers with retrieval or provided sources. Can you address that directly?**

> I think I would just do it a similar way again, it was basically fine.

Scores: {'correctness': 1, 'depth': 1, 'clarity': 2, 'structure': 1, 'relevance': 1} → **1.2/5**

- Strongest: clarity (2/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[technical] The role asks for AWS, which doesn't appear in your projects. How would you host a small web API on AWS, and how would you secure access to it and to the database behind it? If you haven't used it, tell me how you'd approach learning it and what you already know.**

> I haven't used AWS much. I think you put the app on a server and make sure it's secure somehow.

Scores: {'correctness': 1, 'depth': 1, 'clarity': 3, 'structure': 2, 'relevance': 2} → **1.8/5**

- Strongest: clarity (3/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[follow-up (correctness)] You didn't say much about: compute choice such as EC2, ECS or Lambda, IAM roles with least privilege. Can you address that directly?**

> I think I would just do it a similar way again, it was basically fine.

Scores: {'correctness': 1, 'depth': 1, 'clarity': 2, 'structure': 1, 'relevance': 1} → **1.2/5**

- Strongest: clarity (2/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[behavioral] Tell me about a time you had to learn a new technology quickly to get something done. Use the STAR structure: Situation, Task, Action, Result.**

> I had to learn something new for a project and I just read about it and figured it out. It went fine in the end.

Scores: {'correctness': 3, 'depth': 1, 'clarity': 4, 'structure': 3, 'relevance': 3} → **2.8/5**

- Strongest: clarity (4/5). Biggest opportunity: depth (1/5), focus your next attempt there.

**[follow-up (depth)] What was the concrete, measurable result of that, and what specifically did *you* do versus the rest of the team?**

> I think I would just do it a similar way again, it was basically fine.

Scores: {'correctness': 1, 'depth': 1, 'clarity': 2, 'structure': 1, 'relevance': 1} → **1.2/5**

- Strongest: clarity (2/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[behavioral] Tell me about a time you disagreed with a teammate about a technical decision. What happened? Use the STAR structure: Situation, Task, Action, Result.**

> My teammate and I disagreed once but we talked about it and sorted it out.

Scores: {'correctness': 2, 'depth': 1, 'clarity': 4, 'structure': 2, 'relevance': 2} → **2.2/5**

- Strongest: clarity (4/5). Biggest opportunity: depth (1/5), focus your next attempt there.

**[follow-up (depth)] What was the concrete, measurable result of that, and what specifically did *you* do versus the rest of the team?**

> I think I would just do it a similar way again, it was basically fine.

Scores: {'correctness': 1, 'depth': 1, 'clarity': 2, 'structure': 1, 'relevance': 1} → **1.2/5**

- Strongest: clarity (2/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**Session summary:** {'turns': 14, 'overall': 1.63, 'by_category': {'project': 1.7, 'technical': 1.43, 'behavioral': 1.85}}

## Session `second` (id 2)

**[project] On your resume, for PromptShield, you say you built an open-source CLI that runs 48 attacks across 7 categories against an LLM chatbot or RAG app and reports pass/fail mapped to the OWASP Top 10 for LLM Applications. Walk me through it: what design choices did you make (for example around LLMs), what was the hardest problem, and how did you know it worked?**

> The design is a library of attacks, each with a detector, because I wanted new attacks to be easy to add. The hardest problem was catching leaks when the secret came back encoded, so I used a canary token. I tested it against a vulnerable demo bot.

Scores: {'correctness': 4, 'depth': 2, 'clarity': 5, 'structure': 2, 'relevance': 5} → **3.6/5**

- Strongest: clarity (5/5). Biggest opportunity: depth (2/5), focus your next attempt there.

**[follow-up (depth)] Go one level deeper: why did you choose that approach over the obvious alternative, and what trade-off did it cost you?**

> I chose that because it was simpler to maintain, although the trade-off was less flexibility, for example when adding new attack types.

Scores: {'correctness': 3, 'depth': 2, 'clarity': 5, 'structure': 2, 'relevance': 3} → **3.0/5**

- Strongest: clarity (5/5). Biggest opportunity: depth (2/5), focus your next attempt there.

**[project] On your resume, for ModelRouter, you say you built an OpenAI-compatible proxy that routes easy queries to a cheap model and hard queries to a strong model to cut LLM costs. Walk me through it: what design choices did you make (for example around OpenAI API), what was the hardest problem, and how did you know it worked?**

> It exposes an OpenAI-compatible API and routes by a difficulty classifier, because that saves cost. The hardest problem was misrouting hard questions, which I handled by escalating when the classifier was unsure. I checked it with a small benchmark.

Scores: {'correctness': 4, 'depth': 2, 'clarity': 5, 'structure': 2, 'relevance': 5} → **3.6/5**

- Strongest: clarity (5/5). Biggest opportunity: depth (2/5), focus your next attempt there.

**[follow-up (depth)] Go one level deeper: why did you choose that approach over the obvious alternative, and what trade-off did it cost you?**

> I chose that because it was simpler to maintain, although the trade-off was less flexibility, for example when adding new attack types.

Scores: {'correctness': 3, 'depth': 2, 'clarity': 5, 'structure': 2, 'relevance': 3} → **3.0/5**

- Strongest: clarity (5/5). Biggest opportunity: depth (2/5), focus your next attempt there.

**[technical] How would you design a REST API for a to-do app, including the endpoints, status codes and how you would handle errors and versioning?**

> I'd use GET /tasks to list, POST /tasks to create with a 201, PUT to update and DELETE to remove. Errors return 400 or 404 with a JSON message. I'd also add authentication with a token.

Scores: {'correctness': 5, 'depth': 2, 'clarity': 5, 'structure': 2, 'relevance': 4} → **3.6/5**

- Strongest: correctness (5/5). Biggest opportunity: depth (2/5), focus your next attempt there.

**[follow-up (depth)] Go one level deeper: why did you choose that approach over the obvious alternative, and what trade-off did it cost you?**

> I chose that because it was simpler to maintain, although the trade-off was less flexibility, for example when adding new attack types.

Scores: {'correctness': 1, 'depth': 2, 'clarity': 5, 'structure': 2, 'relevance': 1} → **2.2/5**

- Strongest: clarity (5/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[technical] What causes an LLM to hallucinate, and what practical techniques would you use to reduce it in a production feature?**

> Models predict likely text rather than facts, so they can hallucinate. You can ground answers with retrieval and tell the model to say it doesn't know. I'd also test with some example questions.

Scores: {'correctness': 4, 'depth': 2, 'clarity': 5, 'structure': 3, 'relevance': 3} → **3.4/5**

- Strongest: clarity (5/5). Biggest opportunity: depth (2/5), focus your next attempt there.

**[follow-up (depth)] Go one level deeper: why did you choose that approach over the obvious alternative, and what trade-off did it cost you?**

> I chose that because it was simpler to maintain, although the trade-off was less flexibility, for example when adding new attack types.

Scores: {'correctness': 1, 'depth': 2, 'clarity': 5, 'structure': 2, 'relevance': 1} → **2.2/5**

- Strongest: clarity (5/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[technical] The role asks for AWS, which doesn't appear in your projects. How would you host a small web API on AWS, and how would you secure access to it and to the database behind it? If you haven't used it, tell me how you'd approach learning it and what you already know.**

> I'd run the API on EC2 or Lambda and keep the database private in a VPC. Access would use IAM roles with least privilege. I haven't done this in production, only read about it.

Scores: {'correctness': 4, 'depth': 2, 'clarity': 5, 'structure': 2, 'relevance': 4} → **3.4/5**

- Strongest: clarity (5/5). Biggest opportunity: depth (2/5), focus your next attempt there.

**[follow-up (depth)] Go one level deeper: why did you choose that approach over the obvious alternative, and what trade-off did it cost you?**

> I chose that because it was simpler to maintain, although the trade-off was less flexibility, for example when adding new attack types.

Scores: {'correctness': 1, 'depth': 2, 'clarity': 5, 'structure': 2, 'relevance': 1} → **2.2/5**

- Strongest: clarity (5/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[behavioral] Tell me about a time you had to learn a new technology quickly to get something done. Use the STAR structure: Situation, Task, Action, Result.**

> In a group project I had to learn FastAPI in a week. My task was to build the backend. I read the docs, built a small prototype and asked a friend to review it. We shipped on time and I learned to prototype early.

Scores: {'correctness': 5, 'depth': 2, 'clarity': 5, 'structure': 5, 'relevance': 4} → **4.2/5**

- Strongest: correctness (5/5). Biggest opportunity: depth (2/5), focus your next attempt there.

**[behavioral] Tell me about a time you disagreed with a teammate about a technical decision. What happened? Use the STAR structure: Situation, Task, Action, Result.**

> A teammate and I disagreed about the database in our project. I suggested a quick prototype of both, we compared them, and we picked the simpler one. It worked out.

Scores: {'correctness': 3, 'depth': 1, 'clarity': 5, 'structure': 3, 'relevance': 3} → **3.0/5**

- Strongest: clarity (5/5). Biggest opportunity: depth (1/5), focus your next attempt there.

**[follow-up (depth)] What was the concrete, measurable result of that, and what specifically did *you* do versus the rest of the team?**

> I chose that because it was simpler to maintain, although the trade-off was less flexibility, for example when adding new attack types.

Scores: {'correctness': 1, 'depth': 2, 'clarity': 5, 'structure': 1, 'relevance': 1} → **2.0/5**

- Strongest: clarity (5/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**Session summary:** {'turns': 13, 'overall': 3.03, 'by_category': {'project': 3.3, 'technical': 2.83, 'behavioral': 3.07}}

## Session `third` (id 3)

**[project] On your resume, for PromptShield, you say you built an open-source CLI that runs 48 attacks across 7 categories against an LLM chatbot or RAG app and reports pass/fail mapped to the OWASP Top 10 for LLM Applications. Walk me through it: what design choices did you make (for example around LLMs), what was the hardest problem, and how did you know it worked?**

> The core design is a library of attacks defined in YAML, each paired with a detector, so adding an attack needs no new code. I chose that because I wanted all 48 attacks to be easy to review and extend. The hardest problem was detecting leaks reliably: a plain string match missed a secret that came back reversed or base64-encoded, so I planted a canary token in the system prompt and normalised responses before checking. I verified it by running the tool against a deliberately vulnerable demo bot and a hardened one and checking the scores differed, plus unit tests for each detector. Next I'd add more indirect-injection cases.

Scores: {'correctness': 5, 'depth': 4, 'clarity': 5, 'structure': 4, 'relevance': 5} → **4.6/5**

- Strongest: correctness (5/5). Biggest opportunity: depth (4/5), focus your next attempt there.

**[follow-up (stretch)] Good. Now stretch it: how would your approach change at 100x the scale or if a requirement flipped, and what would you monitor to know it was failing?**

> I chose that approach because it was simpler to test, and the trade-off was flexibility. For example, at 100x the scale I would add monitoring on error rate and latency, since that would tell me quickly if it was failing.

Scores: {'correctness': 3, 'depth': 3, 'clarity': 5, 'structure': 4, 'relevance': 3} → **3.6/5**

- Strongest: clarity (5/5). Biggest opportunity: correctness (3/5), focus your next attempt there.

**[project] On your resume, for ModelRouter, you say you built an OpenAI-compatible proxy that routes easy queries to a cheap model and hard queries to a strong model to cut LLM costs. Walk me through it: what design choices did you make (for example around OpenAI API), what was the hardest problem, and how did you know it worked?**

> The proxy exposes the same chat-completions API as OpenAI, so apps only change the base URL. I chose a simple difficulty classifier because it was cheap and I could inspect its mistakes: easy prompts go to the small model and hard ones to the strong model. The hardest problem was that misrouting a hard question hurts quality, so I added an uncertainty check that escalates to the strong model when the classifier isn't confident. I verified it by running a benchmark of labelled prompts and comparing cost and answer quality against always using the strong model. I'd improve it with more training data.

Scores: {'correctness': 5, 'depth': 4, 'clarity': 5, 'structure': 3, 'relevance': 5} → **4.4/5**

- Strongest: correctness (5/5). Biggest opportunity: structure (3/5), focus your next attempt there.

**[technical] How would you design a REST API for a to-do app, including the endpoints, status codes and how you would handle errors and versioning?**

> I'd model tasks as a resource: GET /tasks to list with pagination, POST /tasks to create returning 201, GET /tasks/{id}, PUT or PATCH to update, and DELETE returning 204. Invalid input returns 400 with a JSON error body that names the bad field, and an unknown id returns 404. I'd put the version in the path, like /v1/tasks, so the contract can change later, and protect the endpoints with token-based authentication.

Scores: {'correctness': 5, 'depth': 3, 'clarity': 5, 'structure': 2, 'relevance': 4} → **3.8/5**

- Strongest: correctness (5/5). Biggest opportunity: structure (2/5), focus your next attempt there.

**[follow-up (structure)] Walk me through it step by step: what happened first, what next, and what was the end result?**

> I chose that approach because it was simpler to test, and the trade-off was flexibility. For example, at 100x the scale I would add monitoring on error rate and latency, since that would tell me quickly if it was failing.

Scores: {'correctness': 1, 'depth': 2, 'clarity': 5, 'structure': 4, 'relevance': 1} → **2.6/5**

- Strongest: clarity (5/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[technical] What causes an LLM to hallucinate, and what practical techniques would you use to reduce it in a production feature?**

> A language model predicts the most likely next token, not a verified fact, so when it lacks knowledge it still produces fluent text that can be wrong. In production I'd ground answers in retrieved sources and instruct the model to say it doesn't know when the context lacks the answer. I'd also constrain the output format, and measure hallucination with a test set of questions with known answers, plus human review of a sample.

Scores: {'correctness': 5, 'depth': 2, 'clarity': 5, 'structure': 3, 'relevance': 4} → **3.8/5**

- Strongest: correctness (5/5). Biggest opportunity: depth (2/5), focus your next attempt there.

**[follow-up (depth)] Go one level deeper: why did you choose that approach over the obvious alternative, and what trade-off did it cost you?**

> I chose that approach because it was simpler to test, and the trade-off was flexibility. For example, at 100x the scale I would add monitoring on error rate and latency, since that would tell me quickly if it was failing.

Scores: {'correctness': 1, 'depth': 2, 'clarity': 5, 'structure': 4, 'relevance': 1} → **2.6/5**

- Strongest: clarity (5/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**[technical] The role asks for AWS, which doesn't appear in your projects. How would you host a small web API on AWS, and how would you secure access to it and to the database behind it? If you haven't used it, tell me how you'd approach learning it and what you already know.**

> I haven't run production workloads on AWS, but here is how I'd approach it. For compute I'd pick Lambda or ECS Fargate for a small API. The database would sit in a private subnet inside a VPC, reachable only through security groups from the API. Access uses IAM roles with least privilege rather than long-lived keys, secrets live in Secrets Manager, and CloudWatch collects logs for monitoring.

Scores: {'correctness': 5, 'depth': 3, 'clarity': 5, 'structure': 3, 'relevance': 5} → **4.2/5**

- Strongest: correctness (5/5). Biggest opportunity: depth (3/5), focus your next attempt there.

**[behavioral] Tell me about a time you had to learn a new technology quickly to get something done. Use the STAR structure: Situation, Task, Action, Result.**

> In my second-year group project I had to learn FastAPI within a week because our backend was blocked. My task was to deliver a working API before the demo. I read the official tutorial, built a small prototype of two endpoints, and asked a senior friend to review my approach. As a result we shipped the backend two days before the demo. I learned to build a thin prototype first and ask for review early.

Scores: {'correctness': 5, 'depth': 3, 'clarity': 5, 'structure': 5, 'relevance': 4} → **4.4/5**

- Strongest: correctness (5/5). Biggest opportunity: depth (3/5), focus your next attempt there.

**[behavioral] Tell me about a time you disagreed with a teammate about a technical decision. What happened? Use the STAR structure: Situation, Task, Action, Result.**

> In my second-year group project a teammate wanted MongoDB while I thought a relational database fit our data better. My task was to help the team choose before the next sprint. I wrote a short comparison, built a small prototype of the two core queries in both, and shared the results instead of arguing opinions. The relational version was simpler for our joins, so we went with SQLite, and we finished the sprint on time. I learned to settle disagreements with a quick experiment.

Scores: {'correctness': 5, 'depth': 3, 'clarity': 5, 'structure': 5, 'relevance': 5} → **4.6/5**

- Strongest: correctness (5/5). Biggest opportunity: depth (3/5), focus your next attempt there.

**[follow-up (stretch)] Good. Now stretch it: how would your approach change at 100x the scale or if a requirement flipped, and what would you monitor to know it was failing?**

> I chose that approach because it was simpler to test, and the trade-off was flexibility. For example, at 100x the scale I would add monitoring on error rate and latency, since that would tell me quickly if it was failing.

Scores: {'correctness': 1, 'depth': 2, 'clarity': 5, 'structure': 1, 'relevance': 2} → **2.2/5**

- Strongest: clarity (5/5). Biggest opportunity: correctness (1/5), focus your next attempt there.

**Session summary:** {'turns': 11, 'overall': 3.71, 'by_category': {'project': 4.2, 'technical': 3.4, 'behavioral': 3.73}}
