import os
import json
import urllib.request

token = os.environ.get("GH_PROJECT_TOKEN")
owner = os.environ.get("GH_PROJECT_OWNER", "JaehwanPark")
number = int(os.environ.get("GH_PROJECT_NUMBER", 1))

query = """
query($owner: String!, $number: Int!, $cursor: String) {
  organization(login: $owner) {
    projectV2(number: $number) {
      id
      title
      items(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isArchived
          content {
            __typename
            ... on Issue {
              title
              url
              state
              assignees(first: 5) { nodes { login } }
            }
            ... on PullRequest {
              title
              url
              state
              assignees(first: 5) { nodes { login } }
            }
            ... on DraftIssue {
              title
            }
          }
          fieldValues(first: 30) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldDateValue {
                date
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldTextValue {
                text
                field { ... on ProjectV2FieldCommon { name } }
              }
            }
          }
        }
      }
    }
  }
  user(login: $owner) {
    projectV2(number: $number) {
      id
      title
      items(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isArchived
          content {
            __typename
            ... on Issue {
              title
              url
              state
              assignees(first: 5) { nodes { login } }
            }
            ... on PullRequest {
              title
              url
              state
              assignees(first: 5) { nodes { login } }
            }
            ... on DraftIssue {
              title
            }
          }
          fieldValues(first: 30) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldDateValue {
                date
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldTextValue {
                text
                field { ... on ProjectV2FieldCommon { name } }
              }
            }
          }
        }
      }
    }
  }
}
"""

variables = {"owner": owner, "number": number, "cursor": None}
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