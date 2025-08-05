# import os
# import json
# from datetime import datetime
# from jinja2 import Environment, FileSystemLoader
# import matplotlib.pyplot as plt
# import seaborn as sns
# import plotly.graph_objects as go
# import plotly.express as px
# from plotly.utils import PlotlyJSONEncoder
# import pandas as pd

# class ReportGenerator:
#     def __init__(self):
#         self.reports_dir = 'reports'
#         self.charts_dir = 'static/charts'
#         os.makedirs(self.reports_dir, exist_ok=True)
#         os.makedirs(self.charts_dir, exist_ok=True)
        
#         # Setup Jinja2 environment
#         self.jinja_env = Environment(
#             loader=FileSystemLoader('templates/reports')
#         )
    
#     def generate_github_report(self, repo_data, code_assessment, filename):
#         """Generate GitHub analysis report"""
#         try:
#             # Generate charts
#             charts = self._generate_github_charts(repo_data, code_assessment)
            
#             # Prepare template data
#             template_data = {
#                 'repo_data': repo_data,
#                 'code_assessment': code_assessment,
#                 'charts': charts,
#                 'generated_at': datetime.now(),
#                 'report_type': 'GitHub Analysis'
#             }
            
#             # Render template
#             template = self.jinja_env.get_template('github_report.html')
#             html_content = template.render(**template_data)
            
#             # Save report
#             report_path = os.path.join(self.reports_dir, filename)
#             with open(report_path, 'w', encoding='utf-8') as f:
#                 f.write(html_content)
            
#             return report_path
            
#         except Exception as e:
#             print(f"Error generating GitHub report: {str(e)}")
#             return self._generate_simple_report(repo_data, filename, 'GitHub Analysis')
    
#     def generate_api_report(self, base_url, test_results, filename):
#         """Generate API testing report"""
#         try:
#             # Generate charts
#             charts = self._generate_api_charts(test_results)
            
#             # Prepare template data
#             template_data = {
#                 'base_url': base_url,
#                 'test_results': test_results,
#                 'charts': charts,
#                 'generated_at': datetime.now(),
#                 'report_type': 'API Testing'
#             }
            
#             # Render template
#             template = self.jinja_env.get_template('api_report.html')
#             html_content = template.render(**template_data)
            
#             # Save report
#             report_path = os.path.join(self.reports_dir, filename)
#             with open(report_path, 'w', encoding='utf-8') as f:
#                 f.write(html_content)
            
#             return report_path
            
#         except Exception as e:
#             print(f"Error generating API report: {str(e)}")
#             return self._generate_simple_report(test_results, filename, 'API Testing')
    
#     def _generate_github_charts(self, repo_data, code_assessment):
#         """Generate charts for GitHub analysis"""
#         charts = {}
        
#         try:
#             # Commit activity chart
#             if repo_data.get('commits'):
#                 commits_df = pd.DataFrame(repo_data['commits'])
#                 commits_df['date'] = pd.to_datetime(commits_df['date'])
#                 commits_df['date_only'] = commits_df['date'].dt.date
                
#                 daily_commits = commits_df.groupby('date_only').size().reset_index(name='count')
                
#                 fig = px.line(daily_commits, x='date_only', y='count', 
#                              title='Daily Commit Activity',
#                              labels={'date_only': 'Date', 'count': 'Number of Commits'})
#                 fig.update_layout(xaxis_title='Date', yaxis_title='Commits')
#                 charts['commit_activity'] = json.dumps(fig, cls=PlotlyJSONEncoder)
            
#             # Code quality distribution
#             if code_assessment.get('file_assessments'):
#                 grades = [assessment['grade'] for assessment in code_assessment['file_assessments']]
#                 grade_counts = pd.Series(grades).value_counts().to_dict()
                
#                 fig = px.pie(values=list(grade_counts.values()), 
#                            names=list(grade_counts.keys()),
#                            title='Code Quality Grade Distribution')
#                 charts['grade_distribution'] = json.dumps(fig, cls=PlotlyJSONEncoder)
            
#             # File type distribution
#             if repo_data.get('files'):
#                 file_types = [file['type'] for file in repo_data['files']]
#                 type_counts = pd.Series(file_types).value_counts().head(10).to_dict()
                
#                 fig = px.bar(x=list(type_counts.keys()), y=list(type_counts.values()),
#                            title='File Type Distribution',
#                            labels={'x': 'File Type', 'y': 'Count'})
#                 charts['file_types'] = json.dumps(fig, cls=PlotlyJSONEncoder)
            
#         except Exception as e:
#             print(f"Error generating GitHub charts: {str(e)}")
        
#         return charts
    
#     def _generate_api_charts(self, test_results):
#         """Generate charts for API testing"""
#         charts = {}
        
#         try:
#             # Response time distribution
#             if test_results.get('endpoint_results'):
#                 endpoints = test_results['endpoint_results']
#                 response_times = [ep['response_time'] for ep in endpoints if ep['response_time'] > 0]
#                 endpoint_names = [f"{ep['method']} {ep['endpoint']}" for ep in endpoints if ep['response_time'] > 0]
                
