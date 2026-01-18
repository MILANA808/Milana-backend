"""
Basic usage example for AKSI agents

This example demonstrates how to use the AKSI agents independently
for analyzing repositories and generating issues.
"""

from aksi_agents.researcher import AIResearcher
from aksi_agents.writer import AIWriter
from aksi_agents.validator import AIValidator
from aksi_agents.logger import AKSILogger


def example_research_and_write():
    """Example: Research repository and generate issue"""
    print("=== AKSI Basic Usage Example ===\n")

    # Initialize logger
    logger = AKSILogger()

    # Step 1: Research
    print("Step 1: Researching repository...")
    researcher = AIResearcher(logger)
    research = researcher.analyze_repository("example-org/example-repo", topic="automation")

    print(f"  Found {len(research.similar_issues)} similar issues")
    print(f"  Found {len(research.patterns)} patterns")
    print(f"  Recommendations: {len(research.recommendations)}")
    print()

    # Step 2: Write issue variants
    print("Step 2: Generating issue variants...")
    writer = AIWriter(logger)
    variants = writer.generate_issue_variants(
        topic="Automated Testing Infrastructure",
        context={
            "problem": "Manual testing is time-consuming",
            "solution": "Implement automated test suite",
            "patterns": research.patterns
        },
        num_variants=3
    )

    print(f"  Generated {len(variants)} variants")
    for i, variant in enumerate(variants, 1):
        print(f"  Variant {i}: EQS Score = {variant.eqs_score:.2f}")
        print(f"    Title: {variant.title}")
        print(f"    Labels: {', '.join(variant.labels)}")
    print()

    # Step 3: Validate best variant
    print("Step 3: Validating best variant...")
    validator = AIValidator(logger)
    best_variant = variants[0]

    validation = validator.validate_issue(
        title=best_variant.title,
        body=best_variant.body,
        labels=best_variant.labels
    )

    print(f"  Valid: {validation.is_valid}")
    print(f"  Validation Score: {validation.score:.2f}")
    if validation.errors:
        print(f"  Errors: {', '.join(validation.errors)}")
    if validation.warnings:
        print(f"  Warnings: {', '.join(validation.warnings)}")
    if validation.suggestions:
        print(f"  Suggestions: {', '.join(validation.suggestions)}")
    print()

    # Step 4: Display generated issue
    if validation.is_valid:
        print("Step 4: Generated Issue (Ready to Create)")
        print("=" * 60)
        print(f"Title: {best_variant.title}")
        print(f"Labels: {', '.join(best_variant.labels)}")
        print("\nBody:")
        print(best_variant.body)
        print("=" * 60)
    else:
        print("Step 4: Validation failed - issue needs improvements")

    return best_variant, validation


if __name__ == "__main__":
    example_research_and_write()
