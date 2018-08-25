#!/usr/bin/env python3

"""
Integrate with Wunderlist's API to postpone due dates.

Find any tasks in the specified list that count as overdue, and nudge their
due date up to today. This has two benefits:

  - Tasks that would otherwise be overdue will now recur from their completion
    date, which Wunderlist doesn't natively support.
  - There isn't a big list of overdue tasks, and any guilt that goes along
    with that.
"""

from datetime import date, datetime
import logging
from os import environ
import sys
import urllib

import requests

API_ROOT = environ.get("API_ROOT", "https://a.wunderlist.com/api/v1/")
CLIENT_ID = environ.get("CLIENT_ID")
ACCESS_TOKEN = environ.get("ACCESS_TOKEN")
DEBUG = environ.get("DEBUG")
DRY_RUN = environ.get("DRY_RUN")

LIST_TITLE = environ.get("LIST_TITLE")

AUTH_HEADERS = {"X-Client-ID": CLIENT_ID,
                "X-Access-Token": ACCESS_TOKEN}

logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger()


def get_list_id(list_title):
    lists_url = urllib.parse.urljoin(API_ROOT, "lists")
    lists_response = requests.get(lists_url, headers=AUTH_HEADERS)

    lists_by_title = {str(l["title"]): l for l in lists_response.json()}

    logger.debug(lists_by_title)

    try:
        list_info = lists_by_title[LIST_TITLE]
    except KeyError as e:
        raise KeyError("Couldn't find list with title %s" % LIST_TITLE) from e

    logger.debug(list_info)

    return list_info["id"]


def tasks_for_list(list_id):
    tasks_url = urllib.parse.urljoin(API_ROOT, "tasks")

    tasks_response = requests.get(tasks_url,
                                  params={"list_id": list_id},
                                  headers=AUTH_HEADERS)
    return [{"id": t["id"],
             "title": t["title"],
             "revision": t["revision"],
             "due_date": t.get("due_date")}
            for t in tasks_response.json()]


def notes_for_list(list_id):
    notes_url = urllib.parse.urljoin(API_ROOT, "notes")

    notes_response = requests.get(notes_url,
                                  params={"list_id": list_id},
                                  headers=AUTH_HEADERS)
    return {n['task_id']: n['content'] for n in notes_response.json()}


def overdue(task):
    due_date_str = task.get("due_date")
    if not due_date_str:
        return False
    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    return due_date < date.today()


def excluded(task):
    note_text = task.get("note") or ""
    return "#noforgiveness" in note_text


def task_url(task_id):
    return urllib.parse.urljoin(API_ROOT, "tasks/" + str(task_id))


if __name__ == "__main__":

    list_id = get_list_id(LIST_TITLE)
    tasks = tasks_for_list(list_id)

    notes = notes_for_list(list_id)

    for task in tasks:
        task["note"] = notes.get(task["id"])

    for task in tasks:
        logger.debug(task)

    excluded_tasks = [t for t in tasks if excluded(t)]
    tasks_to_update = [t for t in tasks if overdue(t) and not excluded(t)]

    logger.info(
            "Found {} tasks; {} excluded; {} to update".format(
                len(tasks),
                len(excluded_tasks),
                len(tasks_to_update)))

    new_due_date_str = date.today().isoformat()

    for t in tasks_to_update:
        url = task_url(t["id"])

        if DRY_RUN:
            logger.info("Would have updated due date for {} to {}".format(t["title"], new_due_date_str))
            continue

        patch_resp = requests.patch(url,
                                    headers=AUTH_HEADERS,
                                    json={"due_date": new_due_date_str,
                                          "revision": t["revision"]})
        if patch_resp.ok:
            logger.info("Updated due date for {} to {}".format(t["title"], new_due_date_str))
        else:
            logger.error("Failed to update {}: error {}".format(t["title"], patch_resp.status_code))

        logger.debug("Response status {}; content {}".format(
            patch_resp.status_code, patch_resp.content))

    # Flush and close all handlers, just to make sure the logs show up
    logging.shutdown()
