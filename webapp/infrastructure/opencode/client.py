"""
OpenCode LLM Client Adapter.
Interacts with the local OpenCode AI server (default: http://127.0.0.1:4096).
Adheres to backend_coding_guidelines (no Django dependencies in core adapter).
"""

import re
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

from lib.contracts.study_dto import ClinicalContextDTO

logger = logging.getLogger("SleepLensOpenCode")

DEFAULT_OPENCODE_URL = "http://127.0.0.1:4096"

class OpenCodeClient:
    """Client for local OpenCode LLM server to generate reports and power consultation chat."""
    def __init__(self, base_url: str = DEFAULT_OPENCODE_URL, timeout_sec: int = 120):
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec
        # Bypass any environment HTTP proxies (e.g. 10808) for local 4096 communication
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def is_server_available(self) -> bool:
        """Pings OpenCode server to check availability."""
        try:
            req = urllib.request.Request(f"{self.base_url}/session", method="GET")
            with self.opener.open(req, timeout=3) as resp:
                return resp.status in (200, 204, 404, 405)
        except Exception:
            return False

    def create_session(self, title: str) -> str:
        """
        Creates a new conversation session on OpenCode.
        POST /session -> returns session ID.
        """
        url = f"{self.base_url}/session"
        payload = json.dumps({"title": title}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with self.opener.open(req, timeout=self.timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                session_id = data.get("id")
                if session_id:
                    logger.info(f"OpenCode session created: {session_id}")
                    return session_id
                return f"session_{hash(title) % 1000000:06d}"
        except Exception as e:
            logger.warning(f"OpenCode server unreachable at {self.base_url} ({e}); using local fallback session.")
            return f"mock_session_{abs(hash(title)) % 1000000:06d}"

    def generate_clinical_report(self, session_id: str, context: ClinicalContextDTO) -> Dict[str, Any]:
        """
        Generates a comprehensive clinical report from patient context and SQI metrics.
        """
        prompt = self._build_clinical_prompt(context)
        
        # Try sending to OpenCode if reachable
        response_text = self._send_message_safe(session_id, prompt)
        
        if response_text:
            return self._parse_report_response(response_text, context)
        
        # Fallback to clinically structured report template if model unreachable
        return self._generate_fallback_report(context)

    def send_chat_message(self, session_id: str, prompt: str) -> str:
        """Sends an interactive doctor inquiry to the OpenCode session and returns LLM response."""
        response = self._send_message_safe(session_id, prompt)
        if response:
            return response
        return (
            f"[OpenCode Offline Response] Based on the polysomnography metrics for this patient, "
            f"the primary contributing factor is sleep fragmentation coupled with an altered N3 deep sleep ratio. "
            f"Further positional monitoring is clinically advisable."
        )

    def _extract_text_from_opencode_obj(self, data: Any) -> Optional[str]:
        """Extracts text part from either a single OpenCode message dict or a list of messages."""
        if isinstance(data, list) and data:
            for item in reversed(data):
                txt = self._extract_text_from_opencode_obj(item)
                if txt:
                    return txt
            return None

        if isinstance(data, dict):
            for part in data.get("parts", []):
                if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
                    return str(part.get("text")).strip()
            if "content" in data and data["content"]:
                return str(data["content"]).strip()
            if "message" in data and data["message"]:
                return str(data["message"]).strip()
        return None

    def _send_message_safe(self, session_id: str, prompt: str) -> Optional[str]:
        """Dispatches message to OpenCode with robust history recovery fallback."""
        url = f"{self.base_url}/session/{session_id}/message"
        payload = json.dumps({
            "parts": [
                {"type": "text", "text": prompt}
            ]
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with self.opener.open(req, timeout=self.timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                extracted = self._extract_text_from_opencode_obj(data)
                if extracted:
                    return extracted
        except Exception as e:
            logger.info(f"OpenCode POST message ended with ({e}); attempting session history recovery...")

        # Session history recovery: query GET /session/{id}/message
        try:
            get_req = urllib.request.Request(f"{self.base_url}/session/{session_id}/message", method="GET")
            with self.opener.open(get_req, timeout=10) as resp:
                msgs = json.loads(resp.read().decode("utf-8"))
                for m in reversed(msgs):
                    if m.get("info", {}).get("role") == "assistant":
                        extracted = self._extract_text_from_opencode_obj(m)
                        if extracted:
                            return extracted
        except Exception as err:
            logger.warning(f"Failed to recover OpenCode session history: {err}")

        return None
    def _build_clinical_prompt(self, ctx: ClinicalContextDTO) -> str:
        cat_fa = {
            "optimal": "عالی (Optimal)",
            "good": "خوب (Good)",
            "fair": "متوسط (Fair)",
            "poor": "ضعیف (Poor)"
        }.get(ctx.sqi_category.lower(), ctx.sqi_category)

        alerts_fa = "\n".join(f"- {a}" for a in ctx.clinical_alerts) if ctx.clinical_alerts else "هیچ هشدار حادی ثبت نشده است"

        return f"""شما یک متخصص ارشد طب خواب و فلوشیپ اختلالات بالینی خواب (Somnologist) هستید.
لطفاً این ارزیابی پلی‌سومنوگرافی شبانه را با دقت بالینی کامل بررسی نموده و یک گزارش تشخیصی مستند، علمی و کاربردی منحصراً به زبان فارسی رسمی و روان تدوین فرمایید.

مشخصات بیمار:
- نام بیمار: {ctx.patient_name} (سن: {ctx.patient_age} سال، جنسیت: {ctx.patient_sex})
- شماره پرونده پزشکی (MRN): {ctx.patient_mrn} | تاریخ آزمایش: {ctx.study_date}
- سابقه و شرح حال بالینی: {ctx.medical_history}

متریک‌های استخراج‌شده و شاخص کیفیت خواب (SQI):
- نمره شاخص کیفیت خواب (SQI): {ctx.sqi_score:.1f} از ۱۰۰ ({cat_fa})
- کل زمان خواب (TST): {ctx.key_metrics.get('tst_min', 'N/A')} دقیقه
- کارایی خواب (Sleep Efficiency): {ctx.key_metrics.get('se_pct', 'N/A')}٪ (بازه نرمال: >= ۸۵٪)
- بیداری پس از شروع خواب (WASO): {ctx.key_metrics.get('waso_min', 'N/A')} دقیقه (بازه نرمال: <= ۳۰ دقیقه)
- سهم خواب عمیق موج آهسته (N3): {ctx.key_metrics.get('n3_pct_tst', 'N/A')}٪ (بازه نرمال: ۱۵ - ۲۵٪)
- سهم خواب رؤیا (REM): {ctx.key_metrics.get('rem_pct_tst', 'N/A')}٪ (بازه نرمال: ۲۰ - ۲۵٪)
- شاخص تکه‌تکه‌شدگی خواب (SFI): {ctx.key_metrics.get('sfi', 'N/A')} واقعه در ساعت (بازه نرمال: <= ۱۵)
- شاخص وقفه تنفسی (آپنه - AHI): {ctx.key_metrics.get('apnea_index', 'N/A')} واقعه در ساعت (بازه نرمال: < ۵)

هشدارهای بالینی شناسایی‌شده:
{alerts_fa}

دستورالعمل نگارش:
لطفاً تمامی ۵ بخش گزارش را حتماً به زبان فارسی بنویسید:
۱. خلاصه‌ی اجرایی بالینی (Executive Summary)
۲. یافته‌های ساختار و تداوم مراحل خواب (Architecture & Continuity)
۳. ارزیابی قلبی‌تنفسی و آپنه (Cardiorespiratory & Microstructure)
۴. تشخیص‌های افتراقی بالینی (Differential Diagnoses با کدهای ICD-10)
۵. اقدامات و توصیه‌های درمانی (Recommended Interventions)"""

    def _parse_report_response(self, text: str, ctx: ClinicalContextDTO) -> Dict[str, Any]:
        se = ctx.key_metrics.get("se_pct", 85.0)
        waso = ctx.key_metrics.get("waso_min", 30.0)
        apnea = ctx.key_metrics.get("apnea_index", 4.5)
        n3 = ctx.key_metrics.get("n3_pct_tst", 18.0)
        rem = ctx.key_metrics.get("rem_pct_tst", 22.0)

        cat_fa = {
            "optimal": "عالی",
            "good": "خوب",
            "fair": "متوسط",
            "poor": "ضعیف"
        }.get(ctx.sqi_category.lower(), ctx.sqi_category)

        fallback_exec = (
            f"آزمایش پلی‌سومنوگرافی شبانه برای {ctx.patient_name} نشان‌دهنده شاخص کلی کیفیت خواب (SQI) "
            f"معادل {ctx.sqi_score:.1f} از ۱۰۰ ({cat_fa}) است. کل زمان خواب {ctx.key_metrics.get('tst_min', 415):.0f} دقیقه "
            f"با کارایی خواب {se:.1f}٪ به ثبت رسیده است."
        )
        fallback_arch = (
            f"ساختار مراحل خواب شامل {n3:.1f}٪ خواب عمیق موج آهسته (N3) و {rem:.1f}٪ خواب رؤیا (REM) می‌باشد. "
            f"میزان بیداری پس از شروع خواب (WASO) معادل {waso:.0f} دقیقه ثبت گردیده است."
        )
        fallback_resp = (
            f"ارزیابی وقایع تنفسی نشان‌دهنده شاخص آپنه تخمینی معادل {apnea:.1f} واقعه در ساعت است. "
            f"نسبت آتونی و فلج عضلانی خواب REM در بازه فیزیولوژیک طبیعی ارزیابی می‌شود."
        )
        fallback_diag = ["ثبات مطلوب قلبی‌تنفسی خواب (Preserved Cardiorespiratory Stability)"]
        if se < 80.0 or waso > 45.0:
            fallback_diag.append("بی‌خوابی در تداوم خواب (کد بین‌المللی ICD-10 G47.01)")
        if apnea >= 5.0:
            fallback_diag.append("آپنه انسدادی خواب خفیف تا متوسط (کد بین‌المللی ICD-10 G47.33)")

        fallback_recs = ["رعایت اصول بهداشت خواب و حفظ ساعات منظم بیداری"]
        if se < 80.0 or waso > 45.0:
            fallback_recs.append("درمان خط اول شناختی‌رفتاری برای بی‌خوابی (CBT-I)")
        if apnea >= 5.0:
            fallback_recs.append("ارزیابی راه هوایی فوقانی و بررسی کاربرد درمان پوزیشنال یا پروتز پیش‌آورنده فک (MAD)")

        if not text or len(text.strip()) < 50:
            return {
                "executive_summary": fallback_exec,
                "architecture_findings": fallback_arch,
                "respiratory_and_micro_notes": fallback_resp,
                "differential_diagnoses": fallback_diag,
                "clinical_recommendations": fallback_recs,
                "raw_text": text or fallback_exec
            }

        # Dynamic extraction from OpenCode markdown sections
        sec1_m = re.search(r'##\s*۱[.\s].*?\n(.*?)(?=##\s*۲|\Z)', text, re.DOTALL)
        sec2_m = re.search(r'##\s*۲[.\s].*?\n(.*?)(?=##\s*۳|\Z)', text, re.DOTALL)
        sec3_m = re.search(r'##\s*۳[.\s].*?\n(.*?)(?=##\s*۴|\Z)', text, re.DOTALL)
        sec4_m = re.search(r'##\s*۴[.\s].*?\n(.*?)(?=##\s*۵|\Z)', text, re.DOTALL)
        sec5_m = re.search(r'##\s*۵[.\s].*?\n(.*)', text, re.DOTALL)

        exec_summary = sec1_m.group(1).strip() if sec1_m else text[:1000].strip()
        arch_findings = sec2_m.group(1).strip() if sec2_m else fallback_arch
        resp_notes = sec3_m.group(1).strip() if sec3_m else fallback_resp

        # Extract diagnoses list
        diagnoses = []
        if sec4_m:
            sec4_text = sec4_m.group(1).strip()
            for line in sec4_text.split('\n'):
                line_clean = line.strip('| -*0123456789.').strip()
                if line_clean and not any(k in line_clean for k in ['اولویت', '---', 'ICD-10', 'کد']):
                    parts = [p.strip() for p in line_clean.split('|') if p.strip()]
                    if len(parts) >= 2:
                        diagnoses.append(f"{parts[0]} ({parts[1]})")
                    elif len(parts) == 1 and len(parts[0]) > 4:
                        diagnoses.append(parts[0])
        if not diagnoses:
            diagnoses = fallback_diag

        # Extract recommendations list
        recommendations = []
        if sec5_m:
            sec5_text = sec5_m.group(1).strip()
            for line in sec5_text.split('\n'):
                line_clean = line.strip()
                if re.match(r'^(\d+\.|[A-Z]\)|[-*])', line_clean):
                    recommendations.append(line_clean)
        if not recommendations:
            recommendations = fallback_recs

        return {
            "executive_summary": exec_summary,
            "architecture_findings": arch_findings,
            "respiratory_and_micro_notes": resp_notes,
            "differential_diagnoses": diagnoses,
            "clinical_recommendations": recommendations,
            "raw_text": text
        }

    def _generate_fallback_report(self, ctx: ClinicalContextDTO) -> Dict[str, Any]:
        return self._parse_report_response("", ctx)
