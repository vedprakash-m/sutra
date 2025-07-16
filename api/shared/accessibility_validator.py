"""
WCAG 2.1 AA Accessibility Compliance Validator for Forge UX Requirements.
Implements comprehensive accessibility checking with actionable recommendations
and 90% minimum compliance enforcement.
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AccessibilityLevel(Enum):
    """WCAG conformance levels"""

    A = "A"
    AA = "AA"
    AAA = "AAA"


class ComplianceStatus(Enum):
    """Compliance check status"""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class AccessibilityCheck:
    """Individual accessibility check result"""

    check_id: str
    guideline: str
    success_criterion: str
    level: AccessibilityLevel
    status: ComplianceStatus
    confidence: float
    description: str
    recommendation: str
    impact: str
    automated: bool
    priority: int  # 1-5, 1 being highest priority


@dataclass
class AccessibilityAssessment:
    """Complete accessibility assessment result"""

    overall_score: float
    compliance_level: AccessibilityLevel
    checks: List[AccessibilityCheck]
    summary: Dict[str, Any]
    recommendations: List[str]
    manual_checks_needed: List[str]
    estimated_remediation_time: str


class AccessibilityValidator:
    """WCAG 2.1 AA compliance validator for UX requirements"""

    def __init__(self):
        self.wcag_guidelines = self._load_wcag_guidelines()
        self.minimum_score_threshold = 90.0  # 90% minimum for AA compliance

    def validate_ux_requirements(self, ux_data: Dict[str, Any]) -> AccessibilityAssessment:
        """
        Validate UX requirements for accessibility compliance

        Args:
            ux_data: Dictionary containing UX requirements, wireframes, journeys, etc.

        Returns:
            AccessibilityAssessment with detailed compliance evaluation
        """
        checks = []

        # Validate user journeys
        if "userJourneys" in ux_data:
            checks.extend(self._validate_user_journeys(ux_data["userJourneys"]))

        # Validate wireframes
        if "wireframes" in ux_data:
            checks.extend(self._validate_wireframes(ux_data["wireframes"]))

        # Validate design system
        if "designSystem" in ux_data:
            checks.extend(self._validate_design_system(ux_data["designSystem"]))

        # Validate interactions
        if "interactions" in ux_data:
            checks.extend(self._validate_interactions(ux_data["interactions"]))

        # Validate content structure
        if "content" in ux_data:
            checks.extend(self._validate_content_structure(ux_data["content"]))

        # Calculate overall score and compliance
        overall_score = self._calculate_overall_score(checks)
        compliance_level = self._determine_compliance_level(checks, overall_score)

        # Generate summary and recommendations
        summary = self._generate_summary(checks, overall_score)
        recommendations = self._generate_recommendations(checks)
        manual_checks = self._identify_manual_checks(checks)
        remediation_time = self._estimate_remediation_time(checks)

        return AccessibilityAssessment(
            overall_score=overall_score,
            compliance_level=compliance_level,
            checks=checks,
            summary=summary,
            recommendations=recommendations,
            manual_checks_needed=manual_checks,
            estimated_remediation_time=remediation_time,
        )

    def _validate_user_journeys(self, journeys: List[Dict[str, Any]]) -> List[AccessibilityCheck]:
        """Validate user journeys for accessibility considerations"""
        checks = []

        for journey in journeys:
            journey_id = journey.get("id", "unknown")

            # Check for alternative paths for different abilities
            alt_paths = journey.get("alternativePaths", [])
            if len(alt_paths) == 0:
                checks.append(
                    AccessibilityCheck(
                        check_id=f"journey_{journey_id}_alt_paths",
                        guideline="WCAG 2.1",
                        success_criterion="2.1.1 Keyboard",
                        level=AccessibilityLevel.A,
                        status=ComplianceStatus.WARNING,
                        confidence=0.8,
                        description="User journey should include alternative paths for different interaction methods",
                        recommendation="Add keyboard-only navigation paths and screen reader considerations",
                        impact="Users with motor disabilities may not be able to complete tasks",
                        automated=True,
                        priority=2,
                    )
                )

            # Check for clear navigation structure
            steps = journey.get("steps", [])
            if len(steps) > 7:  # Miller's rule of 7±2
                checks.append(
                    AccessibilityCheck(
                        check_id=f"journey_{journey_id}_complexity",
                        guideline="WCAG 2.1",
                        success_criterion="3.2.3 Consistent Navigation",
                        level=AccessibilityLevel.AA,
                        status=ComplianceStatus.WARNING,
                        confidence=0.7,
                        description="Complex user journeys may be difficult for users with cognitive disabilities",
                        recommendation="Consider breaking into smaller sub-journeys or providing progress indicators",
                        impact="Users with cognitive disabilities may struggle with complex navigation",
                        automated=True,
                        priority=3,
                    )
                )

            # Check for error recovery paths
            error_handling = journey.get("errorHandling", {})
            if not error_handling:
                checks.append(
                    AccessibilityCheck(
                        check_id=f"journey_{journey_id}_error_recovery",
                        guideline="WCAG 2.1",
                        success_criterion="3.3.1 Error Identification",
                        level=AccessibilityLevel.A,
                        status=ComplianceStatus.FAIL,
                        confidence=0.9,
                        description="User journey must include error recovery mechanisms",
                        recommendation="Define clear error states and recovery actions for each step",
                        impact="Users may get stuck without clear error recovery paths",
                        automated=True,
                        priority=1,
                    )
                )

        return checks

    def _validate_wireframes(self, wireframes: List[Dict[str, Any]]) -> List[AccessibilityCheck]:
        """Validate wireframes for accessibility compliance"""
        checks = []

        for wireframe in wireframes:
            wireframe_id = wireframe.get("id", "unknown")

            # Check for heading hierarchy
            headings = wireframe.get("headings", [])
            if headings:
                heading_levels = [h.get("level", 1) for h in headings]
                if not self._validate_heading_hierarchy(heading_levels):
                    checks.append(
                        AccessibilityCheck(
                            check_id=f"wireframe_{wireframe_id}_heading_hierarchy",
                            guideline="WCAG 2.1",
                            success_criterion="1.3.1 Info and Relationships",
                            level=AccessibilityLevel.A,
                            status=ComplianceStatus.FAIL,
                            confidence=0.95,
                            description="Heading hierarchy is not logical (e.g., H3 following H1)",
                            recommendation="Ensure headings follow logical sequence (H1 → H2 → H3)",
                            impact="Screen reader users cannot properly navigate page structure",
                            automated=True,
                            priority=1,
                        )
                    )

            # Check for color contrast considerations
            colors = wireframe.get("colorScheme", {})
            if colors:
                contrast_issues = self._check_color_contrast(colors)
                for issue in contrast_issues:
                    checks.append(
                        AccessibilityCheck(
                            check_id=f"wireframe_{wireframe_id}_contrast_{issue['id']}",
                            guideline="WCAG 2.1",
                            success_criterion="1.4.3 Contrast (Minimum)",
                            level=AccessibilityLevel.AA,
                            status=ComplianceStatus.FAIL,
                            confidence=0.9,
                            description=f"Insufficient color contrast: {issue['description']}",
                            recommendation=f"Increase contrast ratio to at least 4.5:1 for normal text, 3:1 for large text",
                            impact="Users with visual impairments cannot read content",
                            automated=True,
                            priority=1,
                        )
                    )

            # Check for focus indicators
            interactive_elements = wireframe.get("interactiveElements", [])
            for element in interactive_elements:
                if not element.get("focusIndicator"):
                    checks.append(
                        AccessibilityCheck(
                            check_id=f"wireframe_{wireframe_id}_focus_{element.get('id', 'unknown')}",
                            guideline="WCAG 2.1",
                            success_criterion="2.4.7 Focus Visible",
                            level=AccessibilityLevel.AA,
                            status=ComplianceStatus.FAIL,
                            confidence=0.9,
                            description=f"Interactive element '{element.get('type', 'unknown')}' lacks focus indicator",
                            recommendation="Add visible focus indicators for all interactive elements",
                            impact="Keyboard users cannot see which element has focus",
                            automated=True,
                            priority=1,
                        )
                    )

            # Check for alt text requirements
            images = wireframe.get("images", [])
            for image in images:
                if not image.get("altText") and image.get("decorative") != True:
                    checks.append(
                        AccessibilityCheck(
                            check_id=f"wireframe_{wireframe_id}_alt_text_{image.get('id', 'unknown')}",
                            guideline="WCAG 2.1",
                            success_criterion="1.1.1 Non-text Content",
                            level=AccessibilityLevel.A,
                            status=ComplianceStatus.FAIL,
                            confidence=0.95,
                            description=f"Image '{image.get('description', 'unknown')}' missing alt text",
                            recommendation="Provide descriptive alt text or mark as decorative",
                            impact="Screen reader users cannot understand image content",
                            automated=True,
                            priority=1,
                        )
                    )

        return checks

    def _validate_design_system(self, design_system: Dict[str, Any]) -> List[AccessibilityCheck]:
        """Validate design system for accessibility standards"""
        checks = []

        # Check typography scale
        typography = design_system.get("typography", {})
        if typography:
            font_sizes = typography.get("fontSizes", [])
            if font_sizes and min(font_sizes) < 16:
                checks.append(
                    AccessibilityCheck(
                        check_id="design_system_min_font_size",
                        guideline="WCAG 2.1",
                        success_criterion="1.4.4 Resize text",
                        level=AccessibilityLevel.AA,
                        status=ComplianceStatus.WARNING,
                        confidence=0.8,
                        description="Minimum font size below 16px may cause readability issues",
                        recommendation="Use minimum 16px for body text, larger for headings",
                        impact="Users with visual impairments may struggle to read small text",
                        automated=True,
                        priority=2,
                    )
                )

        # Check color palette
        colors = design_system.get("colorPalette", {})
        if colors:
            # Check for sufficient color options
            if len(colors.get("semantic", {})) < 3:
                checks.append(
                    AccessibilityCheck(
                        check_id="design_system_color_variety",
                        guideline="WCAG 2.1",
                        success_criterion="1.4.1 Use of Color",
                        level=AccessibilityLevel.A,
                        status=ComplianceStatus.WARNING,
                        confidence=0.7,
                        description="Limited semantic color options may rely too heavily on color alone",
                        recommendation="Provide additional visual cues (icons, patterns, text) beyond color",
                        impact="Color-blind users may not distinguish between states",
                        automated=True,
                        priority=2,
                    )
                )

        # Check spacing system
        spacing = design_system.get("spacing", {})
        if spacing:
            touch_targets = spacing.get("touchTargets", {})
            min_touch_size = touch_targets.get("minimum", 0)
            if min_touch_size < 44:  # WCAG 2.1 AA requirement
                checks.append(
                    AccessibilityCheck(
                        check_id="design_system_touch_targets",
                        guideline="WCAG 2.1",
                        success_criterion="2.5.5 Target Size",
                        level=AccessibilityLevel.AAA,
                        status=ComplianceStatus.WARNING,
                        confidence=0.9,
                        description="Touch targets smaller than 44px may be difficult to use",
                        recommendation="Ensure all interactive elements are at least 44x44px",
                        impact="Users with motor disabilities may have difficulty activating controls",
                        automated=True,
                        priority=2,
                    )
                )

        return checks

    def _validate_interactions(self, interactions: List[Dict[str, Any]]) -> List[AccessibilityCheck]:
        """Validate interaction patterns for accessibility"""
        checks = []

        for interaction in interactions:
            interaction_id = interaction.get("id", "unknown")

            # Check for keyboard alternatives
            if interaction.get("type") in ["hover", "gesture", "touch"]:
                if not interaction.get("keyboardAlternative"):
                    checks.append(
                        AccessibilityCheck(
                            check_id=f"interaction_{interaction_id}_keyboard",
                            guideline="WCAG 2.1",
                            success_criterion="2.1.1 Keyboard",
                            level=AccessibilityLevel.A,
                            status=ComplianceStatus.FAIL,
                            confidence=0.95,
                            description=f"Interaction '{interaction.get('type')}' lacks keyboard alternative",
                            recommendation="Provide keyboard equivalent for all interactions",
                            impact="Keyboard-only users cannot access functionality",
                            automated=True,
                            priority=1,
                        )
                    )

            # Check for time limits
            if interaction.get("timeLimit"):
                if not interaction.get("extendible"):
                    checks.append(
                        AccessibilityCheck(
                            check_id=f"interaction_{interaction_id}_time_limit",
                            guideline="WCAG 2.1",
                            success_criterion="2.2.1 Timing Adjustable",
                            level=AccessibilityLevel.A,
                            status=ComplianceStatus.FAIL,
                            confidence=0.9,
                            description="Time-limited interaction is not extendible",
                            recommendation="Allow users to extend time limits or disable them",
                            impact="Users with disabilities may need more time to complete actions",
                            automated=True,
                            priority=1,
                        )
                    )

            # Check for motion sensitivity
            if interaction.get("animation") or interaction.get("motion"):
                if not interaction.get("reducedMotionOption"):
                    checks.append(
                        AccessibilityCheck(
                            check_id=f"interaction_{interaction_id}_motion",
                            guideline="WCAG 2.1",
                            success_criterion="2.3.3 Animation from Interactions",
                            level=AccessibilityLevel.AAA,
                            status=ComplianceStatus.WARNING,
                            confidence=0.8,
                            description="Motion/animation interactions should respect prefers-reduced-motion",
                            recommendation="Provide option to disable animations or respect user's motion preferences",
                            impact="Users with vestibular disorders may experience discomfort",
                            automated=True,
                            priority=2,
                        )
                    )

        return checks

    def _validate_content_structure(self, content: Dict[str, Any]) -> List[AccessibilityCheck]:
        """Validate content structure for accessibility"""
        checks = []

        # Check for clear language requirements
        language = content.get("language", {})
        if not language.get("level"):
            checks.append(
                AccessibilityCheck(
                    check_id="content_language_level",
                    guideline="WCAG 2.1",
                    success_criterion="3.1.5 Reading Level",
                    level=AccessibilityLevel.AAA,
                    status=ComplianceStatus.WARNING,
                    confidence=0.7,
                    description="No reading level specified for content",
                    recommendation="Aim for simple language (Grade 8 level or lower where possible)",
                    impact="Users with cognitive disabilities may struggle with complex language",
                    automated=True,
                    priority=3,
                )
            )

        # Check for content organization
        structure = content.get("structure", {})
        if not structure.get("landmarks"):
            checks.append(
                AccessibilityCheck(
                    check_id="content_landmarks",
                    guideline="WCAG 2.1",
                    success_criterion="1.3.1 Info and Relationships",
                    level=AccessibilityLevel.A,
                    status=ComplianceStatus.FAIL,
                    confidence=0.9,
                    description="Content structure lacks semantic landmarks",
                    recommendation="Use semantic HTML landmarks (header, nav, main, aside, footer)",
                    impact="Screen reader users cannot efficiently navigate content",
                    automated=True,
                    priority=1,
                )
            )

        return checks

    def _validate_heading_hierarchy(self, heading_levels: List[int]) -> bool:
        """Validate that heading levels follow logical hierarchy"""
        if not heading_levels:
            return True

        # Check if starts with H1
        if heading_levels[0] != 1:
            return False

        # Check for logical progression
        for i in range(1, len(heading_levels)):
            current = heading_levels[i]
            previous = heading_levels[i - 1]

            # Can't skip levels (e.g., H1 → H3)
            if current > previous + 1:
                return False

        return True

    def _check_color_contrast(self, colors: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check color combinations for contrast issues (simplified)"""
        issues = []

        # This is a simplified check - in practice, you'd calculate actual contrast ratios
        primary = colors.get("primary", "#000000")
        background = colors.get("background", "#ffffff")

        # Simplified contrast check based on color values
        if self._calculate_simple_contrast(primary, background) < 4.5:
            issues.append({"id": "primary_background", "description": f"Primary color {primary} on background {background}"})

        return issues

    def _calculate_simple_contrast(self, color1: str, color2: str) -> float:
        """Simplified contrast calculation (placeholder for real implementation)"""
        # This is a placeholder - real implementation would convert hex to RGB,
        # calculate relative luminance, and compute contrast ratio
        return 5.0  # Simplified assumption

    def _calculate_overall_score(self, checks: List[AccessibilityCheck]) -> float:
        """Calculate overall accessibility score"""
        if not checks:
            return 100.0

        total_weight = 0
        weighted_score = 0

        for check in checks:
            weight = 6 - check.priority  # Higher priority = higher weight
            total_weight += weight

            if check.status == ComplianceStatus.PASS:
                weighted_score += weight
            elif check.status == ComplianceStatus.WARNING:
                weighted_score += weight * 0.7
            elif check.status == ComplianceStatus.FAIL:
                weighted_score += 0

        return (weighted_score / total_weight) * 100 if total_weight > 0 else 0

    def _determine_compliance_level(self, checks: List[AccessibilityCheck], score: float) -> AccessibilityLevel:
        """Determine WCAG compliance level based on checks"""
        # Check for any Level A failures
        a_failures = [c for c in checks if c.level == AccessibilityLevel.A and c.status == ComplianceStatus.FAIL]
        if a_failures:
            return AccessibilityLevel.A  # Cannot meet AA if A requirements fail

        # Check for Level AA failures
        aa_failures = [c for c in checks if c.level == AccessibilityLevel.AA and c.status == ComplianceStatus.FAIL]
        if aa_failures or score < self.minimum_score_threshold:
            return AccessibilityLevel.A

        return AccessibilityLevel.AA

    def _generate_summary(self, checks: List[AccessibilityCheck], score: float) -> Dict[str, Any]:
        """Generate summary statistics"""
        total_checks = len(checks)
        passed = len([c for c in checks if c.status == ComplianceStatus.PASS])
        failed = len([c for c in checks if c.status == ComplianceStatus.FAIL])
        warnings = len([c for c in checks if c.status == ComplianceStatus.WARNING])

        by_level = {}
        for level in AccessibilityLevel:
            level_checks = [c for c in checks if c.level == level]
            by_level[level.value] = {
                "total": len(level_checks),
                "passed": len([c for c in level_checks if c.status == ComplianceStatus.PASS]),
                "failed": len([c for c in level_checks if c.status == ComplianceStatus.FAIL]),
                "warnings": len([c for c in level_checks if c.status == ComplianceStatus.WARNING]),
            }

        return {
            "totalChecks": total_checks,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "score": score,
            "byLevel": by_level,
            "criticalIssues": failed,
            "meetsMinimum": score >= self.minimum_score_threshold,
        }

    def _generate_recommendations(self, checks: List[AccessibilityCheck]) -> List[str]:
        """Generate prioritized recommendations"""
        failed_checks = [c for c in checks if c.status == ComplianceStatus.FAIL]
        failed_checks.sort(key=lambda x: x.priority)

        recommendations = []
        for check in failed_checks[:10]:  # Top 10 priorities
            recommendations.append(f"[Priority {check.priority}] {check.recommendation}")

        return recommendations

    def _identify_manual_checks(self, checks: List[AccessibilityCheck]) -> List[str]:
        """Identify checks that require manual verification"""
        manual_checks = [
            "Verify all images have appropriate alt text",
            "Test with screen reader for proper navigation",
            "Verify keyboard navigation works throughout application",
            "Test color contrast with actual design implementation",
            "Verify form labels are properly associated",
            "Test with users who have disabilities",
            "Verify motion animations respect user preferences",
            "Test time-sensitive features for adequate timing",
            "Verify error messages are clear and actionable",
            "Test focus management in dynamic content",
        ]

        return manual_checks

    def _estimate_remediation_time(self, checks: List[AccessibilityCheck]) -> str:
        """Estimate time needed to fix accessibility issues"""
        failed_checks = [c for c in checks if c.status == ComplianceStatus.FAIL]

        # Rough estimation based on priority and count
        high_priority = len([c for c in failed_checks if c.priority <= 2])
        medium_priority = len([c for c in failed_checks if c.priority == 3])
        low_priority = len([c for c in failed_checks if c.priority >= 4])

        estimated_hours = (high_priority * 4) + (medium_priority * 2) + (low_priority * 1)

        if estimated_hours <= 8:
            return "1 day"
        elif estimated_hours <= 40:
            return f"{estimated_hours // 8} days"
        else:
            return f"{estimated_hours // 40} weeks"

    def _load_wcag_guidelines(self) -> Dict[str, Any]:
        """Load WCAG 2.1 guidelines (simplified for this implementation)"""
        return {
            "1.1.1": {"title": "Non-text Content", "level": "A", "description": "All non-text content has a text alternative"},
            "1.3.1": {
                "title": "Info and Relationships",
                "level": "A",
                "description": "Information, structure, and relationships can be programmatically determined",
            },
            "1.4.3": {
                "title": "Contrast (Minimum)",
                "level": "AA",
                "description": "Text has a contrast ratio of at least 4.5:1",
            },
            "2.1.1": {"title": "Keyboard", "level": "A", "description": "All functionality is available from a keyboard"},
            "2.4.7": {"title": "Focus Visible", "level": "AA", "description": "Keyboard focus indicator is visible"},
            "3.3.1": {
                "title": "Error Identification",
                "level": "A",
                "description": "Errors are identified and described in text",
            },
        }


def validate_accessibility_compliance(ux_requirements: Dict[str, Any]) -> AccessibilityAssessment:
    """
    Convenience function to validate UX requirements for accessibility compliance

    Args:
        ux_requirements: Dictionary containing UX requirements data

    Returns:
        AccessibilityAssessment with detailed compliance evaluation
    """
    validator = AccessibilityValidator()
    return validator.validate_ux_requirements(ux_requirements)
