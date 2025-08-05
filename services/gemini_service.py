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

        prompt = f"""
You are an unbiased expert code reviewer. Analyze the following {file_data.get('type', 'code')} file named '{file_name}'.

Return your assessment strictly in this JSON format, without any extra commentary:

{{
  "grade": "A/B/C/D/F",
  "score": 0-100,
  "strengths": ["..."],
  "issues": ["..."],
  "suggestions": ["..."],
  "complexity": "Low/Medium/High",
  "maintainability": "Poor/Fair/Good/Excellent",
  "security_concerns": ["..."],
  "best_practices": ["..."]
}}

Code:
{content_sample}

Only return JSON.
"""

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))

            result['file_name'] = file_name
            result['file_type'] = file_data.get('type', 'unknown')
            result['file_path'] = file_data.get('path', 'unknown')

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

    def _determine_overall_grade(self, assessments: List[Dict]) -> str:
        if not assessments:
            return 'C'

        total_score = sum(a.get('score', 0) for a in assessments)
        avg_score = total_score / len(assessments)

        if avg_score >= 90:
            return 'A'
        elif avg_score >= 80:
            return 'B'
        elif avg_score >= 70:
            return 'C'
        elif avg_score >= 60:
            return 'D'
        else:
            return 'F'


    def _calculate_metrics(self, file_assessments: List[Dict]) -> Dict:
        if not file_assessments:
            return {
                'total_files': 0,
                'average_score': 0,
                'grade_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
            }

        total_score = sum(assessment.get('score', 0) for assessment in file_assessments)
        average_score = total_score / len(file_assessments)

        grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        for assessment in file_assessments:
            grade = assessment.get('grade', 'C')
            if grade in grade_counts:
                grade_counts[grade] += 1

        return {
            'total_files': len(file_assessments),
            'average_score': round(average_score),
            'grade_distribution': grade_counts
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
