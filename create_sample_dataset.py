#!/usr/bin/env python3
"""
Federal Bill Sample Dataset Creator
Analyzes bills by impact on people's lives and creates a representative sample
"""

import json
import os
import shutil
import re
from pathlib import Path
from collections import defaultdict
import random


class BillAnalyzer:
    def __init__(self, bills_dir):
        self.bills_dir = Path(bills_dir)
        self.bills_data = []
        self.impact_categories = {
            "high_impact": [],
            "medium_impact": [],
            "low_impact": [],
            "mixed_impact": [],
        }

        # Keywords for impact assessment
        self.high_impact_keywords = [
            "healthcare",
            "medicare",
            "medicaid",
            "prescription",
            "drug",
            "health insurance",
            "tax",
            "taxes",
            "wage",
            "wages",
            "benefit",
            "benefits",
            "unemployment",
            "student loan",
            "education funding",
            "school",
            "tuition",
            "housing",
            "rent",
            "mortgage",
            "affordable housing",
            "consumer protection",
            "privacy",
            "financial services",
            "banking",
            "immigration",
            "refugee",
            "asylum",
            "family reunification",
            "social security",
            "disability",
            "veterans benefits",
        ]

        self.medium_impact_keywords = [
            "infrastructure",
            "road",
            "bridge",
            "internet",
            "broadband",
            "utility",
            "environment",
            "air quality",
            "water quality",
            "climate",
            "pollution",
            "technology",
            "artificial intelligence",
            "ai",
            "data privacy",
            "digital rights",
            "veterans",
            "military benefits",
            "small business",
            "entrepreneur",
            "transportation",
            "public transit",
            "safety",
            "traffic",
        ]

        self.low_impact_keywords = [
            "post office",
            "naming",
            "commemorative",
            "resolution",
            "designation",
            "government operations",
            "agency reorganization",
            "administrative",
            "military equipment",
            "defense contract",
            "base",
            "facility",
            "treaty",
            "sanctions",
            "foreign policy",
            "diplomatic",
        ]

        self.administrative_keywords = [
            "post office",
            "naming",
            "commemorative",
            "designation",
            "resolution",
            "administrative",
            "procedural",
            "government operations",
        ]

    def load_bill_metadata(self, bill_path):
        """Load metadata for a single bill"""
        metadata_file = bill_path / "metadata.json"
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {metadata_file}: {e}")
            return None

    def analyze_bill_impact(self, bill_data):
        """Analyze bill impact based on title and description"""
        if not bill_data:
            return "mixed_impact"

        # Combine title and other titles for analysis
        text_to_analyze = bill_data.get("title", "").lower()
        for other_title in bill_data.get("other_titles", []):
            text_to_analyze += " " + other_title.get("title", "").lower()

        # Check for administrative bills first
        if any(keyword in text_to_analyze for keyword in self.administrative_keywords):
            return "low_impact"

        # Count keyword matches
        high_count = sum(
            1 for keyword in self.high_impact_keywords if keyword in text_to_analyze
        )
        medium_count = sum(
            1 for keyword in self.medium_impact_keywords if keyword in text_to_analyze
        )
        low_count = sum(
            1 for keyword in self.low_impact_keywords if keyword in text_to_analyze
        )

        # Determine impact level
        if high_count >= 2 or (high_count >= 1 and medium_count >= 1):
            return "high_impact"
        elif medium_count >= 2 or (medium_count >= 1 and high_count >= 1):
            return "medium_impact"
        elif low_count >= 2:
            return "low_impact"
        elif high_count == 1:
            return "high_impact"
        elif medium_count == 1:
            return "medium_impact"
        else:
            return "mixed_impact"

    def get_bill_progression_score(self, bill_data):
        """Calculate progression score based on actions"""
        if not bill_data or "actions" not in bill_data:
            return 0

        actions = bill_data["actions"]
        score = 0

        for action in actions:
            description = action.get("description", "").lower()
            classification = action.get("classification", [])

            # High progression indicators
            if "became law" in description or "became-law" in classification:
                score += 100
            elif (
                "signed by president" in description
                or "executive-signature" in classification
            ):
                score += 90
            elif "passed" in description and (
                "house" in description or "senate" in description
            ):
                score += 80
            elif (
                "committee.*report" in description or "ordered.*reported" in description
            ):
                score += 60
            elif "committee consideration" in description or "markup" in description:
                score += 40
            elif "referred" in description:
                score += 10
            elif "introduced" in description:
                score += 5

        return score

    def analyze_all_bills(self):
        """Analyze all bills in the directory"""
        print("Analyzing bills for impact on people's lives...")

        bill_dirs = [d for d in self.bills_dir.iterdir() if d.is_dir()]
        total_bills = len(bill_dirs)

        for i, bill_dir in enumerate(bill_dirs):
            if i % 500 == 0:
                print(f"Processed {i}/{total_bills} bills...")

            bill_data = self.load_bill_metadata(bill_dir)
            if not bill_data:
                continue

            impact_level = self.analyze_bill_impact(bill_data)
            progression_score = self.get_bill_progression_score(bill_data)

            bill_info = {
                "path": bill_dir,
                "identifier": bill_data.get("identifier", ""),
                "title": bill_data.get("title", ""),
                "impact_level": impact_level,
                "progression_score": progression_score,
                "cosponsor_count": len(bill_data.get("sponsorships", [])),
                "actions_count": len(bill_data.get("actions", [])),
                "metadata": bill_data,
            }

            self.bills_data.append(bill_info)
            self.impact_categories[impact_level].append(bill_info)

        print(f"Analysis complete! Found {len(self.bills_data)} bills:")
        for category, bills in self.impact_categories.items():
            print(f"  {category}: {len(bills)} bills")

    def select_sample_bills(self, target_total=250):
        """Select representative sample of bills"""
        print(f"\nSelecting sample of {target_total} bills...")

        # Calculate target distribution
        total_bills = len(self.bills_data)
        high_impact_ratio = 0.3  # 30% high impact
        medium_impact_ratio = 0.4  # 40% medium impact
        low_impact_ratio = 0.2  # 20% low impact
        mixed_impact_ratio = 0.1  # 10% mixed impact

        targets = {
            "high_impact": int(target_total * high_impact_ratio),
            "medium_impact": int(target_total * medium_impact_ratio),
            "low_impact": int(target_total * low_impact_ratio),
            "mixed_impact": int(target_total * mixed_impact_ratio),
        }

        selected_bills = []

        for category, target_count in targets.items():
            available_bills = self.impact_categories[category]

            if len(available_bills) <= target_count:
                # Take all bills in this category
                selected_bills.extend(available_bills)
                print(f"  {category}: Selected all {len(available_bills)} bills")
            else:
                # Sort by progression score and cosponsor count, then sample
                sorted_bills = sorted(
                    available_bills,
                    key=lambda x: (x["progression_score"], x["cosponsor_count"]),
                    reverse=True,
                )

                # Take top 60% by progression, then random sample from rest
                top_count = int(target_count * 0.6)
                random_count = target_count - top_count

                selected = sorted_bills[:top_count]
                remaining = sorted_bills[top_count:]

                if random_count > 0 and remaining:
                    selected.extend(
                        random.sample(remaining, min(random_count, len(remaining)))
                    )

                selected_bills.extend(selected)
                print(
                    f"  {category}: Selected {len(selected)} bills (top {top_count} + {random_count} random)"
                )

        print(f"\nTotal selected: {len(selected_bills)} bills")
        return selected_bills

    def create_sample_dataset(self, selected_bills, output_dir):
        """Create the sample dataset by copying selected bills"""
        print(f"\nCreating sample dataset in {output_dir}...")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Copy each selected bill
        for i, bill_info in enumerate(selected_bills):
            if i % 50 == 0:
                print(f"  Copied {i}/{len(selected_bills)} bills...")

            source_path = bill_info["path"]
            dest_path = output_path / source_path.name

            # Copy entire bill directory
            if source_path.exists():
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)

        print(f"Sample dataset created with {len(selected_bills)} bills!")

        # Create summary report
        self.create_summary_report(selected_bills, output_path)

    def create_summary_report(self, selected_bills, output_path):
        """Create a summary report of the sample dataset"""
        report = {
            "total_bills": len(selected_bills),
            "creation_date": str(Path().cwd()),
            "impact_distribution": defaultdict(int),
            "bill_types": defaultdict(int),
            "progression_stats": {
                "became_law": 0,
                "passed_chamber": 0,
                "committee_activity": 0,
                "introduced_only": 0,
            },
            "sample_bills": [],
        }

        for bill in selected_bills:
            # Impact distribution
            report["impact_distribution"][bill["impact_level"]] += 1

            # Bill types
            identifier = bill["identifier"]
            if identifier.startswith("HR"):
                report["bill_types"]["House Bills"] += 1
            elif identifier.startswith("S"):
                report["bill_types"]["Senate Bills"] += 1
            elif "JRES" in identifier:
                report["bill_types"]["Joint Resolutions"] += 1
            elif "CONRES" in identifier:
                report["bill_types"]["Concurrent Resolutions"] += 1

            # Progression stats
            if bill["progression_score"] >= 90:
                report["progression_stats"]["became_law"] += 1
            elif bill["progression_score"] >= 70:
                report["progression_stats"]["passed_chamber"] += 1
            elif bill["progression_score"] >= 30:
                report["progression_stats"]["committee_activity"] += 1
            else:
                report["progression_stats"]["introduced_only"] += 1

            # Sample bill info
            report["sample_bills"].append(
                {
                    "identifier": bill["identifier"],
                    "title": bill["title"],
                    "impact_level": bill["impact_level"],
                    "progression_score": bill["progression_score"],
                    "cosponsor_count": bill["cosponsor_count"],
                }
            )

        # Save report
        report_file = output_path / "sample_dataset_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"Summary report saved to {report_file}")


