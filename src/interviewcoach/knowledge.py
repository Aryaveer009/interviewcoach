"""Offline question bank used by the mock LLM (and as a fallback hint source).

Each technical entry is a question plus the points a good answer should hit; each point
carries a few keywords so the offline scorer can check coverage. In live-LLM mode the model
writes questions and expected points itself and this bank is not consulted.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import ExpectedPoint


@dataclass(frozen=True)
class Bank:
    question: str
    points: tuple[tuple[str, tuple[str, ...]], ...]


def _b(question: str, *points: tuple[str, tuple[str, ...]]) -> Bank:
    return Bank(question, points)


TECHNICAL: dict[str, Bank] = {
    "Python": _b(
        "Explain the difference between a list, a tuple and a generator in Python, and when you "
        "would pick each one.",
        ("lists are mutable, tuples immutable", ("mutable", "immutable")),
        ("generators produce values lazily", ("lazy", "lazily", "yield", "on demand")),
        ("memory impact of generators on large data", ("memory", "large", "stream")),
        ("a concrete use case for each", ("for example", "e.g", "such as", "use case", "when i")),
    ),
    "SQL": _b(
        "You have orders and customers tables. How would you find the top 5 customers by total "
        "spend last month, and how would you make that query fast?",
        ("join the tables and aggregate with GROUP BY", ("join", "group by", "sum")),
        ("filter the date range and order/limit the result", ("where", "order by", "limit",
                                                              "between")),
        ("indexes on join/filter columns", ("index", "indices")),
        ("inspecting the query plan", ("explain", "query plan", "execution plan")),
    ),
    "LLMs": _b(
        "What causes an LLM to hallucinate, and what practical techniques would you use to reduce "
        "it in a production feature?",
        ("models predict likely text, not verified facts", ("probab", "predict", "next token",
                                                              "not verified")),
        ("grounding answers with retrieval or provided sources", ("ground", "retriev", "rag",
                                                                    "source", "context")),
        ("prompting and constraints such as 'say I don't know'", ("prompt", "instruction",
                                                                   "don't know", "constrain")),
        ("evaluation or human review of outputs", ("evaluat", "test", "review", "metric",
                                                    "benchmark")),
    ),
    "RAG": _b(
        "Walk me through how you would build a retrieval-augmented generation pipeline over a set "
        "of PDFs, and how you would check that retrieval is actually working.",
        ("chunking the documents", ("chunk", "split", "segment")),
        ("embeddings stored in a vector index", ("embedding", "vector", "faiss", "index")),
        ("retrieve top-k and pass them as context to the LLM", ("top-k", "top k", "similar",
                                                                 "context", "prompt")),
        ("measuring retrieval quality, e.g. recall/precision on labelled questions",
         ("recall", "precision", "evaluat", "metric", "labelled", "labeled", "test set")),
    ),
    "OWASP": _b(
        "Pick two items from the OWASP Top 10 (web or LLM) and explain how each attack works and "
        "how you would defend against it.",
        ("names two specific OWASP items", ("injection", "broken access", "xss", "ssrf",
                                             "insecure", "leakage", "misconfiguration")),
        ("explains the attack mechanism", ("attacker", "exploit", "malicious", "untrusted")),
        ("gives a concrete mitigation", ("validate", "sanitize", "sanitise", "parameterized",
                                          "least privilege", "escape", "encode")),
        ("mentions testing or detection", ("test", "scan", "log", "monitor")),
    ),
    "Prompt Injection": _b(
        "What is prompt injection, what is the difference between direct and indirect injection, "
        "and how would you defend an LLM app against it?",
        ("untrusted input overrides the developer's instructions", ("override", "ignore",
                                                                     "instruction", "untrusted")),
        ("indirect injection arrives via retrieved docs, emails or web pages",
         ("indirect", "document", "web page", "retriev", "email")),
        ("layered defences: least privilege, output filtering, separating data from instructions",
         ("least privilege", "filter", "sandbox", "separate", "allowlist", "guardrail")),
        ("testing the app with attack suites", ("test", "red team", "attack", "evaluate")),
    ),
    "REST APIs": _b(
        "How would you design a REST API for a to-do app, including the endpoints, status codes "
        "and how you would handle errors and versioning?",
        ("resource-oriented endpoints with HTTP verbs", ("get", "post", "put", "delete", "patch",
                                                          "resource")),
        ("meaningful status codes", ("200", "201", "400", "404", "status code")),
        ("consistent error format and validation", ("error", "validat", "message")),
        ("versioning, pagination or auth", ("version", "paginat", "auth", "token")),
    ),
    "Docker": _b(
        "What is the difference between a Docker image and a container, and how would you keep an "
        "image small and secure?",
        ("an image is a read-only template, a container is a running instance",
         ("template", "instance", "running", "read-only", "layer")),
        ("small base images and multi-stage builds", ("multi-stage", "slim", "alpine",
                                                       "base image", "small")),
        ("run as non-root and avoid baking in secrets", ("non-root", "root", "secret", "user")),
        ("scanning images or pinning versions", ("scan", "pin", "version", "trivy", "vulnerab")),
    ),
    "Kubernetes": _b(
        "Explain what a pod, a deployment and a service are in Kubernetes, and how a rolling "
        "update works.",
        ("a pod is the smallest unit running containers", ("pod", "container")),
        ("a deployment manages replicas declaratively", ("deployment", "replica", "declarative")),
        ("a service gives stable networking to pods", ("service", "stable", "load balanc", "dns")),
        ("rolling update replaces pods gradually", ("rolling", "gradual", "rollback", "zero")),
    ),
    "Git": _b(
        "You and a teammate changed the same lines in a file and now there is a merge conflict. "
        "How do you resolve it, and what is the difference between merge and rebase?",
        ("open conflict markers and decide the correct result", ("marker", "<<<", "resolve",
                                                                  "conflict")),
        ("test and commit the resolution", ("test", "commit", "continue")),
        ("merge keeps history with a merge commit", ("merge commit", "history", "preserve")),
        ("rebase rewrites commits linearly; do not rebase shared branches",
         ("rewrite", "linear", "shared", "force")),
    ),
    "CI/CD": _b(
        "Describe a CI/CD pipeline you would set up for a Python service. What stages would it "
        "have and what should block a merge?",
        ("lint and type-check", ("lint", "ruff", "mypy", "flake8", "type")),
        ("run automated tests", ("test", "pytest", "coverage")),
        ("build an artifact or container image", ("build", "docker", "image", "artifact")),
        ("deploy with approvals or rollback", ("deploy", "rollback", "approval", "staging")),
    ),
    "Threat Modeling": _b(
        "How would you threat-model a new chatbot feature that can read a user's documents?",
        ("identify assets and trust boundaries", ("asset", "trust boundar", "data flow")),
        ("enumerate threats using a framework such as STRIDE", ("stride", "spoof", "tamper",
                                                                 "threat")),
        ("rate risk by likelihood and impact", ("likelihood", "impact", "risk", "priorit")),
        ("define mitigations and who owns them", ("mitigat", "control", "owner", "fix")),
    ),
    "PostgreSQL": _b(
        "What kinds of indexes does PostgreSQL support and how would you decide whether to add "
        "one?",
        ("B-tree is the default; others like GIN/GiST/hash exist", ("b-tree", "btree", "gin",
                                                                      "gist", "hash")),
        ("use EXPLAIN ANALYZE to see scans", ("explain", "analyze", "seq scan", "query plan")),
        ("trade-off: faster reads vs slower writes and storage", ("write", "storage", "trade",
                                                                    "overhead")),
        ("selectivity / the columns used in filters and joins", ("selectiv", "filter", "join",
                                                                  "where")),
    ),
    "AWS": _b(
        "How would you host a small web API on AWS, and how would you secure access to it and to "
        "the database behind it?",
        ("compute choice such as EC2, ECS or Lambda", ("ec2", "ecs", "lambda", "fargate")),
        ("IAM roles with least privilege", ("iam", "least privilege", "role", "policy")),
        ("network isolation with VPC and security groups", ("vpc", "security group", "subnet",
                                                             "private")),
        ("secrets management and logging", ("secret", "kms", "cloudwatch", "log")),
    ),
    "Terraform": _b(
        "What problem does Terraform solve and what is the role of state?",
        ("declarative infrastructure as code", ("declarative", "infrastructure as code", "iac",
                                                 "code")),
        ("plan then apply workflow", ("plan", "apply")),
        ("state tracks real resources and should be stored remotely and locked",
         ("state", "remote", "lock", "backend")),
        ("modules or environments for reuse", ("module", "environment", "reuse", "workspace")),
    ),
    "Penetration Testing": _b(
        "Walk me through how you would approach a basic penetration test of a web application you "
        "have written permission to test.",
        ("scope and authorisation first", ("scope", "permission", "authori", "rules of engagement")),
        ("recon and enumeration", ("recon", "enumerat", "nmap", "discover")),
        ("testing for common vulnerabilities", ("injection", "xss", "auth", "burp", "vulnerab")),
        ("reporting with severity and remediation", ("report", "severity", "remediat", "fix")),
    ),
    "Machine Learning": _b(
        "Explain overfitting: how do you detect it and what can you do about it?",
        ("model fits training noise and generalises poorly", ("generali", "noise", "memoriz",
                                                                "training")),
        ("detect via train/validation gap", ("validation", "gap", "hold-out", "holdout",
                                              "cross-valid")),
        ("regularisation, more data or simpler model", ("regulari", "more data", "simpler",
                                                          "dropout", "early stopping")),
        ("a metric appropriate to the task", ("accuracy", "precision", "recall", "f1", "auc")),
    ),
    "Embeddings": _b(
        "What is an embedding, how do you compare two of them, and where have you seen them used?",
        ("dense vector capturing meaning", ("vector", "dense", "meaning", "semantic")),
        ("cosine similarity or dot product", ("cosine", "dot product", "similarity", "distance")),
        ("use cases such as search or clustering", ("search", "cluster", "recommend", "retriev")),
        ("limitations such as domain mismatch or dimension cost", ("limit", "domain", "dimension",
                                                                     "cost")),
    ),
    "FastAPI": _b(
        "How does FastAPI use type hints and Pydantic, and how would you add authentication to an "
        "endpoint?",
        ("type hints drive validation and docs", ("type hint", "validat", "openapi", "docs")),
        ("Pydantic models for request/response", ("pydantic", "model", "schema")),
        ("dependency injection for auth", ("depends", "dependency", "oauth", "jwt", "token")),
        ("async endpoints or testing with TestClient", ("async", "testclient", "test")),
    ),
    "Cybersecurity": _b(
        "Explain the CIA triad and give one example of a control for each element.",
        ("confidentiality, integrity, availability named", ("confidential", "integrity",
                                                             "availab")),
        ("confidentiality example such as encryption or access control", ("encrypt",
                                                                           "access control")),
        ("integrity example such as hashing or signatures", ("hash", "checksum", "signature")),
        ("availability example such as redundancy or backups", ("redundan", "backup", "failover")),
    ),
}

GENERIC_POINTS = (
    ("an accurate definition", ("is a", "is the", "means", "refers", "defined")),
    ("a concrete example or use case", ("for example", "e.g", "such as", "use case",
                                              "i used", "i built")),
    ("a trade-off or limitation", ("trade-off", "tradeoff", "downside", "limitation",
                                             "however", "but")),
    ("a pitfall or best practice", ("pitfall", "best practice", "avoid", "mistake",
                                             "careful")),
)


def technical_bank(skill: str) -> Bank:
    if skill in TECHNICAL:
        return TECHNICAL[skill]
    return Bank(
        f"Explain {skill} to a teammate who has never used it: what is it for, how have you used "
        "it, and what are its trade-offs?",
        tuple((d, k + (skill.lower(),) if i == 0 else k) for i, (d, k) in enumerate(GENERIC_POINTS)),
    )


def to_expected(points: tuple[tuple[str, tuple[str, ...]], ...]) -> list[ExpectedPoint]:
    return [ExpectedPoint(description=d, keywords=list(k)) for d, k in points]


BEHAVIORAL: dict[str, str] = {
    "learning quickly": "Tell me about a time you had to learn a new technology quickly to get "
                        "something done.",
    "conflict": "Tell me about a time you disagreed with a teammate about a technical decision. "
                "What happened?",
    "failure": "Describe a project or task that did not go the way you planned. What did you do "
               "about it?",
    "deadline pressure": "Tell me about a time you had too much to do and a deadline approaching. "
                         "How did you decide what to do first?",
    "ownership": "Tell me about a time you took ownership of something nobody asked you to fix.",
    "feedback": "Tell me about a time you received critical feedback on your work. How did you "
                "respond?",
}

STAR_POINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("the situation and context", ("situation", "context", "when i was", "at the time",
                                         "project", "team", "we were")),
    ("the task or goal you owned", ("task", "goal", "responsib", "needed to", "had to",
                                             "my job")),
    ("your own specific actions", ("i decided", "i built", "i wrote", "i asked",
                                               "i set", "i led", "i started", "i created",
                                               "i proposed", "i suggested", "i tested", "i ran",
                                               "i made", "i organi", "i took")),
    ("a concrete, ideally measurable result", ("result", "outcome", "%", "improved",
                                                          "reduced", "increased", "shipped",
                                                          "saved", "delivered")),
    ("what you learned", ("learned", "learnt", "lesson", "next time", "would do",
                                        "differently")),
)
