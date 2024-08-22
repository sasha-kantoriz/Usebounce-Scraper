import os
import json
from functools import wraps
from datetime import datetime as dt
from bs4 import BeautifulSoup as soup
from playwright.sync_api import Playwright, sync_playwright

from flask import Flask, request, jsonify


app = Flask(__name__)

def scraper(playwright: Playwright, email) -> None:
    try:
        browser = playwright.chromium.launch(
            headless=True,
            # proxy={"server": "ipv6-ww.lightningproxies.net:10000"}
        )
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(120000)
        page.set_default_navigation_timeout(120000)
        page.goto("https://www.usebouncer.com/free-email-checker/")
        page.wait_for_load_state("domcontentloaded")
        page.get_by_placeholder("Email*").fill(email)
        page.get_by_placeholder("Email*").press("Enter")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("p.bm__check-email")
        raw = page.content()
        html = soup(raw, "html.parser")
        e_mail = html.find("p", class_="bm__check-email").text
        desc = html.find("p", class_="bm__check-email-desc").text
        big_rows = html.find_all("div", class_="bm__check-row")
        status_reason = big_rows[0]

        status = status_reason.find("div", class_="bm__check-status").find("span").text
        reason = status_reason.find("div", class_="bm__check-reason").find("span").text

        result = {
            "email": e_mail,
            "description": desc,
            "status": status,
            "reason": reason
        }

        domain_row = big_rows[1]
        inners = domain_row.find_all("div", class_="bm__check-inner")
        for inner in inners:
            checklists = inner.find_all("ul", class_="bm__check-list")
            keys = list(checklists[0].stripped_strings)
            vals = list(checklists[1].stripped_strings)
            zipper = zip(keys, vals)
            result.update(dict(zipper))
        status = "OK"
        print(">> Success! Result:\n", result)
    except Exception as e:
        print(f">> Error. Error type: {repr(e)}.")
        now = dt.now().strftime("%Y-%m-%d, %H:%M:%S")
        result = {
            "timestamp": now,
            "email": email,
            "error type": repr(e)
        }

        status = "FAIL"
    finally:
        print(">> Finish.")
        output = (status, result)
    # ---------------------
    context.close()
    browser.close()
    return output


def authorize(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.args.get("token") != os.getenv("TOKEN"):
            return jsonify({"message": "Not Authorized"}), 401
        return f(*args, **kwargs)
    return wrapper


@app.route("/", methods=["GET"])
@authorize
def main():
    email = request.args.get("email")
    if not email:
        return jsonify({"message": "email is required"}), 400

    with sync_playwright() as playwright:
        result = scraper(playwright, email)

    return jsonify({"status": "Processed", "result": result})


if __name__ == "__main__":
    email_list = [
        "contact@affordabletreasures.com",
        "bryano@gap1.com",
        "dinavaranogallery@gmail.com",
        "info@casanovagallery.com"
    ]

    app.run(host="0.0.0.0", port=15000)