#                 if response_times:
#                     fig = px.bar(x=endpoint_names, y=response_times,
#                                title='Response Time by Endpoint',
#                                labels={'x': 'Endpoint', 'y': 'Response Time (ms)'})
#                     fig.update_xaxis(tickangle=45)
#                     charts['response_times'] = json.dumps(fig, cls=PlotlyJSONEncoder)
            
#             # Status code distribution
#             if test_results.get('status_code_distribution'):
#                 status_codes = test_results['status_code_distribution']
                
#                 fig = px.pie(values=list(status_codes.values()), 
#                            names=[f"HTTP {code}" for code in status_codes.keys()],
#                            title='HTTP Status Code Distribution')
#                 charts['status_codes'] = json.dumps(fig, cls=PlotlyJSONEncoder)
            
#             # Performance grades
#             if test_results.get('endpoint_results'):
#                 endpoints = test_results['endpoint_results']
#                 grades = [ep.get('performance_grade', 'F') for ep in endpoints]
#                 grade_counts = pd.Series(grades).value_counts().to_dict()
                
#                 fig = px.bar(x=list(grade_counts.keys()), y=list(grade_counts.values()),
#                            title='Performance Grade Distribution',
#                            labels={'x': 'Grade', 'y': 'Count'},
#                            color=list(grade_counts.keys()),
#                            color_discrete_map={'A': 'green', 'B': 'yellow', 'C': 'orange', 'D': 'red', 'F': 'darkred'})
#                 charts['performance_grades'] = json.dumps(fig, cls=PlotlyJSONEncoder)
            
#         except Exception as e:
#             print(f"Error generating API charts: {str(e)}")
        
#         return charts
    
#     def _generate_simple_report(self, data, filename, report_type):
#         """Generate a simple HTML report when template fails"""
#         html_content = f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <title>AutoTestify - {report_type} Report</title>
#             <style>
#                 body {{ font-family: Arial, sans-serif; margin: 40px; }}
#                 .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
#                 .content {{ padding: 20px; }}
#                 .error {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0; }}
#             </style>
#         </head>
#         <body>
#             <div class="header">
#                 <h1>AutoTestify</h1>
#                 <h2>{report_type} Report</h2>
#                 <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
#             </div>
#             <div class="content">
#                 <div class="error">
#                     <h3>Report Generation Error</h3>
#                     <p>There was an issue generating the full report. Please check the system logs for details.</p>
#                 </div>
#                 <h3>Raw Data</h3>
#                 <pre>{json.dumps(data, indent=2, default=str)}</pre>
#             </div>
#         </body>
#         </html>
#         """
        
#         report_path = os.path.join(self.reports_dir, filename)
#         with open(report_path, 'w', encoding='utf-8') as f:
#             f.write(html_content)
        
#         return report_path

import os
import json
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import pandas as pd
import pdfkit

