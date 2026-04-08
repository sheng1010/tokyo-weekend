import warnings

import requests


def create_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    session.verify = False
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    return session
