"""A small, hand-written skills taxonomy used by both resume and JD parsing.

Matching is purely lexical (word-boundary regex over aliases), which keeps
parsing deterministic, offline and private. Each skill has a *family*; two
skills in the same family are "related", which is what lets the gap analysis
say "partly covered" (e.g. the JD asks for PostgreSQL, the resume lists SQLite).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class Skill:
    name: str  # canonical display name
    family: str
    aliases: tuple[str, ...] = field(default_factory=tuple)
    implies: tuple[str, ...] = field(default_factory=tuple)  # canonical names


def _s(name: str, family: str, *aliases: str, implies: tuple[str, ...] = ()) -> Skill:
    return Skill(name, family, tuple(a.lower() for a in (name, *aliases)), implies)


SKILLS: tuple[Skill, ...] = (
    # languages
    _s("Python", "python-lang"),
    _s("Java", "jvm"),
    _s("JavaScript", "web-lang", "js"),
    _s("TypeScript", "web-lang", "ts"),
    _s("C++", "systems-lang"),
    _s("C#", "dotnet"),
    _s("Go", "systems-lang", "golang"),
    _s("Rust", "systems-lang"),
    _s("Bash", "scripting", "shell scripting", "shell"),
    _s("SQL", "relational-db", "structured query language"),
    # python / web frameworks
    _s("FastAPI", "python-web", implies=("Python",)),
    _s("Flask", "python-web", implies=("Python",)),
    _s("Django", "python-web", implies=("Python",)),
    _s("Streamlit", "python-web", implies=("Python",)),
    _s("React", "web-frontend", "react.js", "reactjs"),
    _s("Node.js", "web-lang", "nodejs", "node js"),
    _s("REST APIs", "api-design", "rest api", "restful", "restful apis", "rest"),
    _s("Microservices", "architecture"),
    _s("System Design", "architecture", "distributed systems"),
    _s("Data Structures & Algorithms", "cs-fundamentals", "data structures",
       "algorithms", "dsa"),
    # ML / AI
    _s("Machine Learning", "ml", "ml"),
    _s("Deep Learning", "ml"),
    _s("PyTorch", "ml", implies=("Machine Learning",)),
    _s("TensorFlow", "ml", implies=("Machine Learning",)),
    _s("scikit-learn", "ml", "sklearn", implies=("Machine Learning",)),
    _s("NLP", "genai", "natural language processing"),
    _s("LLMs", "genai", "llm", "large language models", "large language model",
       "generative ai", "genai"),
    _s("RAG", "genai", "retrieval-augmented generation", "retrieval augmented generation",
       implies=("LLMs",)),
    _s("Prompt Engineering", "genai", "prompt design"),
    _s("Embeddings", "genai", "embedding", "vector embeddings"),
    _s("Vector Databases", "genai", "vector database", "vector db", "faiss", "chromadb",
       "chroma", "pinecone", "pgvector", "weaviate", "qdrant"),
    _s("LangChain", "genai", implies=("LLMs",)),
    _s("LlamaIndex", "genai", implies=("LLMs",)),
    _s("OpenAI API", "genai", "openai", implies=("LLMs",)),
    _s("Hugging Face", "genai", "huggingface", "transformers"),
    _s("Fine-tuning", "genai", "fine tuning", "finetuning", "lora"),
    _s("MLOps", "devops"),
    _s("Data Analysis", "data", "data analytics", "exploratory data analysis", "eda"),
    _s("Pandas", "data", implies=("Python",)),
    _s("NumPy", "data", implies=("Python",)),
    _s("ETL", "data", "data pipelines", "data pipeline"),
    _s("Spark", "data", "pyspark", "apache spark"),
    # databases
    _s("PostgreSQL", "relational-db", "postgres", implies=("SQL",)),
    _s("MySQL", "relational-db", implies=("SQL",)),
    _s("SQLite", "relational-db", implies=("SQL",)),
    _s("MongoDB", "nosql-db", "mongo"),
    _s("Redis", "nosql-db"),
    _s("Elasticsearch", "nosql-db", "opensearch"),
    # cloud / devops
    _s("Docker", "containers", "containerization", "containers"),
    _s("Kubernetes", "containers", "k8s"),
    _s("AWS", "cloud", "amazon web services", "ec2", "s3", "lambda"),
    _s("Azure", "cloud"),
    _s("GCP", "cloud", "google cloud"),
    _s("CI/CD", "devops", "github actions", "gitlab ci", "jenkins", "continuous integration"),
    _s("Git", "vcs", "github", "gitlab", "version control"),
    _s("Linux", "os", "unix"),
    _s("Terraform", "iac", "infrastructure as code", "iac"),
    # testing
    _s("pytest", "testing", "unit testing", "unit tests", "test-driven development", "tdd"),
    # security
    _s("Cybersecurity", "security", "cyber security", "information security", "infosec",
       "application security", "appsec"),
    _s("OWASP", "security", "owasp top 10"),
    _s("Penetration Testing", "security", "pentesting", "pen testing", "pen-testing",
       "ethical hacking"),
    _s("Vulnerability Assessment", "security", "vulnerability scanning",
       "vulnerability management"),
    _s("Threat Modeling", "security", "threat modelling"),
    _s("Network Security", "security", "firewalls", "intrusion detection"),
    _s("SIEM", "security", "splunk", "log analysis"),
    _s("Cryptography", "security", "encryption", "tls", "pki"),
    _s("Incident Response", "security", "incident handling", "soc"),
    _s("Prompt Injection", "security", "jailbreak", "llm security", "red teaming", "red-teaming"),
    _s("Burp Suite", "security-tools"),
    _s("Nmap", "security-tools"),
    _s("Wireshark", "security-tools"),
    _s("Metasploit", "security-tools"),
    # practices
    _s("Agile", "practices", "scrum", "kanban"),
    _s("Technical Writing", "practices", "documentation"),
)

SKILLS_BY_NAME: dict[str, Skill] = {s.name: s for s in SKILLS}


def _alias_pattern(alias: str) -> re.Pattern[str]:
    # (?<![\w+#.]) / (?![\w+#]) so "java" never matches inside "javascript"
    # and "c++"/"c#"/"node.js" match as whole tokens.
    return re.compile(r"(?<![\w+#.])" + re.escape(alias) + r"(?![\w+#])", re.IGNORECASE)


@lru_cache(maxsize=1)
def _patterns() -> tuple[tuple[Skill, tuple[re.Pattern[str], ...]], ...]:
    return tuple((s, tuple(_alias_pattern(a) for a in s.aliases)) for s in SKILLS)


def extract_skills(text: str) -> list[str]:
    """Canonical skill names found in ``text`` (document order, de-duplicated)."""
    hits: list[tuple[int, str]] = []
    for skill, pats in _patterns():
        positions = [m.start() for p in pats if (m := p.search(text))]
        if positions:
            hits.append((min(positions), skill.name))
    hits.sort()
    return [name for _, name in hits]


def expand_implied(skills: set[str]) -> set[str]:
    """Add skills that are implied by others (PostgreSQL -> SQL)."""
    out = set(skills)
    for name in list(skills):
        skill = SKILLS_BY_NAME.get(name)
        if skill:
            out.update(skill.implies)
    return out


def family_of(name: str) -> str | None:
    skill = SKILLS_BY_NAME.get(name)
    return skill.family if skill else None


def count_mentions(text: str, skill_name: str) -> int:
    """How many times ``skill_name`` (any alias) is mentioned in ``text``."""
    for skill, pats in _patterns():
        if skill.name == skill_name:
            return sum(len(p.findall(text)) for p in pats)
    return 0
