#!/usr/bin/env python3

from datetime import date, datetime
import logging
from os import environ
import sys
import urllib

import requests

API_ROOT = environ.get("API_ROOT")
CLIENT_ID = environ.get("CLIENT_ID")
ACCESS_TOKEN = environ.get("ACCESS_TOKEN")
DEBUG = environ.get("DEBUG")

LIST_TITLE = environ.get("LIST_TITLE")

AUTH_HEADERS = {"X-Client-ID": CLIENT_ID,
                "X-Access-Token": ACCESS_TOKEN}

logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger()

if __name__ == "__main__":
    lists_url = urllib.parse.urljoin(API_ROOT, "lists")
    lists_response = requests.get(lists_url, headers=AUTH_HEADERS)

    lists_by_title = {str(l["title"]): l for l in lists_response.json()}

    logger.debug(lists_by_title)

    try:
        list_info = lists_by_title[LIST_TITLE]
    except KeyError:
        logger.error("Couldn't find list with title %s" % LIST_TITLE)
        sys.exit(1)

    logger.debug(list_info)

    list_id = list_info["id"]

    tasks_url = urllib.parse.urljoin(API_ROOT, "tasks")

    tasks_response = requests.get(tasks_url,
                                  params={"list_id": list_id},
                                  headers=AUTH_HEADERS)

    def overdue(task):
        due_date_str = task.get("due_date")
        if not due_date_str:
            return False
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        return due_date < date.today()

    tasks = [{"id": t["id"],
              "title": t["title"],
              "revision": t["revision"],
              "due_date": t.get("due_date")}
             for t in tasks_response.json()]

    overdue_tasks = [t for t in tasks if overdue(t)]

    for task in tasks:
        logger.debug(task)

    logger.info("Found {} tasks; {} overdue".format(len(tasks), len(overdue_tasks)))

    def task_url(task_id):
        return urllib.parse.urljoin(API_ROOT, "tasks/" + str(task_id))

    new_due_date_str = date.today().isoformat()

    for t in overdue_tasks:
        url = task_url(t["id"])
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
