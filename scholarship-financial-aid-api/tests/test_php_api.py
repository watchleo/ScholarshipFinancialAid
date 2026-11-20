"""Run the two HTTP servers together when the PHP CLI is available."""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("php"), "PHP CLI required for the two-server test")
class PhpApiTest(unittest.TestCase):
    def start_server(self, command, env):
        # Pick a loopback port so the test can run alongside the classroom demo.
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]

        process = subprocess.Popen(
            [argument.replace("{port}", str(port)) for argument in command],
            env=env, cwd=PROJECT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        self.addCleanup(process.stderr.close)
        self.addCleanup(process.wait, timeout=5)
        self.addCleanup(process.terminate)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if process.poll() is not None:
                self.fail(process.stderr.read().decode(errors="replace"))
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    return f"http://127.0.0.1:{port}"
            except OSError:
                time.sleep(0.05)
        self.fail(f"Server startup timed out on port {port}")

    def test_php_submission_and_status_report_use_fastapi_records(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        key = "classroom-test-key"
        env = {**os.environ, "SCHOLARSHIP_API_KEY": key}
        fastapi_url = self.start_server([
            sys.executable, "-c",
            "import sys, uvicorn; from api import create_app; "
            "uvicorn.run(create_app(db_path=sys.argv[1]), port=int(sys.argv[2]))",
            str(Path(directory.name) / "classroom.db"), "{port}",
        ], env)
        php_url = self.start_server(
            ["php", "-S", "127.0.0.1:{port}", "php-api/index.php"],
            {**env, "FASTAPI_BASE_URL": fastapi_url},
        )
        with httpx.Client(trust_env=False) as client:
            denied = client.get(f"{php_url}/api/applications")
            self.assertEqual(denied.status_code, 401)
            client.headers["X-API-Key"] = key
            created = client.post(f"{php_url}/api/applications", json={
                "Student_ID": "S004", "Scholarship_ID": "SCH02", "Aid_ID": "FA02",
                "Term_ID": "T03", "Evaluator_ID": "E01",
            })
            self.assertEqual(created.status_code, 201, created.text)
            application_id = created.json()["data"]["Application_ID"]
            fetched = client.get(f"{fastapi_url}/api/applications/{application_id}")
            self.assertEqual(fetched.status_code, 200)
            self.assertEqual(fetched.json()["data"]["Status"], "Pending")
            report = client.get(f"{php_url}/api/application-status-counts")
            self.assertEqual(report.status_code, 200)
            self.assertEqual(report.json()["by_status"]["Pending"], 2)
            self.assertEqual(report.json()["total"], 7)