def main():
    # Configuration
    current_bills_dir = "/Users/tamara/tad_code.nosync/current_projects/CHN/SAMPLE-DATA-SETS/usa-data-pipeline-SAMPLE/data_output/data_processed/country:us/congress/sessions/119/bills"
    backup_dir = "/Users/tamara/tad_code.nosync/current_projects/CHN/SAMPLE-DATA-SETS/usa-data-pipeline-SAMPLE/data_output/data_processed/country:us/congress/sessions/119/bills_full_dataset"
    new_bills_dir = "/Users/tamara/tad_code.nosync/current_projects/CHN/SAMPLE-DATA-SETS/usa-data-pipeline-SAMPLE/data_output/data_processed/country:us/congress/sessions/119/bills"

    print("Federal Bill Sample Dataset Creator")
    print("=" * 50)

    # Step 1: Rename current directory to backup
    print(f"Step 1: Backing up current dataset to {backup_dir}")
    if Path(current_bills_dir).exists():
        if Path(backup_dir).exists():
            shutil.rmtree(backup_dir)
        shutil.move(current_bills_dir, backup_dir)
        print("✓ Backup created")
    else:
        print("✗ Current bills directory not found!")
        return

    # Step 2: Analyze bills
    print(f"\nStep 2: Analyzing bills from backup")
    analyzer = BillAnalyzer(backup_dir)
    analyzer.analyze_all_bills()

    # Step 3: Select sample
    print(f"\nStep 3: Selecting representative sample")
    selected_bills = analyzer.select_sample_bills(target_total=250)

    # Step 4: Create new sample dataset
    print(f"\nStep 4: Creating sample dataset")
    analyzer.create_sample_dataset(selected_bills, new_bills_dir)

    print("\n" + "=" * 50)
    print("Sample dataset creation complete!")
    print(f"Original dataset: {backup_dir}")
    print(f"Sample dataset: {new_bills_dir}")
    print(f"Total bills in sample: {len(selected_bills)}")


if __name__ == "__main__":
    main()
