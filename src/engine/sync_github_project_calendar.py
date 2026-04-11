"""Sync GitHub Project v2 items to Google Calendar events.

This script is designed for one-way sync:
GitHub Project (source of truth) -> Google Calendar.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from urllib import request


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar"


@dataclass
class ProjectItem:
    item_id: str
    content_type: str
    title: str
    url: str
    due_date: str
    status: str
    track: str
    assignees: str
    state: str


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"missing required env: {name}")
    return value


def _env_bool(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "true" if default else "false")).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def _graphql_query() -> str:
    return """
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
""".strip()


def _graphql_request(token: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = request.Request(
        GITHUB_GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    parsed = json.loads(body)
    if parsed.get("errors"):
        raise RuntimeError(f"github graphql errors: {parsed['errors']}")
    return parsed["data"]


def _project_node(data: dict[str, Any]) -> dict[str, Any]:
    org_node = (data.get("organization") or {}).get("projectV2")
    user_node = (data.get("user") or {}).get("projectV2")
    node = org_node or user_node
    if not node:
        raise RuntimeError("project not found. check GH_PROJECT_OWNER / GH_PROJECT_NUMBER / token scope")
    return node


def _parse_project_item(
    node: dict[str, Any],
    *,
    due_field_name: str,
    status_field_name: str,
    track_field_name: str,
) -> ProjectItem | None:
    if bool(node.get("isArchived")):
        return None

    content = node.get("content") or {}
    content_type = str(content.get("__typename") or "Unknown")

    title = str(content.get("title") or "").strip()
    if not title:
        title = "(untitled)"

    url = str(content.get("url") or "").strip()
    state = str(content.get("state") or "").strip()
    assignees_nodes = ((content.get("assignees") or {}).get("nodes") or []) if content else []
    assignees = ", ".join(str(n.get("login") or "").strip() for n in assignees_nodes if n.get("login"))

    due_date = ""
    status = ""
    track = ""

    for fv in (node.get("fieldValues") or {}).get("nodes") or []:
        field_name = str(((fv.get("field") or {}).get("name")) or "").strip()
        kind = str(fv.get("__typename") or "")

        if kind == "ProjectV2ItemFieldDateValue" and field_name == due_field_name:
            due_date = str(fv.get("date") or "").strip()
        elif kind == "ProjectV2ItemFieldSingleSelectValue":
            if field_name == status_field_name:
                status = str(fv.get("name") or "").strip()
            elif field_name == track_field_name:
                track = str(fv.get("name") or "").strip()
        elif kind == "ProjectV2ItemFieldTextValue" and field_name == track_field_name and not track:
            track = str(fv.get("text") or "").strip()

    if not due_date:
        return None

    return ProjectItem(
        item_id=str(node.get("id") or "").strip(),
        content_type=content_type,
        title=title,
        url=url,
        due_date=due_date,
        status=status,
        track=track,
        assignees=assignees,
        state=state,
    )


def fetch_project_items(
    *,
    token: str,
    owner: str,
    number: int,
    due_field_name: str,
    status_field_name: str,
    track_field_name: str,
    sync_only_statuses: set[str],
) -> list[ProjectItem]:
    items: list[ProjectItem] = []
    cursor: str | None = None
    query = _graphql_query()

    while True:
        data = _graphql_request(
            token,
            query,
            {
                "owner": owner,
                "number": number,
                "cursor": cursor,
            },
        )
        project = _project_node(data)
        batch = (project.get("items") or {}).get("nodes") or []
        for node in batch:
            parsed = _parse_project_item(
                node,
                due_field_name=due_field_name,
                status_field_name=status_field_name,
                track_field_name=track_field_name,
            )
            if not parsed:
                continue
            if sync_only_statuses and parsed.status and parsed.status not in sync_only_statuses:
                continue
            items.append(parsed)

        page_info = (project.get("items") or {}).get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    return items


def _calendar_service(sa_json: str):
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except Exception as exc:
        raise RuntimeError(
            "google calendar dependencies are missing. install google-auth and google-api-python-client"
        ) from exc

    info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=[CALENDAR_SCOPE])
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _event_body(
    item: ProjectItem,
    *,
    event_prefix: str,
    owner: str,
    project_number: int,
) -> dict[str, Any]:
    due = date.fromisoformat(item.due_date)
    description_lines = [
        f"Project: {owner}#{project_number}",
        f"Type: {item.content_type}",
        f"Status: {item.status or '-'}",
        f"Track: {item.track or '-'}",
        f"State: {item.state or '-'}",
        f"Assignees: {item.assignees or '-'}",
        f"URL: {item.url or '-'}",
    ]
    return {
        "summary": f"{event_prefix} {item.title}".strip(),
        "description": "\n".join(description_lines),
        "start": {"date": due.isoformat()},
        "end": {"date": (due + timedelta(days=1)).isoformat()},
        "extendedProperties": {
            "private": {
                "gh_project_item_id": item.item_id,
                "gh_project_owner": owner,
                "gh_project_number": str(project_number),
            }
        },
    }


def upsert_events(
    *,
    service,
    calendar_id: str,
    items: list[ProjectItem],
    event_prefix: str,
    owner: str,
    project_number: int,
    dry_run: bool,
) -> dict[str, int]:
    created = 0
    updated = 0
    skipped = 0

    for item in items:
        body = _event_body(
            item,
            event_prefix=event_prefix,
            owner=owner,
            project_number=project_number,
        )
        if dry_run:
            skipped += 1
            continue

        found = (
            service.events()
            .list(
                calendarId=calendar_id,
                privateExtendedProperty=[f"gh_project_item_id={item.item_id}"],
                singleEvents=True,
                maxResults=1,
            )
            .execute()
        )
        existing = (found.get("items") or [])
        if existing:
            event_id = existing[0]["id"]
            service.events().update(calendarId=calendar_id, eventId=event_id, body=body).execute()
            updated += 1
        else:
            service.events().insert(calendarId=calendar_id, body=body).execute()
            created += 1

    return {
        "created": created,
        "updated": updated,
        "dry_run_skipped": skipped,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync GitHub Project to Google Calendar.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to Google Calendar.")
    args = parser.parse_args()

    gh_token = _env("GH_PROJECT_TOKEN", os.getenv("GITHUB_TOKEN"))
    owner = _env("GH_PROJECT_OWNER")
    project_number = int(_env("GH_PROJECT_NUMBER"))
    due_field_name = _env("GH_PROJECT_DUE_FIELD_NAME", "Due")
    status_field_name = _env("GH_PROJECT_STATUS_FIELD_NAME", "Status")
    track_field_name = _env("GH_PROJECT_TRACK_FIELD_NAME", "Track")
    event_prefix = _env("GCAL_EVENT_PREFIX", "[KORStockScan]")
    calendar_id = _env("GOOGLE_CALENDAR_ID")
    service_account_json = _env("GOOGLE_SERVICE_ACCOUNT_JSON")
    dry_run = args.dry_run or _env_bool("SYNC_DRY_RUN", False)

    only_status_raw = str(os.getenv("GH_SYNC_ONLY_STATUSES", "") or "").strip()
    sync_only_statuses = {x.strip() for x in only_status_raw.split(",") if x.strip()}

    items = fetch_project_items(
        token=gh_token,
        owner=owner,
        number=project_number,
        due_field_name=due_field_name,
        status_field_name=status_field_name,
        track_field_name=track_field_name,
        sync_only_statuses=sync_only_statuses,
    )

    service = _calendar_service(service_account_json)
    counts = upsert_events(
        service=service,
        calendar_id=calendar_id,
        items=items,
        event_prefix=event_prefix,
        owner=owner,
        project_number=project_number,
        dry_run=dry_run,
    )

    summary = {
        "project_owner": owner,
        "project_number": project_number,
        "items_with_due_date": len(items),
        "status_filter_applied": sorted(sync_only_statuses),
        "dry_run": dry_run,
        **counts,
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[PROJECT_CAL_SYNC_ERROR] {exc}", file=sys.stderr)
        raise
