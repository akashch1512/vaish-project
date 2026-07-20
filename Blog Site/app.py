import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "blog.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "personal-blog-dev-key"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                content TEXT NOT NULL,
                is_published INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                published_at TEXT
            )
            """
        )


def get_post(post_id):
    with get_db_connection() as connection:
        post = connection.execute(
            "SELECT * FROM posts WHERE id = ?",
            (post_id,),
        ).fetchone()
    if post is None:
        abort(404)
    return post


def validate_post_form(form):
    title = form.get("title", "").strip()
    summary = form.get("summary", "").strip()
    content = form.get("content", "").strip()
    is_published = 1 if form.get("is_published") == "on" else 0

    errors = []
    if not title:
        errors.append("Title is required.")
    if not summary:
        errors.append("Short summary is required.")
    if not content:
        errors.append("Post content is required.")

    return title, summary, content, is_published, errors


@app.before_request
def prepare_database():
    init_db()


@app.route("/")
def index():
    with get_db_connection() as connection:
        posts = connection.execute(
            """
            SELECT * FROM posts
            WHERE is_published = 1
            ORDER BY COALESCE(published_at, created_at) DESC
            """
        ).fetchall()
    return render_template("index.html", posts=posts)


@app.route("/dashboard")
def dashboard():
    with get_db_connection() as connection:
        posts = connection.execute(
            "SELECT * FROM posts ORDER BY updated_at DESC"
        ).fetchall()
    return render_template("dashboard.html", posts=posts)


@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    post = get_post(post_id)
    if not post["is_published"]:
        flash("That post is still a draft. You can edit or publish it from the dashboard.")
        return redirect(url_for("edit_post", post_id=post["id"]))
    return render_template("post_detail.html", post=post)


@app.route("/posts/new", methods=("GET", "POST"))
def create_post():
    if request.method == "POST":
        title, summary, content, is_published, errors = validate_post_form(request.form)
        if errors:
            for error in errors:
                flash(error)
            return render_template(
                "post_form.html",
                post=request.form,
                page_title="Create Post",
                button_label="Create post",
            )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        published_at = now if is_published else None
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO posts
                    (title, summary, content, is_published, created_at, updated_at, published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (title, summary, content, is_published, now, now, published_at),
            )
        flash("Post created successfully.")
        return redirect(url_for("dashboard"))

    return render_template(
        "post_form.html",
        post={},
        page_title="Create Post",
        button_label="Create post",
    )


@app.route("/posts/<int:post_id>/edit", methods=("GET", "POST"))
def edit_post(post_id):
    post = get_post(post_id)
    if request.method == "POST":
        title, summary, content, is_published, errors = validate_post_form(request.form)
        if errors:
            for error in errors:
                flash(error)
            return render_template(
                "post_form.html",
                post={**dict(post), **request.form},
                page_title="Edit Post",
                button_label="Save changes",
            )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        published_at = post["published_at"]
        if is_published and not published_at:
            published_at = now
        if not is_published:
            published_at = None

        with get_db_connection() as connection:
            connection.execute(
                """
                UPDATE posts
                SET title = ?, summary = ?, content = ?, is_published = ?,
                    updated_at = ?, published_at = ?
                WHERE id = ?
                """,
                (title, summary, content, is_published, now, published_at, post_id),
            )
        flash("Post updated successfully.")
        return redirect(url_for("dashboard"))

    return render_template(
        "post_form.html",
        post=post,
        page_title="Edit Post",
        button_label="Save changes",
    )


@app.post("/posts/<int:post_id>/publish")
def publish_post(post_id):
    post = get_post(post_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection() as connection:
        connection.execute(
            """
            UPDATE posts
            SET is_published = 1, updated_at = ?, published_at = COALESCE(published_at, ?)
            WHERE id = ?
            """,
            (now, now, post["id"]),
        )
    flash("Post published.")
    return redirect(url_for("dashboard"))


@app.post("/posts/<int:post_id>/unpublish")
def unpublish_post(post_id):
    post = get_post(post_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection() as connection:
        connection.execute(
            """
            UPDATE posts
            SET is_published = 0, updated_at = ?, published_at = NULL
            WHERE id = ?
            """,
            (now, post["id"]),
        )
    flash("Post moved to drafts.")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
