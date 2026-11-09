from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

JOB_ROLES = [
    {
        "title": "Backend Python Developer",
        "description": "python django flask fastapi sql postgresql redis docker rest api git",
    },
    {
        "title": "Frontend React Developer",
        "description": "javascript typescript react html css node.js git rest api",
    },
    {
        "title": "Machine Learning Engineer",
        "description": "python machine learning deep learning pytorch tensorflow scikit-learn pandas numpy nlp",
    },
    {
        "title": "Data Analyst",
        "description": "python sql pandas numpy data analysis data science scikit-learn",
    },
    {
        "title": "DevOps Engineer",
        "description": "docker kubernetes aws gcp azure terraform linux ci/cd git",
    },
    {
        "title": "Full Stack Developer",
        "description": "javascript typescript react node.js python sql postgresql html css git docker",
    },
    {
        "title": "NLP Engineer",
        "description": "python nlp machine learning deep learning pytorch spacy transformers",
    },
    {
        "title": "QA Automation Engineer",
        "description": "python selenium playwright rest api git ci/cd agile",
    },
]


def match_resume_to_roles(resume_skills: list[str], top_k: int = 5) -> list[dict]:
    if not resume_skills:
        return []

    resume_doc = " ".join(resume_skills)
    role_docs = [role["description"] for role in JOB_ROLES]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resume_doc] + role_docs)

    resume_vec = tfidf_matrix[0:1]
    role_vecs = tfidf_matrix[1:]

    scores = cosine_similarity(resume_vec, role_vecs).flatten()

    results = []
    for i, role in enumerate(JOB_ROLES):
        results.append({
            "title": role["title"],
            "score": round(float(scores[i]), 4),
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]