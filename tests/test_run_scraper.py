"""run-scraper.sh: daily summary email after a successful scrape."""
import os
import stat
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUN_SCRAPER = REPO / "scripts" / "run-scraper.sh"


def _exe(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/bash\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def _run(tmp_path: Path, scrape_exit: int, summary_email: str) -> subprocess.CompletedProcess:
    """Fake project python: `scraper.py run` exits scrape_exit, `daily_email.py` prints a body."""
    project = tmp_path / "project"
    _exe(project / ".venv" / "bin" / "python", f"""
case "$1" in
  *scraper.py) echo scraped; exit {scrape_exit} ;;
  *daily_email.py) echo "format: loseit-daily/1"; echo "args: $*" ;;
esac
""")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "run-scraper.sh").write_text(RUN_SCRAPER.read_text())
    _exe(bin_dir / "send-alert.sh", 'echo "send-alert $*" >> "$CALLS"; cat >> "$CALLS"\n')
    env = {
        **os.environ,
        "HOME": str(tmp_path / "home"),
        "LOSEIT_PROJECT": str(project),
        "LOSEIT_ALERT_EMAIL": "",
        "LOSEIT_DAILY_SUMMARY_EMAIL": summary_email,
        "CALLS": str(tmp_path / "calls"),
    }
    return subprocess.run(
        ["bash", str(bin_dir / "run-scraper.sh")], text=True, capture_output=True, env=env, check=False
    )


def test_success_sends_daily_summary(tmp_path):
    result = _run(tmp_path, 0, "bot@example.com")
    assert result.returncode == 0, result.stderr
    calls = (tmp_path / "calls").read_text()
    assert "send-alert --to bot@example.com LoseIt daily " in calls
    assert "format: loseit-daily/1" in calls
    assert "--date " in calls


def test_no_summary_without_config(tmp_path):
    result = _run(tmp_path, 0, "")
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "calls").exists()


def test_failed_scrape_sends_no_summary(tmp_path):
    result = _run(tmp_path, 1, "bot@example.com")
    assert result.returncode == 1
    assert not (tmp_path / "calls").exists()
