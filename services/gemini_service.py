import google.generativeai as genai
import os
import json
from typing import List, Dict
import random
import os.path
import time


class GeminiService:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

    def assess_code_quality(self, files: List[Dict]) -> Dict:
        if not self.model:
            return self._generate_mock_assessment(files)

        assessment_results = {
            'file_assessments': []
        }

        try:
            batch_size = 15
            total_files = len(files)

            for i in range(0, total_files, batch_size):
                batch = files[i:i + batch_size]

                for file_data in batch:
                    if file_data.get('content'):
                        try:
                            file_assessment = self._assess_single_file(file_data)
                        except Exception as fe:
                            print(f"Error assessing file {file_data.get('name')}: {fe}")
                            file_assessment = self._generate_mock_file_assessment(file_data)
                        assessment_results['file_assessments'].append(file_assessment)

                # Sleep only if more files are left
                if i + batch_size < total_files:
                    print(f"Processed {i + batch_size} files. Sleeping 60 seconds to respect Gemini rate limits...")
                    time.sleep(60)

            summary = self._generate_overall_summary(assessment_results['file_assessments'])
            assessment_results['summary'] = summary
            assessment_results['metrics'] = self._calculate_metrics(assessment_results['file_assessments'])
            assessment_results['overall_grade'] = summary.get('overall_grade', 'B')
            assessment_results['overall_score'] = assessment_results['metrics']['average_score']

        except Exception as e:
            print(f"Error in Gemini assessment: {str(e)}")
            return self._generate_mock_assessment(files)

        return assessment_results

    def _assess_single_file(self, file_data: Dict) -> Dict:
        file_name = file_data.get('name') or os.path.basename(file_data.get('path', 'unknown'))
        content_sample = file_data.get('content', '')[:4000]
        file_size = len(file_data.get('content', ''))

        prompt = f"""
You are an expert code reviewer. Analyze this {file_data.get('type', 'code')} file: '{file_name}' ({file_size} chars).

Evaluate based on:
- Code Quality (30%): Structure, readability, naming conventions
- Security (25%): Vulnerabilities, input validation, best practices
- Performance (20%): Efficiency, optimization opportunities
- Maintainability (15%): Documentation, modularity, testability
- Best Practices (10%): Language-specific standards, patterns

Return JSON only:
{{
  "grade": "A/B/C/D/F",
  "score": 0-100,
  "quality_score": 0-100,
  "security_score": 0-100,
  "performance_score": 0-100,
  "maintainability_score": 0-100,
  "best_practices_score": 0-100,
  "strengths": ["..."],
  "issues": ["..."],
  "suggestions": ["..."],
  "complexity": "Low/Medium/High",
  "maintainability": "Poor/Fair/Good/Excellent",
  "security_concerns": ["..."],
  "best_practices": ["..."],
  "lines_of_code": 0,
  "cyclomatic_complexity": "Low/Medium/High"
}}

Code:
{content_sample}
"""

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))

            # Calculate weighted score if individual scores provided
            if all(key in result for key in ['quality_score', 'security_score', 'performance_score', 'maintainability_score', 'best_practices_score']):
                weighted_score = (
                    result['quality_score'] * 0.30 +
                    result['security_score'] * 0.25 +
                    result['performance_score'] * 0.20 +
                    result['maintainability_score'] * 0.15 +
                    result['best_practices_score'] * 0.10
                )
                result['score'] = round(weighted_score)
                result['grade'] = self._score_to_grade(weighted_score)

            result['file_name'] = file_name
            result['file_type'] = file_data.get('type', 'unknown')
            result['file_path'] = file_data.get('path', 'unknown')
            result['file_size'] = file_size

            return result

        except Exception as e:
            print(f"Error assessing file {file_name}: {str(e)}")
            return self._generate_mock_file_assessment(file_data)

    def _generate_overall_summary(self, file_assessments: List[Dict]) -> Dict:
        if not file_assessments:
            return {
                'strengths': ['Clean code structure'],
                'weaknesses': ['Limited documentation'],
                'recommendations': ['Add comments'],
                'overall_grade': 'C'
            }

        all_strengths, all_issues, all_suggestions = [], [], []

        for assessment in file_assessments:
            all_strengths.extend(assessment.get('strengths', []))
            all_issues.extend(assessment.get('issues', []))
            all_suggestions.extend(assessment.get('suggestions', []))

        return {
            'strengths': list(set(all_strengths))[:5],
            'weaknesses': list(set(all_issues))[:5],
            'recommendations': list(set(all_suggestions))[:5],
            'overall_grade': self._determine_overall_grade(file_assessments)
        }

    # def _determine_overall_grade(self, assessments: List[Dict]) -> str:
    #     grade_priority = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
    #     total = sum(grade_priority.get(a.get('grade', 'C'), 3) for a in assessments)
    #     avg = total / len(assessments)
    #     for grade, value in reversed(grade_priority.items()):
    #         if avg >= value:
    #             return grade
    #     return 'C'

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'A-'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'B-'
        elif score >= 65:
            return 'C+'
        elif score >= 60:
            return 'C'
        elif score >= 55:
            return 'C-'
        elif score >= 50:
            return 'D'
        else:
            return 'F'

    def _determine_overall_grade(self, assessments: List[Dict]) -> str:
        if not assessments:
            return 'C'

        # Weight by file importance (larger files, core files get more weight)
        total_weighted_score = 0
        total_weight = 0
        
        for assessment in assessments:
            score = assessment.get('score', 0)
            file_size = assessment.get('file_size', 100)
            file_type = assessment.get('file_type', '')
            
            # Calculate weight based on file characteristics
            weight = 1.0
            if file_size > 1000:  # Larger files get more weight
                weight *= 1.5
            if file_type in ['python', 'javascript', 'java', 'cpp']:  # Core languages
                weight *= 1.3
            if 'main' in assessment.get('file_name', '').lower():  # Main files
                weight *= 1.4
                
            total_weighted_score += score * weight
            total_weight += weight

        avg_score = total_weighted_score / total_weight if total_weight > 0 else 0
        return self._score_to_grade(avg_score)


    def _calculate_metrics(self, file_assessments: List[Dict]) -> Dict:
        if not file_assessments:
            return {
                'total_files': 0,
                'average_score': 0,
                'grade_distribution': {},
                'category_scores': {},
                'complexity_distribution': {},
                'security_issues': 0,
                'total_lines': 0
            }

        total_score = sum(assessment.get('score', 0) for assessment in file_assessments)
        average_score = total_score / len(file_assessments)

        # Enhanced grade distribution with +/- grades
        grade_counts = {}
        complexity_counts = {'Low': 0, 'Medium': 0, 'High': 0}
        security_issues = 0
        total_lines = 0
        
        # Category score aggregation
        category_totals = {
            'quality_score': 0,
            'security_score': 0,
            'performance_score': 0,
            'maintainability_score': 0,
            'best_practices_score': 0
        }
        category_counts = {key: 0 for key in category_totals.keys()}
        
        for assessment in file_assessments:
            grade = assessment.get('grade', 'C')
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
            
            complexity = assessment.get('complexity', 'Medium')
            if complexity in complexity_counts:
                complexity_counts[complexity] += 1
                
            security_concerns = assessment.get('security_concerns', [])
            security_issues += len(security_concerns)
            
            lines = assessment.get('lines_of_code', 0)
            total_lines += lines
            
            # Aggregate category scores
            for category in category_totals.keys():
                if category in assessment:
                    category_totals[category] += assessment[category]
                    category_counts[category] += 1

        # Calculate average category scores
        category_scores = {}
        for category, total in category_totals.items():
            if category_counts[category] > 0:
                category_scores[category.replace('_score', '')] = round(total / category_counts[category])

        return {
            'total_files': len(file_assessments),
            'average_score': round(average_score),
            'grade_distribution': grade_counts,
            'category_scores': category_scores,
            'complexity_distribution': complexity_counts,
            'security_issues': security_issues,
            'total_lines': total_lines,
            'files_with_issues': len([a for a in file_assessments if len(a.get('issues', [])) > 0])
        }

    def _generate_mock_assessment(self, files: List[Dict]) -> Dict:
        mock_assessments = [self._generate_mock_file_assessment(file_data) for file_data in files]
        return {
            'overall_grade': 'B',
            'overall_score': 85,
            'file_assessments': mock_assessments,
            'summary': self._generate_overall_summary(mock_assessments),
            'metrics': self._calculate_metrics(mock_assessments)
        }

    def _generate_mock_file_assessment(self, file_data: Dict) -> Dict:
        grades = ['A', 'B', 'C']
        scores = [95, 85, 75]
        grade_index = random.randint(0, len(grades) - 1)

        return {
            'file_name': file_data.get('name') or os.path.basename(file_data.get('path', 'unknown')),
            'file_type': file_data.get('type', 'unknown'),
            'file_path': file_data.get('path', 'unknown'),
            'grade': grades[grade_index],
            'score': scores[grade_index] + random.randint(-3, 3),
            'strengths': ["Readable code", "Logical flow"],
            'issues': ["Could use more comments"],
            'suggestions': ["Add error handling"],
            'complexity': random.choice(['Low', 'Medium', 'High']),
            'maintainability': random.choice(['Good', 'Excellent']),
            'security_concerns': [],
            'best_practices': ["Consistent formatting"]
        }
