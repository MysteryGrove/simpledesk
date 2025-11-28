"""Documentation routes and views."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from app.db import get_session
from app.models import (
    DocumentationPage,
    DocumentationSection,
    DocumentationSubsection,
)


documentation_bp = Blueprint("documentation", __name__, url_prefix="/documentation")


@documentation_bp.before_request
def require_authentication():
    """Ensure documentation pages are available only to authenticated users."""
    if not session.get("user_authenticated"):
        return redirect(url_for("auth.login"))
    return None


@documentation_bp.route("/", methods=["GET"])
def view_documentation() -> str:
    """Render the documentation workspace."""
    return render_template("documentation.html")


def _serialize_page(page: DocumentationPage) -> dict[str, object]:
    return {
        "id": page.id,
        "title": page.title,
        "content": page.content,
        "author": page.author,
        "lastUpdated": page.updated_at.isoformat(),
    }


def _serialize_subsection(subsection: DocumentationSubsection) -> dict[str, object]:
    return {
        "id": subsection.id,
        "title": subsection.title,
        "pages": [_serialize_page(page) for page in subsection.pages],
    }


def _serialize_section(section: DocumentationSection) -> dict[str, object]:
    return {
        "id": section.id,
        "title": section.title,
        "subsections": [_serialize_subsection(subsection) for subsection in section.subsections],
    }


@documentation_bp.route("/api/tree", methods=["GET"])
def documentation_tree() -> tuple[object, int]:
    """Return the full documentation tree for the authenticated user."""

    db_session = get_session()
    try:
        sections = (
            db_session.query(DocumentationSection)
            .order_by(DocumentationSection.id)
            .all()
        )
        return jsonify({"sections": [_serialize_section(section) for section in sections]}), 200
    finally:
        db_session.close()


@documentation_bp.route("/api/sections", methods=["POST"])
def create_section() -> tuple[object, int]:
    """Create a new top-level section."""

    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return jsonify({"error": "Section title is required."}), 400

    db_session = get_session()
    try:
        section = DocumentationSection(title=title)
        db_session.add(section)
        db_session.commit()
        db_session.refresh(section)
        return jsonify({"section": _serialize_section(section)}), 201
    finally:
        db_session.close()


@documentation_bp.route("/api/sections/<int:section_id>", methods=["PUT"])
def rename_section(section_id: int) -> tuple[object, int]:
    """Rename an existing section."""

    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return jsonify({"error": "Section title is required."}), 400

    db_session = get_session()
    try:
        section = db_session.get(DocumentationSection, section_id)
        if not section:
            return jsonify({"error": "Section not found."}), 404
        section.title = title
        section.updated_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(section)
        return jsonify({"section": _serialize_section(section)}), 200
    finally:
        db_session.close()


@documentation_bp.route("/api/sections/<int:section_id>", methods=["DELETE"])
def delete_section(section_id: int) -> tuple[object, int]:
    """Delete a section and its nested subsections and pages."""

    db_session = get_session()
    try:
        section = db_session.get(DocumentationSection, section_id)
        if not section:
            return jsonify({"error": "Section not found."}), 404
        db_session.delete(section)
        db_session.commit()
        return jsonify({"status": "deleted"}), 200
    finally:
        db_session.close()


@documentation_bp.route("/api/sections/<int:section_id>/subsections", methods=["POST"])
def create_subsection(section_id: int) -> tuple[object, int]:
    """Create a subsection within a section."""

    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return jsonify({"error": "Subsection title is required."}), 400

    db_session = get_session()
    try:
        section = db_session.get(DocumentationSection, section_id)
        if not section:
            return jsonify({"error": "Section not found."}), 404
        subsection = DocumentationSubsection(section_id=section_id, title=title)
        db_session.add(subsection)
        db_session.commit()
        db_session.refresh(subsection)
        return jsonify({"subsection": _serialize_subsection(subsection)}), 201
    finally:
        db_session.close()


@documentation_bp.route("/api/subsections/<int:subsection_id>", methods=["PUT"])
def rename_subsection(subsection_id: int) -> tuple[object, int]:
    """Rename a subsection."""

    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return jsonify({"error": "Subsection title is required."}), 400

    db_session = get_session()
    try:
        subsection = db_session.get(DocumentationSubsection, subsection_id)
        if not subsection:
            return jsonify({"error": "Subsection not found."}), 404
        subsection.title = title
        subsection.updated_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(subsection)
        return jsonify({"subsection": _serialize_subsection(subsection)}), 200
    finally:
        db_session.close()


@documentation_bp.route("/api/subsections/<int:subsection_id>", methods=["DELETE"])
def delete_subsection(subsection_id: int) -> tuple[object, int]:
    """Delete a subsection and its pages."""

    db_session = get_session()
    try:
        subsection = db_session.get(DocumentationSubsection, subsection_id)
        if not subsection:
            return jsonify({"error": "Subsection not found."}), 404
        db_session.delete(subsection)
        db_session.commit()
        return jsonify({"status": "deleted"}), 200
    finally:
        db_session.close()


@documentation_bp.route("/api/subsections/<int:subsection_id>/pages", methods=["POST"])
def create_page(subsection_id: int) -> tuple[object, int]:
    """Create a new page within a subsection."""

    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip() or "Untitled page"

    db_session = get_session()
    try:
        subsection = db_session.get(DocumentationSubsection, subsection_id)
        if not subsection:
            return jsonify({"error": "Subsection not found."}), 404
        page = DocumentationPage(subsection_id=subsection_id, title=title, content="")
        db_session.add(page)
        db_session.commit()
        db_session.refresh(page)
        return jsonify({"page": _serialize_page(page)}), 201
    finally:
        db_session.close()


@documentation_bp.route("/api/pages/<int:page_id>", methods=["PUT"])
def save_page(page_id: int) -> tuple[object, int]:
    """Update page title and content."""

    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip() or "Untitled page"
    content = str(payload.get("content", ""))

    db_session = get_session()
    try:
        page = db_session.get(DocumentationPage, page_id)
        if not page:
            return jsonify({"error": "Page not found."}), 404
        page.title = title
        page.content = content
        page.updated_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(page)
        return jsonify({"page": _serialize_page(page)}), 200
    finally:
        db_session.close()


@documentation_bp.route("/api/pages/<int:page_id>", methods=["DELETE"])
def delete_page(page_id: int) -> tuple[object, int]:
    """Delete a page."""

    db_session = get_session()
    try:
        page = db_session.get(DocumentationPage, page_id)
        if not page:
            return jsonify({"error": "Page not found."}), 404
        db_session.delete(page)
        db_session.commit()
        return jsonify({"status": "deleted"}), 200
    finally:
        db_session.close()
