from flask import (
    Flask,
    request,
    redirect,
    send_from_directory
)

from urllib.parse import urlencode

from pathlib import Path

import json

from main import get_plan


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

FRONTEND_DIR = (
    PROJECT_ROOT
    / "frontend"
)


# ============================================================
# FRONTEND
# ============================================================

@app.route("/")
def home():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


@app.route("/<path:filename>")
def frontend_files(filename):

    return send_from_directory(
        FRONTEND_DIR,
        filename
    )


# ============================================================
# PLAN
# ============================================================

@app.route(
    "/plan",
    methods=["GET"]
)
def plan():

    # --------------------------------------------------------
    # Starting location
    # --------------------------------------------------------

    starting_hub = request.args.get(
        "starting-position"
    )


    if not starting_hub:

        return (
            "Please select a starting position.",
            400
        )


    # --------------------------------------------------------
    # Budget
    # --------------------------------------------------------

    unlimited_budget = (
        request.args.get(
            "unlimited-budget"
        )
        == "true"
    )


    if unlimited_budget:

        budget = float("inf")

    else:

        budget_string = (
            request.args.get(
                "budget"
            )
        )


        if not budget_string:

            return (
                "Please enter a budget "
                "or select unlimited budget.",
                400
            )


        try:

            budget = float(
                budget_string
            )

        except ValueError:

            return (
                "Invalid budget.",
                400
            )


        if budget < 0:

            return (
                "Budget cannot be negative.",
                400
            )


    # --------------------------------------------------------
    # Maximum time
    # --------------------------------------------------------

    max_time_string = (
        request.args.get(
            "max-time"
        )
    )


    if not max_time_string:

        return (
            "Please enter a maximum trip time.",
            400
        )


    try:

        max_time_hours = float(
            max_time_string
        )

    except ValueError:

        return (
            "Invalid maximum trip time.",
            400
        )


    if max_time_hours <= 0:

        return (
            "Maximum trip time must be "
            "greater than zero.",
            400
        )


    max_time_minutes = (
        max_time_hours * 60
    )


    # --------------------------------------------------------
    # Interests
    # --------------------------------------------------------

    interests = request.args.getlist(
        "interests"
    )


    if not interests:

        return (
            "Please select at least one interest.",
            400
        )


    # --------------------------------------------------------
    # Debug
    # --------------------------------------------------------

    print()
    print(
        "========================================"
    )
    print(
        "FORM DATA"
    )
    print(
        "========================================"
    )

    print(
        "Starting hub:",
        starting_hub
    )


    if unlimited_budget:

        print(
            "Budget: Unlimited"
        )

    else:

        print(
            "Budget: £",
            budget
        )


    print(
        "Maximum time:",
        max_time_minutes,
        "minutes"
    )

    print(
        "Interests:",
        interests
    )

    print(
        "========================================"
    )
    print()


    # --------------------------------------------------------
    # Generate plan
    # --------------------------------------------------------

    result = get_plan(
        starting_hub=
            starting_hub,

        budget=
            budget,

        interests=
            interests,

        max_time_minutes=
            max_time_minutes
    )


    if "error" in result:

        return (
            result["error"],
            400
        )


    # --------------------------------------------------------
    # Prepare result page
    # --------------------------------------------------------

    route = result.get(
        "route",
        []
    )

    trips = result.get(
        "trips",
        []
    )


    params = {

        "route":
            json.dumps(route),

        "trips":
            json.dumps(trips),

        "budget":
            "Unlimited"
            if unlimited_budget
            else budget,

        "max_time":
            max_time_minutes,

        "interests":
            json.dumps(interests)
    }


    result_url = (
        "/result.html?"
        + urlencode(params)
    )


    return redirect(
        result_url
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )