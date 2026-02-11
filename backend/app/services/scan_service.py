"""
Scan service for orchestrating security tool execution
"""
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.job import ScanJob, Finding, VulnerabilityDefinition, ToolExecution, JobStatus, FindingSeverity, FindingStatus
from app.models.target import Target
from app.models.tool import Tool
from app.docker.tools import (
    Sublist3rTool,
    HttpxTool,
    GobusterTool,
    ZAPTool,
    NucleiTool,
    SQLMapTool,
    SemgrepTool,
    AddressSanitizerTool,
    GhauriTool,
)

logger = logging.getLogger(__name__)


class ScanService:
    """Service for orchestrating security scans"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tools = {
            'sublist3r': Sublist3rTool(),
            'httpx': HttpxTool(),
            'gobuster': GobusterTool(),
            'zap': ZAPTool(),
            'nuclei': NucleiTool(),
            'sqlmap': SQLMapTool(),
            'semgrep': SemgrepTool(),
            'addresssanitizer': AddressSanitizerTool(),
            'ghauri': GhauriTool(),
        }
    
    def _store_tool_execution(
        self, 
        job: ScanJob, 
        tool: Tool, 
        stage_number: int, 
        stage_name: str,
        input_data: Dict,
        result: Dict,
        execution_time: int = None
    ):
        """Store tool execution output in database"""
        import json
        
        # Normalize status to fit database constraint (max 50 chars)
        status = result.get("status", "completed")
        if status == "completed_with_alerts":
            status = "completed"  # Store as completed, alerts are in findings
        elif len(status) > 50:
            status = status[:47] + "..."
        
        execution = ToolExecution(
            job_id=job.job_id,
            tool_id=tool.id,
            stage_number=stage_number,
            stage_name=stage_name,
            status=status,
            execution_time=execution_time,
            started_at=datetime.utcnow(),  # Could be improved with actual start time
            completed_at=datetime.utcnow(),
            output=json.dumps(result, default=str)[:50000] if result else None,  # Limit size
            raw_output=result.get("raw_output", "")[:10000] if result else None,  # Limit size
            error=result.get("error")[:5000] if result.get("error") else None,  # Limit error size
            input_data=json.dumps(input_data, default=str)[:10000] if input_data else None  # Limit size
        )
        self.db.add(execution)
        self.db.commit()
        return execution

    def execute_scan(self, job_id: int) -> Dict:
        """Execute full scan workflow for a job"""
        job = self.db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Get target
        target = self.db.query(Target).filter(Target.id == job.target_id).first()
        if not target:
            raise ValueError(f"Target {job.target_id} not found")
        
        target_url = target.url
        
        try:
            # Update job status to running
            job.status = JobStatus.RUNNING.value
            self.db.commit()
            
            # Get or create tools
            tools_map = self._get_tools_map()
            
            # Stage 1: Subdomain Enumeration
            logger.info(f"Starting Stage 1: Subdomain Enumeration for {target_url}")
            try:
                subdomains = self._run_sublist3r(job, target, tools_map.get('sublist3r'), {"target_url": target_url})
                logger.info(f"Stage 1 completed: Found {len(subdomains)} subdomains")
            except Exception as e:
                logger.error(f"Stage 1 failed but continuing: {e}")
                subdomains = []  # Continue with empty list
            
            # Stage 2: HTTP Service Detection (uses subdomains from Stage 1)
            logger.info(f"Starting Stage 2: HTTP Service Detection")
            try:
                http_services = self._run_httpx(job, target, subdomains, tools_map.get('httpx'), {"subdomains": subdomains})
                logger.info(f"Stage 2 completed: Found {len(http_services)} live HTTP services")
            except Exception as e:
                logger.error(f"Stage 2 failed but continuing: {e}")
                http_services = [target_url]  # Fallback to original target
            
            # Stage 3: Directory Discovery (uses primary URL from Stage 2)
            primary_url = http_services[0] if http_services else target_url
            logger.info(f"Starting Stage 3: Directory Discovery for {primary_url}")
            try:
                self._run_gobuster(job, target, primary_url, tools_map.get('gobuster'), {"target_url": primary_url, "http_services": http_services})
                logger.info(f"Stage 3 completed")
            except Exception as e:
                logger.error(f"Stage 3 failed but continuing: {e}")
            
            # Stage 4: Web Application Scanning (uses primary URL)
            logger.info(f"Starting Stage 4: Web Application Scanning for {primary_url}")
            try:
                self._run_zap(job, target, primary_url, tools_map.get('zap'), {"target_url": primary_url})
                logger.info(f"Stage 4 completed")
            except Exception as e:
                logger.error(f"Stage 4 failed but continuing: {e}")
            
            # Stage 5: Template-Based Scanning (uses primary URL)
            logger.info(f"Starting Stage 5: Template-Based Scanning for {primary_url}")
            try:
                self._run_nuclei(job, target, primary_url, tools_map.get('nuclei'), {"target_url": primary_url})
                logger.info(f"Stage 5 completed")
            except Exception as e:
                logger.error(f"Stage 5 failed but continuing: {e}")
            
            # Stage 6: SQL Injection Testing (uses primary URL)
            logger.info(f"Starting Stage 6: SQL Injection Testing for {primary_url}")
            try:
                self._run_sqlmap(job, target, primary_url, tools_map.get('sqlmap'), {"target_url": primary_url})
                logger.info(f"Stage 6 completed")
            except Exception as e:
                logger.error(f"Stage 6 failed but continuing: {e}")
            
            # Update job status to completed
            job.status = JobStatus.COMPLETED.value
            job.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Scan completed successfully for job {job_id}")
            return {
                "job_id": job.job_id,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Scan failed for job {job_id}: {e}")
            job.status = JobStatus.FAILED.value
            job.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def execute_zap_only(self, job_id: int) -> Dict:
        """Execute only the OWASP ZAP stage for a job (development/local testing)"""
        from urllib.parse import urlparse
        
        job = self.db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        target = self.db.query(Target).filter(Target.id == job.target_id).first()
        if not target:
            raise ValueError(f"Target {job.target_id} not found")

        try:
            job.status = JobStatus.RUNNING.value
            self.db.commit()

            # Check if target is localhost for special handling
            parsed = urlparse(target.url)
            is_localhost = parsed.hostname in ('localhost', '127.0.0.1')
            
            # Run ZAP directly (not through _run_zap to avoid database finding creation)
            logger.info(f"Starting ZAP scan for job {job_id}, target: {target.url}, is_localhost: {is_localhost}")
            zap_result = self.tools['zap'].run(target.url, is_localhost=is_localhost)
            logger.info(f"ZAP scan result: status={zap_result.get('status')}, exit_code={zap_result.get('exit_code')}, alert_count={zap_result.get('alert_count', 0)}")
            
            # Log any errors from ZAP
            if zap_result.get("error"):
                logger.error(f"ZAP scan error: {zap_result.get('error')}")
            if zap_result.get("status") == "failed":
                error_info = zap_result.get("error", "Unknown error")
                raw_output = zap_result.get("raw_output", "")
                logger.error(f"ZAP scan failed. Error: {error_info}, Raw output (first 1000 chars): {raw_output[:1000] if raw_output else 'None'}")
            
            # Get or create ZAP tool
            tools_map = self._get_tools_map()
            zap_tool = tools_map.get('zap')
            
            # Parse and format alerts for frontend and create findings
            formatted_alerts = []
            severity_map = {
                'High': FindingSeverity.HIGH,
                'Medium': FindingSeverity.MEDIUM,
                'Low': FindingSeverity.LOW,
                'Informational': FindingSeverity.INFO
            }
            
            for alert in zap_result.get("alerts", []):
                formatted_alert = {
                    "name": alert.get("name", "Security Issue"),
                    "risk": alert.get("risk", "Info"),
                    "description": alert.get("description", ""),
                    "solution": alert.get("solution", ""),
                    "evidence": alert.get("evidence", ""),
                    "url": alert.get("url", target.url)
                }
                formatted_alerts.append(formatted_alert)
                
                # Create finding in database
                if zap_tool:
                    name = alert.get("name", "Security Issue")
                    severity_str = alert.get("risk", "Low")
                    severity = severity_map.get(severity_str, FindingSeverity.LOW)
                    
                    vuln_def = self._get_or_create_vulnerability(
                        name,
                        alert.get("description", ""),
                        alert.get("solution", "")
                    )
                    
                    self._create_finding(
                        job, target, zap_tool, vuln_def,
                        severity,
                        location=alert.get("url", target.url),
                        evidence=alert.get("evidence", ""),
                        confidence="high" if severity_str == "High" else "medium"
                    )
            
            # Update job status based on result
            if zap_result.get("status") == "failed":
                job.status = JobStatus.FAILED.value
                error_msg = zap_result.get("error", "ZAP scan failed with unknown error")
                raw_output = zap_result.get("raw_output", "")
                logger.error(f"ZAP scan failed for job {job_id}. Error: {error_msg}")
                if raw_output:
                    logger.error(f"ZAP raw output (first 2000 chars): {raw_output[:2000]}")
            else:
                job.status = JobStatus.COMPLETED.value
            
            job.completed_at = datetime.utcnow()
            self.db.commit()

            return {
                "job_id": job.job_id,
                "status": job.status,
                "alerts": formatted_alerts,
                "alert_count": zap_result.get("alert_count", len(formatted_alerts)),
                "raw_output": zap_result.get("raw_output", ""),
                "error": zap_result.get("error"),  # Include error in response for debugging
            }
        except Exception as e:
            logger.error(f"Local ZAP scan failed for job {job_id}: {e}", exc_info=True)
            job.status = JobStatus.FAILED.value
            job.completed_at = datetime.utcnow()
            self.db.commit()
            raise
    
    def execute_localhost_testing(self, job_id: int, source_path: str = None) -> Dict:
        """
        Execute localhost testing scan using AddressSanitizer (primary tool).

        This method is optimized for localhost/127.0.0.1 targets and focuses on:
        - AddressSanitizer - runtime detection of memory safety bugs in C/C++ code

        Note: SQLMap is available but not used by default. It can be enabled later if needed.
        """
        from urllib.parse import urlparse
        
        job = self.db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        target = self.db.query(Target).filter(Target.id == job.target_id).first()
        if not target:
            raise ValueError(f"Target {job.target_id} not found")

        try:
            job.status = JobStatus.RUNNING.value
            self.db.commit()
            
            target_url = target.url
            parsed = urlparse(target_url)
            is_localhost = parsed.hostname in ('localhost', '127.0.0.1')
            
            if not is_localhost:
                raise ValueError("Localhost testing only supports localhost or 127.0.0.1 targets")
            
            # Initialize results for localhost testing
            all_results = {
                "job_id": job.job_id,
                "target_url": target_url,
                "status": "running",
                "results": {},
                "alerts": [],
                "findings": [],
                "vulnerabilities": []
            }

            # Get tools from database (includes AddressSanitizer and Ghauri)
            tools_map = self._get_tools_map()
            asan_tool = tools_map.get('addresssanitizer')
            ghauri_tool = tools_map.get('ghauri')

            # Stage 1: AddressSanitizer - Primary tool for buffer overflow and memory safety analysis
            logger.info(f"Starting AddressSanitizer run for job {job_id}, target: {target_url}")
            try:
                stage_start = datetime.utcnow()
                asan_result = self.tools['addresssanitizer'].run(source_path=source_path)
                execution_time = int((datetime.utcnow() - stage_start).total_seconds())

                # Store tool execution
                if asan_tool:
                    self._store_tool_execution(
                        job,
                        asan_tool,
                        1,
                        "Localhost Testing: AddressSanitizer Memory Safety Analysis",
                        {"target_url": target_url, "source_path": source_path},
                        asan_result,
                        execution_time,
                    )

                all_results["results"]["addresssanitizer"] = asan_result

                # Convert ASan errors to alerts/findings
                for err in asan_result.get("errors", []):
                    raw_block = err.get("raw", "")
                    alert = {
                        "name": "AddressSanitizer memory error",
                        "risk": "High",
                        "description": "AddressSanitizer detected a memory safety violation.",
                        "solution": "Investigate the reported stack trace and fix the offending code.",
                        "evidence": raw_block[:500] if raw_block else "",
                        "url": target_url,
                        "tool": "addresssanitizer",
                        "category": "memory-safety",
                    }
                    all_results["alerts"].append(alert)
                    all_results["findings"].append(
                        {
                            "tool": "addresssanitizer",
                            "message": "AddressSanitizer detected a memory safety violation.",
                            "raw": raw_block,
                        }
                    )

                logger.info(
                    f"AddressSanitizer run completed: "
                    f"{asan_result.get('error_count', 0)} memory errors detected"
                )
            except Exception as e:
                logger.error(f"AddressSanitizer run failed: {e}", exc_info=True)
                all_results["results"]["addresssanitizer"] = {
                    "status": "failed",
                    "error": str(e),
                }

            # Stage 2: Ghauri - SQL injection detection/exploitation (blind SQLi, PostgreSQL-friendly)
            logger.info(f"Starting Ghauri run for job {job_id}, target: {target_url}")
            try:
                stage_start = datetime.utcnow()
                ghauri_result = self.tools['ghauri'].run(target_url=target_url, is_localhost=True)
                execution_time = int((datetime.utcnow() - stage_start).total_seconds())

                if ghauri_tool:
                    self._store_tool_execution(
                        job,
                        ghauri_tool,
                        2,
                        "Localhost Testing: Ghauri SQL Injection Testing",
                        {"target_url": target_url},
                        ghauri_result,
                        execution_time,
                    )

                all_results["results"]["ghauri"] = ghauri_result

                if ghauri_result.get("vulnerable"):
                    alert = {
                        "name": "SQL Injection (Ghauri)",
                        "risk": "CRITICAL",
                        "description": "Ghauri detected a possible SQL injection. Use parameterized queries and sanitize inputs.",
                        "solution": "Use parameterized queries/prepared statements and sanitize all user inputs.",
                        "evidence": (ghauri_result.get("raw_output") or "")[:500],
                        "url": target_url,
                        "tool": "ghauri",
                        "category": "sql-injection",
                    }
                    all_results["alerts"].append(alert)
                    all_results["findings"].append({
                        "tool": "ghauri",
                        "message": "SQL injection detected or database enumerated by Ghauri.",
                        "raw": ghauri_result.get("raw_output", ""),
                    })
                    if ghauri_result.get("databases"):
                        all_results["findings"].append({
                            "tool": "ghauri",
                            "message": f"Databases enumerated: {', '.join(ghauri_result['databases'])}",
                            "raw": "",
                        })
                logger.info(f"Ghauri run completed: vulnerable={ghauri_result.get('vulnerable', False)}")
            except Exception as e:
                logger.error(f"Ghauri run failed: {e}", exc_info=True)
                all_results["results"]["ghauri"] = {
                    "status": "failed",
                    "error": str(e),
                }

            # SQLMap is optional - commented out for now, but can be enabled later if needed
            # Uncomment below to enable SQLMap scanning
            # Stage 2: SQLMap - SQL injection testing (OPTIONAL)
            # logger.info(f"Starting SQLMap scan for job {job_id}, target: {target_url}")
            # try:
            #     stage_start = datetime.utcnow()
            #     sqlmap_result = self.tools['sqlmap'].run(target_url=target_url)
            #     execution_time = int((datetime.utcnow() - stage_start).total_seconds())
            #     
            #     # Store tool execution
            #     if sqlmap_tool:
            #         self._store_tool_execution(
            #             job, sqlmap_tool, 2, "Localhost Testing: SQL Injection Testing",
            #             {"target_url": target_url}, sqlmap_result, execution_time
            #         )
            #     
            #     all_results["results"]["sqlmap"] = sqlmap_result
            #     
            #     # Convert SQLMap vulnerabilities to alerts
            #     if sqlmap_result.get("vulnerable"):
            #         alert = {
            #             "name": "SQL Injection Vulnerability",
            #             "risk": "CRITICAL",
            #             "description": "SQL injection vulnerability detected in the target application",
            #             "solution": "Use parameterized queries and sanitize all user inputs",
            #             "evidence": sqlmap_result.get("raw_output", "")[:500],
            #             "url": target_url,
            #             "tool": "sqlmap"
            #         }
            #         all_results["alerts"].append(alert)
            #         all_results["vulnerabilities"].extend(sqlmap_result.get("vulnerabilities", []))
            #         
            #         # Create database finding if tool exists
            #         if sqlmap_tool:
            #             vuln_def = self._get_or_create_vulnerability(
            #                 "SQL Injection",
            #                 "SQL injection vulnerability detected",
            #                 "Sanitize all user inputs and use parameterized queries"
            #             )
            #             self._create_finding(
            #                 job, target, sqlmap_tool, vuln_def,
            #                 FindingSeverity.CRITICAL,
            #                 location=target_url,
            #                 evidence=sqlmap_result.get("raw_output", ""),
            #                 confidence="high"
            #             )
            #     
            #     logger.info(f"SQLMap scan completed: vulnerable={sqlmap_result.get('vulnerable', False)}")
            # except Exception as e:
            #     logger.error(f"SQLMap scan failed: {e}", exc_info=True)
            #     all_results["results"]["sqlmap"] = {
            #         "status": "failed",
            #         "error": str(e)
            #     }
            
            # Update job status
            job.status = JobStatus.COMPLETED.value
            job.completed_at = datetime.utcnow()
            self.db.commit()
            
            all_results["status"] = "completed"
            all_results["alert_count"] = len(all_results["alerts"])
            
            return all_results
            
        except Exception as e:
            logger.error(f"Localhost testing scan failed: {e}", exc_info=True)
            job.status = JobStatus.FAILED.value
            job.completed_at = datetime.utcnow()
            self.db.commit()
            raise
    
    def _get_tools_map(self) -> Dict[str, Tool]:
        """Get or create tool records in database"""
        tools_map = {}
        for tool_name in ['sublist3r', 'httpx', 'gobuster', 'zap', 'nuclei', 'sqlmap', 'semgrep', 'addresssanitizer', 'ghauri']:
            tool = self.db.query(Tool).filter(Tool.name == tool_name).first()
            if not tool:
                # Create tool record
                docker_images = {
                    'sublist3r': 'security-tools:sublist3r',
                    'httpx': 'security-tools:httpx',
                    'gobuster': 'security-tools:gobuster',
                    'zap': 'security-tools:zap',
                    'nuclei': 'security-tools:nuclei',
                    'sqlmap': 'security-tools:sqlmap',
                    'semgrep': 'security-tools:semgrep',
                    'addresssanitizer': 'security-tools:addresssanitizer',
                    'ghauri': 'security-tools:ghauri',
                }
                display_names = {
                    'sublist3r': 'Sublist3r',
                    'httpx': 'Httpx',
                    'gobuster': 'Gobuster',
                    'zap': 'OWASP ZAP',
                    'nuclei': 'Nuclei',
                    'sqlmap': 'SQLMap',
                    'semgrep': 'Semgrep',
                    'addresssanitizer': 'AddressSanitizer',
                    'ghauri': 'Ghauri',
                }
                tool = Tool(
                    name=tool_name,
                    display_name=display_names[tool_name],
                    docker_image=docker_images[tool_name],
                    celery_queue='scans',
                    category='Security Scanning'
                )
                self.db.add(tool)
                self.db.commit()
                self.db.refresh(tool)
            tools_map[tool_name] = tool
        return tools_map
    
    def _get_or_create_vulnerability(self, name: str, description: str = None, recommendation: str = None) -> VulnerabilityDefinition:
        """Get or create a vulnerability definition"""
        vuln = self.db.query(VulnerabilityDefinition).filter(VulnerabilityDefinition.name == name).first()
        if not vuln:
            vuln = VulnerabilityDefinition(
                name=name,
                description=description,
                recommendation=recommendation
            )
            self.db.add(vuln)
            self.db.commit()
            self.db.refresh(vuln)
        return vuln
    
    def _create_finding(
        self, 
        job: ScanJob, 
        target: Target, 
        tool: Tool, 
        vuln_def: VulnerabilityDefinition,
        severity: FindingSeverity,
        location: str = None,
        evidence: str = None,
        confidence: str = None
    ):
        """Create a finding record"""
        finding = Finding(
            job_id=job.job_id,
            tool_id=tool.id,
            definition_id=vuln_def.id,
            target_id=target.id,
            severity=severity,
            status=FindingStatus.NEW,
            location=location,
            evidence=evidence,
            confidence=confidence
        )
        self.db.add(finding)
        self.db.commit()
    
    def _run_sublist3r(self, job: ScanJob, target: Target, tool: Tool, input_data: Dict = None) -> List[str]:
        """Run Sublist3r and return subdomains"""
        from urllib.parse import urlparse
        
        try:
            # Extract domain from URL (Sublist3r needs domain, not full URL)
            parsed = urlparse(target.url)
            domain = parsed.netloc or parsed.path.split('/')[0] if parsed.path else target.url
            # Remove port if present
            domain = domain.split(':')[0]
            
            stage_start = datetime.utcnow()
            result = self.tools['sublist3r'].run(domain)
            execution_time = int((datetime.utcnow() - stage_start).total_seconds())
            
            # Store tool execution
            self._store_tool_execution(
                job, tool, 1, "Stage 1: Subdomain Enumeration",
                input_data or {"target_url": target.url, "domain": domain}, result, execution_time
            )
            
            subdomains = result.get("subdomains", [])
            
            if subdomains:
                vuln_def = self._get_or_create_vulnerability(
                    "Subdomain Discovery",
                    "Subdomains discovered during enumeration"
                )
                for subdomain in subdomains[:10]:  # Limit to first 10
                    self._create_finding(
                        job, target, tool, vuln_def,
                        FindingSeverity.INFO,
                        location=subdomain,
                        evidence=f"Discovered subdomain: {subdomain}"
                    )
            
            return subdomains
        except Exception as e:
            logger.error(f"Stage 1 (Sublist3r) failed: {e}", exc_info=True)
            # Store failed execution
            try:
                self._store_tool_execution(
                    job, tool, 1, "Stage 1: Subdomain Enumeration",
                    input_data or {"target_url": target.url}, 
                    {"status": "failed", "error": str(e)}, 0
                )
            except:
                pass
            # Return empty list to continue scan
            return []
    
    def _run_httpx(self, job: ScanJob, target: Target, subdomains: List[str], tool: Tool, input_data: Dict = None) -> List[str]:
        """Run Httpx and return live URLs"""
        try:
            stage_start = datetime.utcnow()
            # Prepare targets: use subdomains if available, otherwise use original target
            targets = subdomains[:50] if subdomains else [target.url]
            # Ensure all targets are full URLs
            from urllib.parse import urlparse
            formatted_targets = []
            for t in targets:
                parsed = urlparse(t)
                if not parsed.scheme:
                    # Add http:// if no scheme
                    formatted_targets.append(f"http://{t}")
                else:
                    formatted_targets.append(t)
            
            result = self.tools['httpx'].run(targets=formatted_targets)
            execution_time = int((datetime.utcnow() - stage_start).total_seconds())
            
            # Store tool execution
            self._store_tool_execution(
                job, tool, 2, "Stage 2: HTTP Service Detection",
                input_data or {"subdomains": subdomains, "targets": formatted_targets}, result, execution_time
            )
            
            live_urls = []
            for item in result.get("results", []):
                url = item.get("url") or item.get("input", "")
                status_code = item.get("status_code", 0)
                if status_code in [200, 201, 301, 302, 401, 403]:
                    live_urls.append(url)
                    
                    vuln_def = self._get_or_create_vulnerability(
                        "HTTP Service Detected",
                        "Active HTTP service discovered"
                    )
                    self._create_finding(
                        job, target, tool, vuln_def,
                        FindingSeverity.INFO,
                        location=url,
                        evidence=f"HTTP {status_code} - {item.get('title', 'N/A')}"
                    )
            
            return live_urls if live_urls else [target.url]
        except Exception as e:
            logger.error(f"Stage 2 (Httpx) failed: {e}", exc_info=True)
            try:
                self._store_tool_execution(
                    job, tool, 2, "Stage 2: HTTP Service Detection",
                    input_data or {"subdomains": subdomains}, 
                    {"status": "failed", "error": str(e)}, 0
                )
            except:
                pass
            # Return original target URL to continue scan
            return [target.url]
    
    def _run_gobuster(self, job: ScanJob, target: Target, url: str, tool: Tool, input_data: Dict = None):
        """Run Gobuster directory discovery"""
        try:
            stage_start = datetime.utcnow()
            result = self.tools['gobuster'].run(target_url=url)
            execution_time = int((datetime.utcnow() - stage_start).total_seconds())
            
            # Store tool execution
            self._store_tool_execution(
                job, tool, 3, "Stage 3: Directory Discovery",
                input_data or {"target_url": url}, result, execution_time
            )
            
            for item in result.get("results", [])[:20]:  # Limit to first 20
                vuln_def = self._get_or_create_vulnerability(
                    "Directory/File Discovery",
                    "Hidden directory or file discovered"
                )
                self._create_finding(
                    job, target, tool, vuln_def,
                    FindingSeverity.LOW,
                    location=item,
                    evidence=f"Discovered: {item}"
                )
        except Exception as e:
            logger.error(f"Stage 3 (Gobuster) failed: {e}", exc_info=True)
            try:
                self._store_tool_execution(
                    job, tool, 3, "Stage 3: Directory Discovery",
                    input_data or {"target_url": url}, 
                    {"status": "failed", "error": str(e)}, 0
                )
            except:
                pass
    
    def _run_zap(self, job: ScanJob, target: Target, url: str, tool: Tool, input_data: Dict = None):
        """Run OWASP ZAP"""
        try:
            from urllib.parse import urlparse
            stage_start = datetime.utcnow()
            parsed = urlparse(url)
            is_localhost = parsed.hostname in ('localhost', '127.0.0.1')
            result = self.tools['zap'].run(target_url=url, is_localhost=is_localhost)
            execution_time = int((datetime.utcnow() - stage_start).total_seconds())
            
            # Store tool execution
            self._store_tool_execution(
                job, tool, 4, "Stage 4: Web Application Scanning",
                input_data or {"target_url": url}, result, execution_time
            )
            
            severity_map = {
                'High': FindingSeverity.HIGH,
                'Medium': FindingSeverity.MEDIUM,
                'Low': FindingSeverity.LOW,
                'Informational': FindingSeverity.INFO
            }
            
            for alert in result.get("alerts", []):
                name = alert.get("name", "Security Issue")
                severity_str = alert.get("risk", "Low")
                severity = severity_map.get(severity_str, FindingSeverity.LOW)
                
                vuln_def = self._get_or_create_vulnerability(
                    name,
                    alert.get("description", ""),
                    alert.get("solution", "")
                )
                
                self._create_finding(
                    job, target, tool, vuln_def,
                    severity,
                    location=url,
                    evidence=alert.get("evidence", ""),
                    confidence="high" if severity_str == "High" else "medium"
                )
            
            return result
        except Exception as e:
            logger.error(f"Stage 4 (ZAP) failed: {e}", exc_info=True)
            try:
                self._store_tool_execution(
                    job, tool, 4, "Stage 4: Web Application Scanning",
                    input_data or {"target_url": url}, 
                    {"status": "failed", "error": str(e)}, 0
                )
            except:
                pass
            return {"status": "failed", "error": str(e), "alerts": []}
    
    def _run_nuclei(self, job: ScanJob, target: Target, url: str, tool: Tool, input_data: Dict = None):
        """Run Nuclei template scanning"""
        try:
            stage_start = datetime.utcnow()
            result = self.tools['nuclei'].run(target_url=url)
            execution_time = int((datetime.utcnow() - stage_start).total_seconds())
            
            # Store tool execution
            self._store_tool_execution(
                job, tool, 5, "Stage 5: Template-Based Scanning",
                input_data or {"target_url": url}, result, execution_time
            )
            
            severity_map = {
                'critical': FindingSeverity.CRITICAL,
                'high': FindingSeverity.HIGH,
                'medium': FindingSeverity.MEDIUM,
                'low': FindingSeverity.LOW,
                'info': FindingSeverity.INFO
            }
            
            for finding in result.get("findings", []):
                name = finding.get("info", {}).get("name", "Vulnerability")
                severity_str = finding.get("info", {}).get("severity", "low").lower()
                severity = severity_map.get(severity_str, FindingSeverity.LOW)
                
                vuln_def = self._get_or_create_vulnerability(
                    name,
                    finding.get("info", {}).get("description", ""),
                    finding.get("info", {}).get("remediation", "")
                )
                
                self._create_finding(
                    job, target, tool, vuln_def,
                    severity,
                    location=finding.get("matched-at", url),
                    evidence=finding.get("curl-command", ""),
                    confidence="high"
                )
        except Exception as e:
            logger.error(f"Stage 5 (Nuclei) failed: {e}", exc_info=True)
            try:
                self._store_tool_execution(
                    job, tool, 5, "Stage 5: Template-Based Scanning",
                    input_data or {"target_url": url}, 
                    {"status": "failed", "error": str(e)}, 0
                )
            except:
                pass
    
    def _run_sqlmap(self, job: ScanJob, target: Target, url: str, tool: Tool, input_data: Dict = None):
        """Run SQLMap"""
        try:
            stage_start = datetime.utcnow()
            result = self.tools['sqlmap'].run(target_url=url)
            execution_time = int((datetime.utcnow() - stage_start).total_seconds())
            
            # Store tool execution
            self._store_tool_execution(
                job, tool, 6, "Stage 6: SQL Injection Testing",
                input_data or {"target_url": url}, result, execution_time
            )
            
            if result.get("vulnerable"):
                vuln_def = self._get_or_create_vulnerability(
                    "SQL Injection",
                    "SQL injection vulnerability detected",
                    "Sanitize all user inputs and use parameterized queries"
                )
                
                self._create_finding(
                    job, target, tool, vuln_def,
                    FindingSeverity.CRITICAL,
                    location=url,
                    evidence=result.get("raw_output", ""),
                    confidence="high"
                )
        except Exception as e:
            logger.error(f"Stage 6 (SQLMap) failed: {e}", exc_info=True)
            try:
                self._store_tool_execution(
                    job, tool, 6, "Stage 6: SQL Injection Testing",
                    input_data or {"target_url": url}, 
                    {"status": "failed", "error": str(e)}, 0
                )
            except:
                pass
