import requests
import datetime
import os
from typing import Dict, List, Optional
import pandas as pd
from prettytable import PrettyTable
import json

class RepoHealthChecker:
    def __init__(self, github_token: str):
        """Initialize the RepoHealthChecker with GitHub API token."""
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'

    def analyze_repository(self, owner: str, repo: str) -> Dict:
        """Analyze a GitHub repository and return health metrics."""
        repo_data = self._get_repo_info(owner, repo)
        issues_data = self._analyze_issues(owner, repo)
        commits_data = self._analyze_commits(owner, repo)
        # dependencies_data = self._analyze_dependencies(owner, repo)
        
        return {
            'basic_info': repo_data,
            'issues_analysis': issues_data,
            'commit_analysis': commits_data,
            # 'dependencies': dependencies_data
        }

    def _get_repo_info(self, owner: str, repo: str) -> Dict:
        """Get basic repository information."""
        url = f'{self.base_url}/repos/{owner}/{repo}'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            return {
                'name': data['name'],
                'stars': data['stargazers_count'],
                'forks': data['forks_count'],
                'open_issues': data['open_issues_count'],
                'created_at': data['created_at'],
                'last_update': data['updated_at'],
                'language': data['language'],
                'has_wiki': data['has_wiki'],
                'has_projects': data['has_projects']
            }
        return {}

    def _analyze_issues(self, owner: str, repo: str) -> Dict:
        """Analyze repository issues."""
        url = f'{self.base_url}/repos/{owner}/{repo}/issues'
        params = {'state': 'all', 'per_page': 100}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            issues = response.json()
            
            # Calculate average time to close issues
            closed_issues = [issue for issue in issues if issue['state'] == 'closed']
            if closed_issues:
                total_time = sum(
                    (datetime.datetime.strptime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ') -
                     datetime.datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')).days
                    for issue in closed_issues
                )
                avg_time_to_close = total_time / len(closed_issues)
            else:
                avg_time_to_close = 0

            return {
                'total_issues': len(issues),
                'open_issues': len([i for i in issues if i['state'] == 'open']),
                'closed_issues': len(closed_issues),
                'avg_time_to_close_days': avg_time_to_close
            }
        return {}

    def _analyze_commits(self, owner: str, repo: str) -> Dict:
        """Analyze repository commits."""
        url = f'{self.base_url}/repos/{owner}/{repo}/commits'
        params = {'per_page': 100}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            commits = response.json()
            
            # Analyze commit frequency
            commit_dates = [datetime.datetime.strptime(commit['commit']['author']['date'], 
                                                     '%Y-%m-%dT%H:%M:%SZ').date()
                          for commit in commits]
            
            if commit_dates:
                date_range = (max(commit_dates) - min(commit_dates)).days + 1
                commit_frequency = len(commits) / date_range if date_range > 0 else 0
            else:
                commit_frequency = 0

            return {
                'total_commits': len(commits),
                'commit_frequency_per_day': round(commit_frequency, 2)
            }
        return {}

    # def _analyze_dependencies(self, owner: str, repo: str) -> Dict:
    #     """Analyze repository dependencies and security alerts."""
    #     url = f'{self.base_url}/repos/{owner}/{repo}/dependency-graph/snapshots'
    #     response = requests.get(url, headers=self.headers)
        
    #     if response.status_code == 200:
    #         dependencies = response.json()
    #         return {
    #             'total_dependencies': len(dependencies),
    #             'direct_dependencies': len([d for d in dependencies if not d.get('indirect', False)]),
    #             'indirect_dependencies': len([d for d in dependencies if d.get('indirect', False)])
    #         }
    #     return {}

    def generate_report(self, analysis_data: Dict) -> str:
        """Generate a formatted report from the analysis data."""
        report = PrettyTable()
        report.field_names = ["Metric", "Value"]
        report.align["Metric"] = "l"
        report.align["Value"] = "r"

        # Basic Information
        basic_info = analysis_data['basic_info']
        report.add_row(["Repository Name", basic_info['name']])
        report.add_row(["Primary Language", basic_info['language']])
        report.add_row(["Stars", basic_info['stars']])
        report.add_row(["Forks", basic_info['forks']])

        # Issues Analysis
        issues_data = analysis_data['issues_analysis']
        report.add_row(["Total Issues", issues_data['total_issues']])
        report.add_row(["Open Issues", issues_data['open_issues']])
        report.add_row(["Average Days to Close", f"{issues_data['avg_time_to_close_days']:.1f}"])

        # Commit Analysis
        commit_data = analysis_data['commit_analysis']
        report.add_row(["Total Commits", commit_data['total_commits']])
        report.add_row(["Commits per Day", commit_data['commit_frequency_per_day']])

        # Dependencies
        # dep_data = analysis_data['dependencies']
        # report.add_row(["Total Dependencies", dep_data['total_dependencies']])
        # report.add_row(["Direct Dependencies", dep_data['direct_dependencies']])

        return str(report)

def main():
    # Get GitHub token from environment variable
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("Please set the GITHUB_TOKEN environment variable")

    # Initialize the checker
    checker = RepoHealthChecker(github_token)

    # Get repository details from user input
    owner = input("Enter repository owner: ")
    repo = input("Enter repository name: ")

    # Run analysis
    print(f"\nAnalyzing {owner}/{repo}...")
    analysis = checker.analyze_repository(owner, repo)

    # Generate and print report
    print("\nRepository Health Report")
    print("=" * 50)
    print(checker.generate_report(analysis))

    # Save report to file
    with open('repo_health_report.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    print("\nDetailed report saved to 'repo_health_report.json'")

if __name__ == "__main__":
    main()