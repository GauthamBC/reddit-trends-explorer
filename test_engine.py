import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timezone
from engine import compute_heat, extract_topics, region_and_topic_filter, refers_to_region
from regions import STATES, CATEGORIES, candidate_subreddits
from reddit_client import get_credentials
from graph import build_graph

NOW = datetime.now(timezone.utc).timestamp()

def post(id, title, sub, hours=2, score=100, comments=20):
    return {"id":id, "title":title, "subreddit":sub, "created_utc":NOW-hours*3600,
            "score":score, "comments":comments, "age_hours":hours,
            "heat":compute_heat(score,comments,hours), "flair":"",
            "url":f"https://www.reddit.com/r/{sub}/comments/{id}/example/",
            "nsfw":False, "stickied":False}

def test_states():
    assert len(STATES) == 51
    assert len(CATEGORIES) >= 2
    assert all(candidate_subreddits("Sports", "NFL", name) for name in STATES)

def test_region_matching():
    assert refers_to_region("Lakers fan event in Los Angeles", "", "California")
    assert not refers_to_region("Some LA opinions", "", "California")
    assert not refers_to_region("Washington baseball game", "", "New York")
    assert refers_to_region("Lakers trade talk", "", "California", "Sports")
    assert not refers_to_region("Lakers trade talk", "", "California", "Entertainment")

def test_filter():
    submissions = [
        post("1", "Lakers head coach press conference", "lakers"),
        post("2", "Music festival tonight", "LosAngeles"),
        post("3", "Lakers playoff discussion", "nba"),
        post("4", "Los Angeles Lakers trade", "nba"),
    ]
    source = {"lakers":"team", "losangeles":"local", "nba":"global"}
    output = region_and_topic_filter(submissions, source, "Sports", "NBA", "California",24)
    assert {p["id"] for p in output} == {"1","3","4"}
    assert next(p for p in output if p["id"]=="1")["locality"] == "Team associated with state"

def test_topics_network_xss():
    sample = [post("1", "Lakers trade rumours <script>alert('x')</script>", "lakers"),
              post("2", "Lakers trade deal announced", "nba")]
    topics = extract_topics(sample)
    assert topics
    page = build_graph(sample, topics)
    assert "vis-network" in page
    assert "<script>alert" not in page

def test_credentials_legacy():
    creds = get_credentials({"REDDIT_CLIENT_ID":"abc", "REDDIT_CLIENT_SECRET":"xyz"})
    assert creds["client_id"]=="abc"
    assert creds["client_secret"]=="xyz"

def test_heat_recency():
    assert compute_heat(100,10,1) > compute_heat(100,10,40)


def test_manual_duplicate_does_not_drop_team_classification():
    candidates = candidate_subreddits("Sports", "NBA", "California", ["lakers", "NewSubExample"], cap=10)
    assert candidates[0] == {"name": "lakers", "source": "team"}
    assert candidates[1] == {"name": "NewSubExample", "source": "manual"}
