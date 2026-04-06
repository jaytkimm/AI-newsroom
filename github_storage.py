import os
import json
import streamlit as st
from github import Github, GithubException

def get_github_token():
    if "GITHUB_TOKEN" in st.secrets:
        return st.secrets["GITHUB_TOKEN"]
    return os.environ.get("GITHUB_TOKEN", "")

def get_repo():
    token = get_github_token()
    if not token:
        raise ValueError("GitHub Token not found in secrets.")
    g = Github(token)
    
    repo_name = st.secrets.get("GITHUB_REPO", os.environ.get("GITHUB_REPO", ""))
    if not repo_name:
        raise ValueError("GITHUB_REPO not found in secrets.")
    return g.get_repo(repo_name)

def get_feeds():
    """Retrieve feeds.json from GitHub"""
    try:
        repo = get_repo()
        file_content = repo.get_contents("feeds.json")
        return json.loads(file_content.decoded_content.decode("utf-8"))
    except GithubException as e:
        if getattr(e, 'status', None) == 404:
            return []
        st.error(f"GitHub API Error: {getattr(e, 'status', 'Unknown')} - {getattr(e, 'data', {}).get('message', str(e))}")
        return []
    except Exception as e:
        st.error(f"Error loading feeds: {str(e)}")
        return []

def save_feeds(feeds_list):
    """Save feeds.json to GitHub"""
    repo = get_repo()
    content = json.dumps(feeds_list, indent=2, ensure_ascii=False)
    try:
        file = repo.get_contents("feeds.json")
        repo.update_file("feeds.json", "Update feeds list via Dashboard", content, file.sha)
    except GithubException as e:
        if e.status == 404:
            repo.create_file("feeds.json", "Create feeds list via Dashboard", content)
        else:
            raise e

def get_daily_reports():
    """Retrieve daily_reports.json from GitHub"""
    try:
        repo = get_repo()
        file_content = repo.get_contents("daily_reports.json")
        return json.loads(file_content.decoded_content.decode("utf-8"))
    except GithubException as e:
        if getattr(e, 'status', None) == 404:
            return {}
        st.error(f"GitHub API Error: {getattr(e, 'status', 'Unknown')} - {getattr(e, 'data', {}).get('message', str(e))}")
        return {}
    except Exception as e:
        st.error(f"Error loading daily reports: {str(e)}")
        return {}

def save_daily_report(date_str, markdown_content):
    """Save a daily report to daily_reports.json in GitHub"""
    reports = get_daily_reports()
    reports[date_str] = markdown_content
    
    repo = get_repo()
    content = json.dumps(reports, indent=2, ensure_ascii=False)
    try:
        file = repo.get_contents("daily_reports.json")
        repo.update_file("daily_reports.json", f"Add/Update report for {date_str} via Dashboard", content, file.sha)
    except GithubException as e:
        if e.status == 404:
            repo.create_file("daily_reports.json", f"Create daily_reports.json for {date_str} via Dashboard", content)
        else:
            raise e
