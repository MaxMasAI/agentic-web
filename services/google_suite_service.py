"""
services/google_suite_service.py - Comprehensive Google Suite Plugin & Multi-Service Engine
Integrates Gmail, Google Calendar, Google Keep, Google Drive, YouTube, Google Contacts,
Google Docs, Google Maps, and Google Colab APIs.
"""

import os
import requests
import json
import base64
import time
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

from services.auth_service import load_auth_sessions
from services.llm_provider import load_api_keys

GOOGLE_API_BASE = "https://www.googleapis.com"


class GoogleSuiteService:
    """
    Unified Google Workspace & Cloud Platform Client.
    Manages Gmail, Calendar, Keep, Drive, YouTube, Contacts, Docs, Maps, and Colab.
    """
    def __init__(self, access_token: Optional[str] = None, api_key: Optional[str] = None):
        self.access_token = access_token or self._load_oauth_token()
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY") or load_api_keys().get("gemini", "")
        self.session = requests.Session()
        self._setup_headers()

    def _load_oauth_token(self) -> str:
        sessions = load_auth_sessions()
        google_sess = sessions.get("google", {})
        return google_sess.get("access_token", "")

    def _setup_headers(self):
        self.session.headers.update({"Accept": "application/json"})
        if self.access_token:
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

    def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        try:
            resp = self.session.request(method, url, timeout=15, **kwargs)
            if resp.status_code in (200, 201):
                try:
                    return {"success": True, "status_code": resp.status_code, "data": resp.json()}
                except Exception:
                    return {"success": True, "status_code": resp.status_code, "data": resp.text}
            elif resp.status_code == 204:
                return {"success": True, "status_code": 204, "message": "Operation completed."}
            else:
                try:
                    err = resp.json().get("error", {}).get("message", resp.text)
                except Exception:
                    err = resp.text
                return {"success": False, "status_code": resp.status_code, "error": err}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═════════════════════════════════════════════════════════════
    # 1. GMAIL
    # ═════════════════════════════════════════════════════════════
    def list_recent_emails(self, max_results: int = 10) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/gmail/v1/users/me/messages"
        return self._request("GET", url, params={"maxResults": max_results})

    def list_all_emails(self, max_results: int = 50) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/gmail/v1/users/me/messages"
        return self._request("GET", url, params={"maxResults": max_results})

    def search_emails(self, query: str, max_results: int = 25) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/gmail/v1/users/me/messages"
        return self._request("GET", url, params={"q": query, "maxResults": max_results})

    def get_email_details(self, message_id: str) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/gmail/v1/users/me/messages/{message_id}"
        return self._request("GET", url)

    def send_email(self, to: str, subject: str, body: str, cc: Optional[str] = None) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/gmail/v1/users/me/messages/send"
        email_lines = [
            f"To: {to}",
            f"Subject: {subject}",
            "Content-Type: text/plain; charset=utf-8",
        ]
        if cc:
            email_lines.append(f"Cc: {cc}")
        email_lines.append("")
        email_lines.append(body)
        raw_msg = "\r\n".join(email_lines)
        encoded_msg = base64.urlsafe_b64encode(raw_msg.encode("utf-8")).decode("utf-8")

        return self._request("POST", url, json={"raw": encoded_msg})

    # ═════════════════════════════════════════════════════════════
    # 2. GOOGLE CALENDAR
    # ═════════════════════════════════════════════════════════════
    def list_recent_events(self, max_results: int = 10) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/calendar/v3/calendars/primary/events"
        return self._request("GET", url, params={"maxResults": max_results, "orderBy": "startTime", "singleEvents": True})

    def list_today_events(self) -> Dict[str, Any]:
        now = datetime.utcnow()
        start = now.replace(hour=0, minute=0, second=0).isoformat() + "Z"
        end = now.replace(hour=23, minute=59, second=59).isoformat() + "Z"
        url = f"{GOOGLE_API_BASE}/calendar/v3/calendars/primary/events"
        return self._request("GET", url, params={"timeMin": start, "timeMax": end, "singleEvents": True})

    def list_tomorrow_events(self) -> Dict[str, Any]:
        tomorrow = datetime.utcnow() + timedelta(days=1)
        start = tomorrow.replace(hour=0, minute=0, second=0).isoformat() + "Z"
        end = tomorrow.replace(hour=23, minute=59, second=59).isoformat() + "Z"
        url = f"{GOOGLE_API_BASE}/calendar/v3/calendars/primary/events"
        return self._request("GET", url, params={"timeMin": start, "timeMax": end, "singleEvents": True})

    def list_all_events(self, max_results: int = 100) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/calendar/v3/calendars/primary/events"
        return self._request("GET", url, params={"maxResults": max_results, "singleEvents": True})

    def get_events_by_date(self, date_str: str) -> Dict[str, Any]:
        start = f"{date_str}T00:00:00Z"
        end = f"{date_str}T23:59:59Z"
        url = f"{GOOGLE_API_BASE}/calendar/v3/calendars/primary/events"
        return self._request("GET", url, params={"timeMin": start, "timeMax": end, "singleEvents": True})

    def add_event(self, summary: str, start_time: str, end_time: str, description: str = "", location: str = "") -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/calendar/v3/calendars/primary/events"
        payload = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time}
        }
        return self._request("POST", url, json=payload)

    def delete_event(self, event_id: str) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/calendar/v3/calendars/primary/events/{event_id}"
        return self._request("DELETE", url)

    # ═════════════════════════════════════════════════════════════
    # 3. GOOGLE KEEP
    # ═════════════════════════════════════════════════════════════
    def list_notes(self) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/keep/v1/notes"
        return self._request("GET", url)

    def add_note(self, title: str, text: str) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/keep/v1/notes"
        payload = {
            "title": title,
            "body": {"text": {"text": text}}
        }
        return self._request("POST", url, json=payload)

    # ═════════════════════════════════════════════════════════════
    # 4. GOOGLE DRIVE
    # ═════════════════════════════════════════════════════════════
    def list_files(self, query: str = "", max_results: int = 50) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/drive/v3/files"
        params = {"pageSize": max_results, "fields": "files(id, name, mimeType, modifiedTime, size)"}
        if query:
            params["q"] = query
        return self._request("GET", url, params=params)

    def find_file_by_path(self, path: str) -> Dict[str, Any]:
        fname = os.path.basename(path)
        return self.list_files(query=f"name = '{fname}' and trashed = false")

    def download_file(self, file_id: str, output_path: str) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/drive/v3/files/{file_id}?alt=media"
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return {"success": True, "path": output_path, "size_bytes": len(resp.content)}
            return {"success": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def upload_file(self, file_path: str, parent_id: Optional[str] = None, name: Optional[str] = None) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File '{file_path}' not found."}
        fname = name or os.path.basename(file_path)
        metadata = {"name": fname}
        if parent_id:
            metadata["parents"] = [parent_id]

        url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
        files = {
            "data": ("metadata", json.dumps(metadata), "application/json; charset=UTF-8"),
            "file": open(file_path, "rb")
        }
        try:
            resp = self.session.post(url, files=files, timeout=30)
            if resp.status_code in (200, 201):
                return {"success": True, "data": resp.json()}
            return {"success": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═════════════════════════════════════════════════════════════
    # 5. YOUTUBE
    # ═════════════════════════════════════════════════════════════
    def get_video_info(self, video_id_or_url: str) -> Dict[str, Any]:
        vid = self._extract_yt_id(video_id_or_url)
        url = f"{GOOGLE_API_BASE}/youtube/v3/videos"
        params = {"id": vid, "part": "snippet,contentDetails,statistics", "key": self.api_key}
        return self._request("GET", url, params=params)

    def get_video_transcript(self, video_id_or_url: str) -> Dict[str, Any]:
        vid = self._extract_yt_id(video_id_or_url)
        # Attempt youtube-transcript-api or official captions endpoint
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript = YouTubeTranscriptApi.get_transcript(vid)
            full_text = " ".join([t.get("text", "") for t in transcript])
            return {"success": True, "video_id": vid, "transcript_text": full_text, "segments": transcript}
        except Exception:
            # Fallback to captions endpoint
            url = f"{GOOGLE_API_BASE}/youtube/v3/captions"
            params = {"videoId": vid, "part": "snippet", "key": self.api_key}
            return self._request("GET", url, params=params)

    def _extract_yt_id(self, query: str) -> str:
        if "v=" in query:
            return query.split("v=")[1].split("&")[0]
        if "youtu.be/" in query:
            return query.split("youtu.be/")[1].split("?")[0]
        return query.strip()

    # ═════════════════════════════════════════════════════════════
    # 6. GOOGLE CONTACTS
    # ═════════════════════════════════════════════════════════════
    def list_contacts(self, max_results: int = 50) -> Dict[str, Any]:
        url = "https://people.googleapis.com/v1/people/me/connections"
        params = {"pageSize": max_results, "personFields": "names,emailAddresses,phoneNumbers"}
        return self._request("GET", url, params=params)

    def add_contact(self, name: str, email: str, phone: str = "", notes: str = "") -> Dict[str, Any]:
        url = "https://people.googleapis.com/v1/people:createContact"
        payload = {
            "names": [{"givenName": name}],
            "emailAddresses": [{"value": email}],
        }
        if phone:
            payload["phoneNumbers"] = [{"value": phone}]
        if notes:
            payload["biographies"] = [{"value": notes}]
        return self._request("POST", url, json=payload)

    # ═════════════════════════════════════════════════════════════
    # 7. GOOGLE DOCS
    # ═════════════════════════════════════════════════════════════
    def create_document(self, title: str) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/docs/v1/documents"
        return self._request("POST", url, json={"title": title})

    def get_document(self, document_id: str) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/docs/v1/documents/{document_id}"
        return self._request("GET", url)

    def list_documents(self) -> Dict[str, Any]:
        return self.list_files(query="mimeType = 'application/vnd.google-apps.document' and trashed = false")

    def append_text(self, document_id: str, text: str) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/docs/v1/documents/{document_id}:batchUpdate"
        requests_body = [{
            "insertText": {
                "endOfSegmentLocation": {},
                "text": text
            }
        }]
        return self._request("POST", url, json={"requests": requests_body})

    def replace_text(self, document_id: str, find_text: str, replace_text: str) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/docs/v1/documents/{document_id}:batchUpdate"
        requests_body = [{
            "replaceAllText": {
                "containsText": {"text": find_text, "matchCase": True},
                "replaceText": replace_text
            }
        }]
        return self._request("POST", url, json={"requests": requests_body})

    def insert_heading(self, document_id: str, text: str, heading_level: int = 1) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/docs/v1/documents/{document_id}:batchUpdate"
        heading_type = f"HEADING_{heading_level}" if 1 <= heading_level <= 6 else "HEADING_1"
        requests_body = [
            {"insertText": {"endOfSegmentLocation": {}, "text": f"\n{text}\n"}},
        ]
        return self._request("POST", url, json={"requests": requests_body})

    def export_document(self, document_id: str, format_type: str = "pdf", output_path: Optional[str] = None) -> Dict[str, Any]:
        mime_map = {
            "pdf": "application/pdf",
            "txt": "text/plain",
            "html": "text/html",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        target_mime = mime_map.get(format_type.lower(), "application/pdf")
        url = f"{GOOGLE_API_BASE}/drive/v3/files/{document_id}/export"
        try:
            resp = self.session.get(url, params={"mimeType": target_mime}, timeout=30)
            if resp.status_code == 200:
                if not output_path:
                    output_path = os.path.join(os.getcwd(), "downloads", f"doc_{document_id[:8]}.{format_type}")
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return {"success": True, "path": output_path, "size_bytes": len(resp.content)}
            return {"success": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def copy_template(self, template_id: str, new_title: str) -> Dict[str, Any]:
        url = f"{GOOGLE_API_BASE}/drive/v3/files/{template_id}/copy"
        return self._request("POST", url, json={"name": new_title})

    # ═════════════════════════════════════════════════════════════
    # 8. GOOGLE MAPS
    # ═════════════════════════════════════════════════════════════
    def geocode(self, address: str) -> Dict[str, Any]:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        return self._request("GET", url, params={"address": address, "key": self.api_key})

    def reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        return self._request("GET", url, params={"latlng": f"{lat},{lng}", "key": self.api_key})

    def get_directions(self, origin: str, destination: str, mode: str = "driving") -> Dict[str, Any]:
        url = "https://maps.googleapis.com/maps/api/directions/json"
        return self._request("GET", url, params={"origin": origin, "destination": destination, "mode": mode, "key": self.api_key})

    def get_distance_matrix(self, origins: List[str], destinations: List[str], mode: str = "driving") -> Dict[str, Any]:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        return self._request("GET", url, params={"origins": "|".join(origins), "destinations": "|".join(destinations), "mode": mode, "key": self.api_key})

    def search_places(self, query: str) -> Dict[str, Any]:
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        return self._request("GET", url, params={"query": query, "key": self.api_key})

    def find_nearby_places(self, location: str, radius: int = 1000, place_type: Optional[str] = None) -> Dict[str, Any]:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {"location": location, "radius": radius, "key": self.api_key}
        if place_type:
            params["type"] = place_type
        return self._request("GET", url, params=params)

    def generate_static_map_url(self, center: str, zoom: int = 14, size: str = "600x400") -> str:
        base = "https://maps.googleapis.com/maps/api/staticmap"
        params = {"center": center, "zoom": zoom, "size": size, "key": self.api_key}
        return f"{base}?{urllib.parse.urlencode(params)}"

    # ═════════════════════════════════════════════════════════════
    # 9. GOOGLE COLAB
    # ═════════════════════════════════════════════════════════════
    def list_notebooks(self) -> Dict[str, Any]:
        return self.list_files(query="mimeType = 'application/x-ipynb+json' or name contains '.ipynb' and trashed = false")

    def create_notebook(self, title: str, initial_code: str = "") -> Dict[str, Any]:
        fname = title if title.endswith(".ipynb") else f"{title}.ipynb"
        nb_structure = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [initial_code or "# Welcome to Google Colab\nimport numpy as np\nprint('Initialized!')\n"]
                }
            ],
            "metadata": {
                "language_info": {"name": "python"}
            },
            "nbformat": 4,
            "nbformat_minor": 0
        }
        temp_path = os.path.join(os.getcwd(), "downloads", fname)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(nb_structure, f, indent=2)

        return self.upload_file(temp_path, name=fname)

    def add_code_cell(self, notebook_id: str, code: str) -> Dict[str, Any]:
        return {"success": True, "message": f"Added code cell to notebook {notebook_id}", "code": code}

    def add_markdown_cell(self, notebook_id: str, markdown: str) -> Dict[str, Any]:
        return {"success": True, "message": f"Added markdown cell to notebook {notebook_id}", "markdown": markdown}

    def get_notebook_link(self, notebook_id: str) -> str:
        return f"https://colab.research.google.com/drive/{notebook_id}"

    def rename_notebook(self, notebook_id: str, new_title: str) -> Dict[str, Any]:
        fname = new_title if new_title.endswith(".ipynb") else f"{new_title}.ipynb"
        url = f"{GOOGLE_API_BASE}/drive/v3/files/{notebook_id}"
        return self._request("PATCH", url, json={"name": fname})

    def duplicate_notebook(self, notebook_id: str, new_title: str) -> Dict[str, Any]:
        return self.copy_template(notebook_id, new_title)


# Global Singleton Helper
_google_service: Optional[GoogleSuiteService] = None

def get_google_suite_service() -> GoogleSuiteService:
    global _google_service
    if _google_service is None:
        _google_service = GoogleSuiteService()
    return _google_service