# Optional: for exporting HTML to PDF
try:
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReportGenerator:
    def __init__(self):
        self.reports_dir = 'reports'
        self.charts_dir = 'static/charts'
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.charts_dir, exist_ok=True)

        self.jinja_env = Environment(loader=FileSystemLoader('templates/reports'))

    # def generate_github_report(self, repo_data, code_assessment, filename, export_pdf=False):
    #     try:
    #         charts = self._generate_github_charts(repo_data, code_assessment)
    #         template_data = {
    #             'repo_data': repo_data,
    #             'code_assessment': code_assessment,
    #             'charts': charts,
    #             'generated_at': datetime.now(),
    #             'report_type': 'GitHub Analysis'
    #         }

    #         template = self._get_template('github_report.html')
    #         html_content = template.render(**template_data)

    #         report_path = self._save_report(html_content, filename)
    #         self._maybe_export_pdf(report_path, export_pdf)
    #         return report_path

    #     except Exception as e:
    #         logging.exception("GitHub report generation failed")
    #         return self._generate_simple_report(repo_data, filename, 'GitHub Analysis')
    def generate_github_report(self, repo_data, code_assessment, filename, export_pdf=False, selenium_ui_data=None):
        try:
            charts = self._generate_github_charts(repo_data, code_assessment)
            template_data = {
                'repo_data': repo_data,
                'code_assessment': code_assessment,
                'charts': charts,
                'generated_at': datetime.now(),
                'report_type': 'GitHub Analysis',
                'selenium_ui': selenium_ui_data or {}  # ✅ Pass to template
            }

            template = self._get_template('github_report.html')
            html_content = template.render(**template_data)

            report_path = self._save_report(html_content, filename)

            # ✅ Save Selenium metadata if present
            if selenium_ui_data:
                metadata_path = os.path.join(self.reports_dir, filename.replace('.html', '.json'))
                metadata = {
                    'selenium_ui': selenium_ui_data
                }
                with open(metadata_path, 'w') as meta_file:
                    json.dump(metadata, meta_file, indent=2)

            self._maybe_export_pdf(report_path, export_pdf)
            return report_path

        except Exception as e:
            logging.exception("GitHub report generation failed")
            return self._generate_simple_report(repo_data, filename, 'GitHub Analysis')


    def generate_api_report(self, base_url, test_results, filename, export_pdf=False):
        try:
            charts = self._generate_api_charts(test_results)
            template_data = {
                'base_url': base_url,
                'test_results': test_results,
                'charts': charts,
                'generated_at': datetime.now(),
                'report_type': 'API Testing'
            }

            template = self._get_template('api_report.html')
            html_content = template.render(**template_data)

            report_path = self._save_report(html_content, filename)
            self._maybe_export_pdf(report_path, export_pdf)
            return report_path

        except Exception as e:
            logging.exception("API report generation failed")
            return self._generate_simple_report(test_results, filename, 'API Testing')

    def _generate_github_charts(self, repo_data, code_assessment):
        charts = {}
        try:
            if repo_data.get('commits'):
                df = pd.DataFrame(repo_data['commits'])
                df['date'] = pd.to_datetime(df['date'])
                df['date_only'] = df['date'].dt.date
                daily = df.groupby('date_only').size().reset_index(name='count')

                fig = px.line(daily, x='date_only', y='count', title='Daily Commit Activity')
                fig.update_layout(template='plotly_dark')
                charts['commit_activity'] = json.dumps(fig, cls=PlotlyJSONEncoder)

            if code_assessment.get('file_assessments'):
                grades = [x['grade'] for x in code_assessment['file_assessments']]
                grade_counts = pd.Series(grades).value_counts()
                fig = px.pie(values=grade_counts.values, names=grade_counts.index, title='Code Quality Grades')
                charts['grade_distribution'] = json.dumps(fig, cls=PlotlyJSONEncoder)

            if repo_data.get('files'):
                file_types = [file['type'] for file in repo_data['files']]
                type_counts = pd.Series(file_types).value_counts().head(10)
                fig = px.bar(x=type_counts.index, y=type_counts.values, title='File Type Distribution')
                charts['file_types'] = json.dumps(fig, cls=PlotlyJSONEncoder)

        except Exception as e:
            logging.exception("GitHub chart generation failed")

        return charts

    def _generate_api_charts(self, test_results):
        charts = {}
        try:
            if test_results.get('endpoint_results'):
                endpoints = test_results['endpoint_results']
                valid = [ep for ep in endpoints if ep['response_time'] > 0]

                if valid:
                    names = [f"{ep['method']} {ep['endpoint']}" for ep in valid]
                    times = [ep['response_time'] for ep in valid]
                    fig = px.bar(x=names, y=times, title='Response Time by Endpoint')
                    fig.update_xaxes(tickangle=45)
                    charts['response_times'] = json.dumps(fig, cls=PlotlyJSONEncoder)

                grades = [ep.get('performance_grade', 'F') for ep in valid]
                grade_counts = pd.Series(grades).value_counts()
                fig = px.bar(x=grade_counts.index, y=grade_counts.values, title='Performance Grades')
                charts['performance_grades'] = json.dumps(fig, cls=PlotlyJSONEncoder)

            if test_results.get('status_code_distribution'):
                codes = test_results['status_code_distribution']
                fig = px.pie(values=list(codes.values()), names=[f"HTTP {k}" for k in codes.keys()],
                             title='Status Code Distribution')
                charts['status_codes'] = json.dumps(fig, cls=PlotlyJSONEncoder)

        except Exception as e:
            logging.exception("API chart generation failed")

        return charts

    def _generate_simple_report(self, data, filename, report_type):
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report_type} - Fallback Report</title>
            <style>
                body {{ font-family: sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                .error {{ background: #fdecea; color: #611a15; padding: 10px; border: 1px solid #f5c6cb; }}
                pre {{ background: #f8f9fa; padding: 15px; overflow: auto; }}
            </style>
        </head>
        <body>
            <h1>AutoTestify - {report_type} (Fallback)</h1>
            <p class="error">Failed to render full report. Showing raw data below.</p>
            <h2>Raw Data</h2>
            <pre>{json.dumps(data, indent=2, default=str)}</pre>
        </body>
        </html>
        """
        return self._save_report(html_content, filename)

    def _get_template(self, template_name):
        try:
            return self.jinja_env.get_template(template_name)
        except TemplateNotFound:
            logging.error(f"Template not found: {template_name}")
            raise

    def _save_report(self, html_content, filename):
        path = os.path.join(self.reports_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logging.info(f"Report saved to {path}")
        return path

    def _maybe_export_pdf(self, html_path, export_pdf):
        if export_pdf and PDF_ENABLED:
            pdf_path = html_path.replace('.html', '.pdf')
            try:
                pdfkit.from_file(html_path, pdf_path)
                logging.info(f"PDF exported to {pdf_path}")
            except Exception as e:
                logging.warning(f"PDF export failed: {e}")
