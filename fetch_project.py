import os
import json
import urllib.request

token = os.environ.get("GH_PROJECT_TOKEN")
owner = os.environ.get("GH_PROJECT_OWNER", "JaehwanPark")
number = int(os.environ.get("GH_PROJECT_NUMBER", 1))

query = """
query($owner: String!, $number: Int!) {
  user(login: $owner) {
    projectV2(number: $number) {
      id
      title
      items(first: 20) {
        nodes {
          id
          content {
            ... on DraftIssue {
              title
            }
            ... on Issue {
              title
              url
            }
            ... on PullRequest {
              title
              url
            }
          }
          fieldValues(first: 10) {
            nodes {
              ... on ProjectV2ItemFieldTextValue {
                text
                field { name }
              }
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { name }
              }
              ... on ProjectV2ItemFieldDateValue {
                date
                field { name }
              }
            }
          }
        }
      }
    }
  }
}
"""

variables = {"owner": owner, "number": number}
payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github+json",
    },
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        parsed = json.loads(body)
        print(json.dumps(parsed, indent=2))
except Exception as e:
    print(f"Error: {e}")