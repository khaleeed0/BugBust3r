"""
Security tools wrapper using Docker
"""
import json
import logging
import docker
from typing import Dict, List, Optional
from app.docker.client import docker_client

logger = logging.getLogger(__name__)


class SecurityTool:
    """Base class for security tools"""
    
    def __init__(self, image: str, tool_name: str):
        self.image = image
        self.tool_name = tool_name
    
    def run(self, target: str, **kwargs) -> Dict:
        """Run the tool and return results"""
        raise NotImplementedError


class Sublist3rTool(SecurityTool):
    """Sublist3r - Subdomain enumeration"""
    
    def __init__(self):
        super().__init__("security-tools:sublist3r", "sublist3r")
    
    def run(self, target: str, **kwargs) -> Dict:
        """Run Sublist3r on target domain"""
        command = f"python3 /app/sublist3r/sublist3r.py -d {target} -o /output/subdomains.txt"
        
        try:
            stdout, stderr, exit_code = docker_client.run_container(
                image=self.image,
                command=command,
                volumes={},
                remove=True
            )
            
            # Parse subdomains from output
            subdomains = []
            if stdout:
                subdomains = [line.strip() for line in stdout.split('\n') if line.strip() and '.' in line]
            
            return {
                "tool": self.tool_name,
                "target": target,
                "status": "success" if exit_code == 0 else "failed",
                "exit_code": exit_code,
                "subdomains": subdomains,
                "count": len(subdomains),
                "raw_output": stdout,
                "error": stderr if exit_code != 0 else None
            }
        except Exception as e:
            logger.error(f"Sublist3r error: {e}")
            return {
                "tool": self.tool_name,
                "target": target,
                "status": "failed",
                "error": str(e)
            }


class HttpxTool(SecurityTool):
    """Httpx - HTTP service detection"""
    
    def __init__(self):
        super().__init__("security-tools:httpx", "httpx")
    
    def run(self, targets: List[str], **kwargs) -> Dict:
        """Run Httpx on target URLs/subdomains"""
        # Create input file content
        targets_str = '\n'.join(targets)
        
        command = f"echo '{targets_str}' | /app/httpx -json -o /output/httpx.json"
        
        try:
            stdout, stderr, exit_code = docker_client.run_container(
                image=self.image,
                command=command,
                volumes={},
                remove=True
            )
            
            # Parse JSON results
            results = []
            if stdout:
                for line in stdout.split('\n'):
                    if line.strip():
                        try:
                            results.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            return {
                "tool": self.tool_name,
                "targets": targets,
                "status": "success" if exit_code == 0 else "failed",
                "exit_code": exit_code,
                "results": results,
                "count": len(results),
                "raw_output": stdout,
                "error": stderr if exit_code != 0 else None
            }
        except Exception as e:
            logger.error(f"Httpx error: {e}")
            return {
                "tool": self.tool_name,
                "targets": targets,
                "status": "failed",
                "error": str(e)
            }


class GobusterTool(SecurityTool):
    """Gobuster - Directory and file brute-forcing"""
    
    def __init__(self):
        super().__init__("security-tools:gobuster", "gobuster")
    
    def run(self, target_url: str, wordlist: str = None, **kwargs) -> Dict:
        """Run Gobuster on target URL"""
        # Common directory wordlist
        common_words = "admin\napi\nassets\nbackup\nconfig\ndatabase\ndev\ndocs\ndownload\nexample\nfiles\nimages\nindex\njs\nlogin\nold\nphp\nprivate\npublic\nscripts\nstatic\ntest\ntmp\nupload\nuploads\nwww\ncss\njs\nimg\nimages\nassets\nstatic\npublic\nprivate\nadmin\nadministrator\nlogin\nlogout\nsignin\nsignup\nregister\napi\nv1\nv2\nrest\njson\nxml\nconfig\nconfiguration\nsettings\nsetup\ninstall\ninstaller\nbackup\nbackups\nold\nnew\ntest\ntesting\ndev\ndevelopment\nstaging\nprod\nproduction\ndemo\nsample\nexample\ndocs\ndocumentation\nhelp\nsupport\ncontact\nabout\nindex\nhome\nmain\npage\nwp\nwordpress\nphpmyadmin\nphpinfo\ninfo.php\nphpinfo.php\nrobots.txt\nsitemap.xml"
        
        # Use stdin for wordlist if no wordlist file provided
        if wordlist is None:
            command = f"echo -e '{common_words}' | /app/gobuster dir -u {target_url} -f -k -q"
        else:
            command = f"/app/gobuster dir -u {target_url} -w {wordlist} -f -k -q"
        
        try:
            stdout, stderr, exit_code = docker_client.run_container(
                image=self.image,
                command=command,
                volumes={},
                remove=True
            )
            
            # Parse results
            results = []
            if stdout:
                for line in stdout.split('\n'):
                    if line.strip() and ('Status:' in line or '/' in line):
                        results.append(line.strip())
            
            return {
                "tool": self.tool_name,
                "target": target_url,
                "status": "success" if exit_code == 0 else "failed",
                "exit_code": exit_code,
                "results": results,
                "count": len(results),
                "raw_output": stdout,
                "error": stderr if exit_code != 0 else None
            }
        except Exception as e:
            logger.error(f"Gobuster error: {e}")
            return {
                "tool": self.tool_name,
                "target": target_url,
                "status": "failed",
                "error": str(e)
            }


class ZAPTool(SecurityTool):
    """OWASP ZAP - Web application scanning"""
    
    def __init__(self):
        super().__init__("security-tools:zap", "zap")
    
    def run(self, target_url: str, is_localhost: bool = False, **kwargs) -> Dict:
        """Run ZAP baseline scan on target URL"""
        import re
        from urllib.parse import urlparse
        
        # For localhost testing, convert localhost/127.0.0.1 to host.docker.internal
        # so Docker containers can access the host machine
        scan_url = target_url
        network_mode = None
        
        if is_localhost:
            parsed = urlparse(target_url)
            # Replace localhost or 127.0.0.1 with host.docker.internal
            hostname = parsed.hostname
            if hostname in ('localhost', '127.0.0.1'):
                # Replace the hostname in the URL
                scan_url = target_url.replace(f"{parsed.scheme}://{hostname}", 
                                             f"{parsed.scheme}://host.docker.internal")
                # Use host network mode on Linux, or bridge with host.docker.internal on Mac/Windows
                # For macOS/Windows, host.docker.internal works with bridge network
                # For Linux, we might need host network mode
                network_mode = "bridge"  # host.docker.internal works on Mac/Windows with bridge
        
        # Check if ZAP image exists
        if not docker_client.image_exists(self.image):
            error_msg = f"ZAP Docker image '{self.image}' not found. Please build it using: cd docker-tools/zap && docker build -t {self.image} ."
            logger.error(error_msg)
            return {
                "tool": self.tool_name,
                "target": target_url,
                "status": "failed",
                "exit_code": -1,
                "alerts": [],
                "alert_count": 0,
                "raw_output": "",
                "error": error_msg
            }
        
        # ZAP baseline script requires /zap/wrk to be writable
        # Create the directory in the container and use it
        # Run ZAP baseline scan with JSON output to stdout
        # Use -I flag to not fail on warnings, -J to output JSON, -j for Ajax spider
        # Use shorter timeout and minimal spider time for faster scans
        # Use sh to chain commands (Ubuntu has sh)
        command = f"sh -c 'mkdir -p /zap/wrk && cd /app && python3 zap-baseline.py -t {scan_url} -I -J -j -m 1 -T 2'"
        
        try:
            logger.info(f"Running ZAP scan on {scan_url} (original: {target_url}, is_localhost: {is_localhost})")
            stdout, stderr, exit_code = docker_client.run_container(
                image=self.image,
                command=command,
                volumes={},  # No bind mounts needed
                tmpfs={'/zap/wrk': 'size=100m'},  # Use tmpfs with size limit for writable directory
                remove=True,
                network_mode=network_mode
            )
            logger.info(f"ZAP scan completed with exit code: {exit_code}, stdout length: {len(stdout) if stdout else 0}, stderr length: {len(stderr) if stderr else 0}")
            
            # Parse ZAP results - try JSON first, then parse text output
            alerts = []
            alert_count = 0
            
            try:
                if stdout:
                    # First, try to find JSON in output
                    json_pattern = r'\{.*"@version".*\}'
                    json_match = re.search(json_pattern, stdout, re.DOTALL)
                    
                    if json_match:
                        try:
                            json_str = json_match.group(0)
                            zap_data = json.loads(json_str)
                            
                            # Parse alerts from ZAP JSON structure
                            site_data = zap_data.get('site', [])
                            if isinstance(site_data, list) and len(site_data) > 0:
                                alerts_data = site_data[0].get('alerts', [])
                                for alert_data in alerts_data:
                                    alert = {
                                        "name": alert_data.get("name", "Security Issue"),
                                        "risk": alert_data.get("risk", "Info"),
                                        "description": alert_data.get("description", ""),
                                        "solution": alert_data.get("solution", ""),
                                        "evidence": alert_data.get("evidence", ""),
                                        "url": alert_data.get("url", target_url)
                                    }
                                    alerts.append(alert)
                                    alert_count += 1
                        except (json.JSONDecodeError, KeyError, IndexError, AttributeError):
                            pass
                    
                    # If no JSON alerts found, parse text output for WARN and FAIL messages
                    if alert_count == 0:
                        # Parse WARN-NEW and FAIL-NEW lines
                        warn_pattern = r'WARN-NEW:\s+(.+?)\s+\[(\d+)\]\s+x\s+(\d+)'
                        fail_pattern = r'FAIL-NEW:\s+(.+?)\s+\[(\d+)\]\s+x\s+(\d+)'
                        
                        # Collect all warnings
                        warnings = {}
                        current_warning = None
                        lines = stdout.split('\n')
                        
                        for i, line in enumerate(lines):
                            # Check for WARN-NEW or FAIL-NEW header
                            warn_match = re.search(warn_pattern, line)
                            fail_match = re.search(fail_pattern, line)
                            
                            if warn_match:
                                name = warn_match.group(1).strip()
                                alert_id = warn_match.group(2)
                                count = int(warn_match.group(3))
                                current_warning = name
                                warnings[name] = {
                                    "name": name,
                                    "risk": "Medium",
                                    "alert_id": alert_id,
                                    "count": count,
                                    "urls": []
                                }
                            elif fail_match:
                                name = fail_match.group(1).strip()
                                alert_id = fail_match.group(2)
                                count = int(fail_match.group(3))
                                current_warning = name
                                warnings[name] = {
                                    "name": name,
                                    "risk": "High",
                                    "alert_id": alert_id,
                                    "count": count,
                                    "urls": []
                                }
                            elif current_warning and line.strip() and line.strip().startswith('http'):
                                # This is a URL for the current warning
                                url_match = re.search(r'(https?://[^\s]+)', line)
                                if url_match:
                                    url = url_match.group(1)
                                    if url not in warnings[current_warning]["urls"]:
                                        warnings[current_warning]["urls"].append(url)
                        
                        # Convert warnings to alerts
                        for warning_name, warning_data in warnings.items():
                            for url in warning_data["urls"]:
                                alert = {
                                    "name": warning_data["name"],
                                    "risk": warning_data["risk"],
                                    "description": f"ZAP detected {warning_data['name']} (Alert ID: {warning_data['alert_id']})",
                                    "solution": "Review and fix the security issue identified by ZAP",
                                    "evidence": f"Found on {url}",
                                    "url": url
                                }
                                alerts.append(alert)
                                alert_count += 1
                            
                            # If no URLs found, create at least one alert
                            if not warning_data["urls"]:
                                alert = {
                                    "name": warning_data["name"],
                                    "risk": warning_data["risk"],
                                    "description": f"ZAP detected {warning_data['name']} (Alert ID: {warning_data['alert_id']}, Count: {warning_data['count']})",
                                    "solution": "Review and fix the security issue identified by ZAP",
                                    "evidence": f"Found {warning_data['count']} instance(s)",
                                    "url": target_url
                                }
                                alerts.append(alert)
                                alert_count += 1
                                    
            except Exception as e:
                logger.warning(f"Failed to parse ZAP output: {e}")
                # If parsing fails completely, create a generic alert
                if stdout and ("FAIL" in stdout.upper() or "WARN" in stdout.upper()):
                    alerts.append({
                        "name": "ZAP Scan Completed with Issues",
                        "risk": "Info",
                        "description": "ZAP scan completed. Check raw output for details.",
                        "solution": "",
                        "evidence": "",
                        "url": target_url
                    })
                    alert_count = 1
            
            # Determine status based on exit code and alerts
            # ZAP may return non-zero exit code even on success if warnings are found
            # Check if we got alerts or if output indicates success
            status = "success"
            if exit_code != 0 and exit_code != 2:  # Exit code 2 is warning, not failure
                # Check if ZAP actually failed or just found issues
                if "Failed to start ZAP" in stdout or "Failed to start ZAP" in (stderr or ""):
                    status = "failed"
                elif alert_count > 0:
                    # If we have alerts, consider it success even with non-zero exit
                    status = "completed_with_alerts"
                else:
                    status = "failed"
            elif alert_count > 0:
                status = "completed_with_alerts"
            
            return {
                "tool": self.tool_name,
                "target": target_url,
                "status": status,
                "exit_code": exit_code,
                "alerts": alerts,
                "alert_count": alert_count,
                "raw_output": stdout[:5000] if stdout else "",  # Limit output size
                "error": stderr if exit_code != 0 and stderr else None
            }
        except Exception as e:
            logger.error(f"ZAP error: {e}", exc_info=True)
            error_msg = str(e)
            # Include stderr if available in the exception
            if hasattr(e, 'stderr') and e.stderr:
                error_msg = f"{error_msg}\nStderr: {e.stderr}"
            return {
                "tool": self.tool_name,
                "target": target_url,
                "status": "failed",
                "exit_code": -1,
                "alerts": [],
                "alert_count": 0,
                "raw_output": "",
                "error": error_msg
            }


class NucleiTool(SecurityTool):
    """Nuclei - Template-based vulnerability scanning"""
    
    def __init__(self):
        super().__init__("security-tools:nuclei", "nuclei")
    
    def run(self, target_url: str, **kwargs) -> Dict:
        """Run Nuclei on target URL"""
        # Nuclei v3.5.1 uses -j or -jsonl for JSON lines output (one JSON object per line)
        # Use -silent to reduce noise, -nc for no color
        # -timeout for request timeout, -rate-limit to avoid overwhelming target
        command = f"/app/nuclei -u {target_url} -j -silent -nc -timeout 30 -rate-limit 50"
        
        try:
            stdout, stderr, exit_code = docker_client.run_container(
                image=self.image,
                command=command,
                volumes={},
                remove=True
            )
            
            # Parse Nuclei JSON results
            findings = []
            if stdout:
                for line in stdout.split('\n'):
                    if line.strip():
                        try:
                            findings.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            return {
                "tool": self.tool_name,
                "target": target_url,
                "status": "success" if exit_code == 0 else "failed",
                "exit_code": exit_code,
                "findings": findings,
                "count": len(findings),
                "raw_output": stdout,
                "error": stderr if exit_code != 0 else None
            }
        except Exception as e:
            logger.error(f"Nuclei error: {e}")
            return {
                "tool": self.tool_name,
                "target": target_url,
                "status": "failed",
                "error": str(e)
            }


class SQLMapTool(SecurityTool):
    """SQLMap - SQL injection testing"""
    
    def __init__(self):
        super().__init__("security-tools:sqlmap", "sqlmap")
    
    def run(self, target_url: str, **kwargs) -> Dict:
        """Run SQLMap on target URL"""
        command = f"python3 /app/sqlmap/sqlmap.py -u {target_url} --batch --level=1 --risk=1 --output-dir=/output"
        
        try:
            stdout, stderr, exit_code = docker_client.run_container(
                image=self.image,
                command=command,
                volumes={},
                remove=True
            )
            
            # Parse SQLMap results
            vulnerabilities = []
            if stdout:
                # SQLMap outputs detailed information
                if "sqlmap identified the following injection point" in stdout.lower():
                    vulnerabilities.append({
                        "vulnerable": True,
                        "details": stdout
                    })
            
            return {
                "tool": self.tool_name,
                "target": target_url,
                "status": "success" if exit_code == 0 else "failed",
                "exit_code": exit_code,
                "vulnerabilities": vulnerabilities,
                "vulnerable": len(vulnerabilities) > 0,
                "raw_output": stdout,
                "error": stderr if exit_code != 0 else None
            }
        except Exception as e:
            logger.error(f"SQLMap error: {e}")
            return {
                "tool": self.tool_name,
                "target": target_url,
                "status": "failed",
                "error": str(e)
            }


class SemgrepTool(SecurityTool):
    """Semgrep - Static analysis tool for finding bugs and security issues"""
    
    def __init__(self):
        super().__init__("security-tools:semgrep", "semgrep")
    
    def run(self, source_path: str = None, target_url: str = None, **kwargs) -> Dict:
        """
        Run Semgrep on source code or target URL
        
        For localhost testing, if target_url is provided, we'll use Semgrep's
        security rules to check for common buffer overflow and security patterns.
        Since Semgrep scans source code, we'll use predefined security rule sets
        that can identify common vulnerabilities.
        """
        import os
        import tempfile
        
        # For localhost URL testing, we don't have source code
        # So we'll run Semgrep with security rules that check for common patterns
        # We'll create a minimal test file to demonstrate the tool
        
        scan_path = source_path or "/source"
        volumes = {}
        empty_json = '{"results":[]}'
        
        # Priority 1: If source_path is provided, scan real source code
        # Note: We don't check os.path.exists() here because we're in a Linux container
        # and the path is on the Windows host. Docker will handle mounting it.
        if source_path and source_path.strip():
            # Normalize Windows path separators for Docker
            # Docker on Windows can handle both \ and /, but let's normalize
            normalized_path = source_path.replace('\\', '/')
            # Remove trailing slash if present
            normalized_path = normalized_path.rstrip('/')
            
            volumes[source_path] = {"bind": "/source", "mode": "ro"}
            # Use 'auto' config which automatically detects language and uses appropriate security rules
            # This works better for C#, Python, JavaScript, etc. than just p/security-audit
            # Add --max-memory and --timeout to prevent hanging on large codebases
            command = (
                "sh -c '"
                "semgrep --config=auto --config=p/security-audit --json --output=/output/semgrep.json --max-memory 4000 --timeout 240 /source 2>&1 || true && "
                "if [ -f /output/semgrep.json ]; then cat /output/semgrep.json; else echo '" + empty_json + "'; fi"
                "'"
            )
            logger.info(f"Scanning real source code from: {source_path} (mounted to /source in container)")
        # Priority 2: If target_url is provided but no source_path, create test files
        elif target_url and not source_path:
            # For localhost URL testing, create test files with known vulnerabilities
            # Use a more reliable method to create files with proper formatting
            # We'll use Python's multi-line string approach via a script
            # Use shell heredoc to create files reliably
            command = (
                "sh -c '"
                "mkdir -p /source /output && "
                "cat > /source/vulnerable.c << \"EOFC\"\n"
                "#include <string.h>\n"
                "#include <stdio.h>\n"
                "void buffer_overflow_vuln(char *input) {\n"
                "    char buffer[10];\n"
                "    strcpy(buffer, input);\n"
                "    printf(\"%s\", buffer);\n"
                "}\n"
                "int main() {\n"
                "    char data[100] = \"AAAAAAAAAAAAAAAA\";\n"
                "    buffer_overflow_vuln(data);\n"
                "    return 0;\n"
                "}\n"
                "EOFC\n"
                "cat > /source/vulnerable.py << \"EOFPY\"\n"
                "import os\n"
                "def command_injection(user_input):\n"
                "    os.system(f\"ls {user_input}\")\n"
                "def hardcoded_password():\n"
                "    password = \"admin123\"\n"
                "    return password\n"
                "EOFPY\n"
                "semgrep --config=p/security-audit --json --output=/output/semgrep.json /source 2>&1 && "
                "if [ -f /output/semgrep.json ]; then cat /output/semgrep.json; else echo '" + empty_json + "'; fi"
                "'"
            )
            volumes = {}
        else:
            # Default: use security rules
            command = (
                "sh -c '"
                "mkdir -p /source && "
                "semgrep --config=p/security-audit --json --output=/output/semgrep.json /source 2>&1 || true && "
                "cat /output/semgrep.json 2>/dev/null || echo '" + empty_json + "'"
                "'"
            )
        
        try:
            stdout, stderr, exit_code = docker_client.run_container(
                image=self.image,
                command=command,
                volumes=volumes,
                remove=True
            )
            
            # Parse Semgrep JSON results
            findings = []
            try:
                # Try to parse JSON output
                if stdout:
                    # Find JSON in output
                    json_start = stdout.find('{')
                    json_end = stdout.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = stdout[json_start:json_end]
                        semgrep_data = json.loads(json_str)
                        findings = semgrep_data.get("results", [])
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse Semgrep JSON: {e}")
                # Parse text output if JSON fails
                if stdout:
                    for line in stdout.split('\n'):
                        if 'rule:' in line.lower() or 'severity:' in line.lower():
                            findings.append({"raw": line.strip()})
            
            # Convert findings to our format
            formatted_findings = []
            for finding in findings:
                # Extract message from extra.message field
                extra = finding.get("extra", {})
                message = extra.get("message", finding.get("message", ""))
                if not message:
                    # Fallback to rule_id if no message
                    message = finding.get("check_id", "Security issue detected")
                
                formatted_findings.append({
                    "rule_id": finding.get("check_id", finding.get("rule_id", "unknown")),
                    "message": message,
                    "severity": extra.get("severity", "INFO"),
                    "path": finding.get("path", "unknown"),
                    "line": finding.get("start", {}).get("line", 0),
                    "column": finding.get("start", {}).get("col", 0),
                    "category": extra.get("metadata", {}).get("category", "security")
                })
            
            return {
                "tool": self.tool_name,
                "target": target_url or source_path or scan_path,
                "status": "success" if exit_code == 0 or findings else "failed",
                "exit_code": exit_code,
                "findings": formatted_findings,
                "count": len(formatted_findings),
                "raw_output": stdout[:5000] if stdout else "",  # Limit output size
                "error": stderr if exit_code != 0 and stderr else None
            }
        except Exception as e:
            logger.error(f"Semgrep error: {e}", exc_info=True)
            return {
                "tool": self.tool_name,
                "target": target_url or source_path or scan_path,
                "status": "failed",
                "error": str(e),
                "findings": [],
                "count": 0
            }


class AddressSanitizerTool(SecurityTool):
    """AddressSanitizer (ASan) - Memory safety testing for C/C++"""
    
    def __init__(self):
        super().__init__("security-tools:addresssanitizer", "addresssanitizer")
    
    def run(self, source_path: str = None, **kwargs) -> Dict:
        """
        Run AddressSanitizer on C/C++ code.

        Behaviour:
        - If source_path is provided, mount it at /source and try to compile all *.c / *.cc / *.cpp
          files in that directory with -fsanitize=address,undefined, then run the binary.
        - If no source_path is provided, a small intentionally vulnerable C program is created
          inside the container, compiled with ASan, and executed to demonstrate detection.
        """
        import os

        volumes: Dict[str, Dict[str, str]] = {}

        if source_path and source_path.strip():
            # Mount provided host directory into /source (read-only)
            host_path = os.path.abspath(source_path)
            volumes[host_path] = {"bind": "/source", "mode": "ro"}
            use_demo = "false"
        else:
            # No external source; create a demo vulnerable program under /source
            use_demo = "true"

        # Use the run script in the image - run via sh so env var is passed
        command = ["sh", "-c", f"USE_DEMO={use_demo} /app/run_asan.sh"]

        try:
            stdout, stderr, exit_code = docker_client.run_container(
                image=self.image,
                command=command,
                volumes=volumes,
                remove=True,
            )

            full_output = (stdout or "") + ("\n" + stderr if stderr else "")
            asan_errors: List[Dict[str, str]] = []

            if "ERROR: AddressSanitizer" in full_output:
                status = "completed_with_issues"
                current_block: List[str] = []
                capturing = False
                for line in full_output.splitlines():
                    if "ERROR: AddressSanitizer" in line:
                        if current_block:
                            asan_errors.append({"raw": "\n".join(current_block)})
                            current_block = []
                        capturing = True
                    if capturing:
                        current_block.append(line)
                        if line.strip() == "":
                            capturing = False
                if current_block:
                    asan_errors.append({"raw": "\n".join(current_block)})
            else:
                status = "success" if exit_code == 0 else "failed"

            return {
                "tool": self.tool_name,
                "status": status,
                "exit_code": exit_code,
                "errors": asan_errors,
                "error_count": len(asan_errors),
                "raw_output": full_output[:5000],
                "error": stderr if exit_code != 0 and stderr else None,
            }
        except Exception as e:
            logger.error(f"AddressSanitizer error: {e}", exc_info=True)
            return {
                "tool": self.tool_name,
                "status": "failed",
                "exit_code": -1,
                "errors": [],
                "error_count": 0,
                "raw_output": "",
                "error": str(e),
            }

