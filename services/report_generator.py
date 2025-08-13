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
import numpy as np
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
    def generate_github_report_content(self, repo_data, code_assessment, selenium_ui_data=None):
        """Generate GitHub report HTML content without saving to file"""
        try:
            charts = self._generate_github_charts(repo_data, code_assessment)
            template_data = {
                'repo_data': repo_data,
                'code_assessment': code_assessment,
                'charts': charts,
                'generated_at': datetime.now(),
                'report_type': 'GitHub Analysis',
                'selenium_ui': selenium_ui_data or {}
            }

            template = self._get_template('github_report.html')
            return template.render(**template_data)

        except Exception as e:
            logging.exception("GitHub report generation failed")
            return self._generate_simple_report_content(repo_data, 'GitHub Analysis')

    def generate_github_report(self, repo_data, code_assessment, filename, export_pdf=False, selenium_ui_data=None):
        try:
            html_content = self.generate_github_report_content(repo_data, code_assessment, selenium_ui_data)
            report_path = self._save_report(html_content, filename)

            if selenium_ui_data:
                metadata_path = os.path.join(self.reports_dir, filename.replace('.html', '.json'))
                metadata = {'selenium_ui': selenium_ui_data}
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
            # Commit activity chart
            if repo_data.get('commits') and len(repo_data['commits']) > 0:
                df = pd.DataFrame(repo_data['commits'])
                df['date'] = pd.to_datetime(df['date'])
                df['date_only'] = df['date'].dt.date
                daily = df.groupby('date_only').size().reset_index(name='count')

                fig = px.line(daily, x='date_only', y='count', title='Daily Commit Activity')
                fig.update_layout(
                    height=400,
                    autosize=True,
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                charts['commit_activity'] = json.dumps(fig, cls=PlotlyJSONEncoder)

            # Enhanced Grade distribution chart
            if code_assessment.get('file_assessments') and len(code_assessment['file_assessments']) > 0:
                grades = [x.get('grade', 'F') for x in code_assessment['file_assessments'] if x.get('grade')]
                if grades:
                    grade_counts = pd.Series(grades).value_counts()
                    
                    # Define colors for grades
                    grade_colors = {
                        'A+': '#1f77b4', 'A': '#2ca02c', 'A-': '#17becf',
                        'B+': '#ff7f0e', 'B': '#ffbb78', 'B-': '#d62728',
                        'C+': '#9467bd', 'C': '#c5b0d5', 'C-': '#8c564b',
                        'D': '#e377c2', 'F': '#7f7f7f'
                    }
                    
                    colors = [grade_colors.get(grade, '#cccccc') for grade in grade_counts.index]
                    
                    fig = px.pie(
                        values=grade_counts.values.tolist(), 
                        names=grade_counts.index.tolist(), 
                        title='Code Quality Grade Distribution',
                        color_discrete_sequence=colors
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(
                        height=450,
                        autosize=True,
                        margin=dict(l=40, r=40, t=60, b=40),
                        showlegend=True
                    )
                    charts['grade_distribution'] = json.dumps(fig, cls=PlotlyJSONEncoder)
                    
                    # Enhanced Category scores radar chart
                    metrics = code_assessment.get('metrics', {})
                    category_scores = metrics.get('category_scores', {})
                    if category_scores:
                        # Normalize and enhance category names
                        category_mapping = {
                            'quality': 'Code Quality',
                            'security': 'Security',
                            'performance': 'Performance', 
                            'maintainability': 'Maintainability',
                            'best_practices': 'Best Practices'
                        }
                        
                        categories = [category_mapping.get(k, k.title()) for k in category_scores.keys()]
                        scores = list(category_scores.values())
                        
                        # Add benchmark line at 80 (good threshold)
                        benchmark_scores = [80] * len(categories)
                        
                        fig = px.line_polar(
                            r=[scores, benchmark_scores],
                            theta=[categories, categories],
                            line_close=True,
                            title='Code Quality Assessment vs Benchmark (80)',
                            color_discrete_sequence=['#1f77b4', '#ff7f0e']
                        )
                        
                        fig.update_traces(
                            fill='toself',
                            fillcolor=['rgba(31,119,180,0.3)', 'rgba(255,127,14,0.1)'],
                            name=['Current Score', 'Benchmark (80)']
                        )
                        
                        fig.update_layout(
                            height=450,
                            polar=dict(
                                radialaxis=dict(
                                    visible=True, 
                                    range=[0, 100],
                                    tickmode='linear',
                                    tick0=0,
                                    dtick=20,
                                    gridcolor='rgba(0,0,0,0.1)'
                                ),
                                angularaxis=dict(
                                    tickfont=dict(size=12)
                                )
                            ),
                            margin=dict(l=60, r=60, t=80, b=60),
                            showlegend=True,
                            legend=dict(x=0.8, y=0.1)
                        )
                        charts['category_radar'] = json.dumps(fig, cls=PlotlyJSONEncoder)
                    
                    # Complexity distribution
                    complexity_dist = metrics.get('complexity_distribution', {})
                    if complexity_dist:
                        fig = px.bar(
                            x=list(complexity_dist.keys()),
                            y=list(complexity_dist.values()),
                            title='Code Complexity Distribution',
                            color=list(complexity_dist.values()),
                            color_continuous_scale='RdYlGn_r'
                        )
                        fig.update_layout(
                            height=350,
                            autosize=True,
                            margin=dict(l=40, r=40, t=60, b=40),
                            showlegend=False
                        )
                        charts['complexity_distribution'] = json.dumps(fig, cls=PlotlyJSONEncoder)

            # Enhanced File type distribution chart
            if repo_data.get('files') and len(repo_data['files']) > 0:
                file_types = [file.get('type', 'Unknown') for file in repo_data['files'] if file.get('type')]
                if file_types:
                    type_counts = pd.Series(file_types).value_counts().head(10)
                    
                    # Create horizontal bar chart for better readability
                    fig = px.bar(
                        y=type_counts.index.tolist(), 
                        x=type_counts.values.tolist(), 
                        title='File Type Distribution',
                        orientation='h',
                        color=type_counts.values.tolist(),
                        color_continuous_scale='viridis'
                    )
                    fig.update_layout(
                        height=max(300, len(type_counts) * 30),
                        autosize=True,
                        margin=dict(l=100, r=40, t=60, b=40),
                        showlegend=False
                    )
                    charts['file_types'] = json.dumps(fig, cls=PlotlyJSONEncoder)
                    
                    # Enhanced Score vs File Size scatter plot
                    if code_assessment.get('file_assessments'):
                        assessments = code_assessment['file_assessments']
                        valid_assessments = [a for a in assessments if a.get('score', 0) > 0 and a.get('file_size', 0) > 0]
                        
                        if len(valid_assessments) > 0:
                            scores = [a.get('score', 0) for a in valid_assessments]
                            sizes = [a.get('file_size', 0) for a in valid_assessments]
                            names = [a.get('file_name', 'Unknown') for a in valid_assessments]
                            file_types = [a.get('file_type', 'unknown') for a in valid_assessments]
                            complexity = [a.get('complexity', 'Medium') for a in valid_assessments]
                            
                            # Create size categories for better visualization
                            size_categories = []
                            for size in sizes:
                                if size < 500:
                                    size_categories.append('Small (<500)')
                                elif size < 2000:
                                    size_categories.append('Medium (500-2K)')
                                elif size < 5000:
                                    size_categories.append('Large (2K-5K)')
                                else:
                                    size_categories.append('Very Large (>5K)')
                            
                            # Create hover text with detailed info
                            hover_text = [
                                f"<b>{name}</b><br>" +
                                f"Score: {score}/100<br>" +
                                f"Size: {size:,} chars<br>" +
                                f"Type: {ftype}<br>" +
                                f"Complexity: {comp}"
                                for name, score, size, ftype, comp in zip(names, scores, sizes, file_types, complexity)
                            ]
                            
                            fig = px.scatter(
                                x=sizes,
                                y=scores,
                                color=complexity,
                                symbol=size_categories,
                                title='Code Quality vs File Size (by Complexity & Size Category)',
                                labels={'x': 'File Size (characters)', 'y': 'Quality Score', 'color': 'Complexity'},
                                color_discrete_map={
                                    'Low': '#2ca02c',
                                    'Medium': '#ff7f0e', 
                                    'High': '#d62728'
                                },
                                hover_name=hover_text,
                                size=[max(8, min(25, s/200)) for s in sizes]
                            )
                            
                            # Add trend line
                            try:
                                if len(sizes) > 2:
                                    z = np.polyfit(sizes, scores, 1)
                                    p = np.poly1d(z)
                                    x_trend = np.linspace(min(sizes), max(sizes), 100)
                                    y_trend = p(x_trend)
                                    
                                    fig.add_scatter(
                                        x=x_trend, y=y_trend,
                                        mode='lines',
                                        name='Trend Line',
                                        line=dict(color='rgba(0,0,0,0.5)', dash='dash')
                                    )
                            except ImportError:
                                pass  # Skip trend line if numpy not available
                            
                            # Add quality threshold lines
                            fig.add_hline(y=90, line_dash="dot", line_color="green", annotation_text="Excellent (90+)")
                            fig.add_hline(y=70, line_dash="dot", line_color="orange", annotation_text="Good (70+)")
                            fig.add_hline(y=50, line_dash="dot", line_color="red", annotation_text="Needs Work (50+)")
                            
                            fig.update_layout(
                                height=500,
                                autosize=True,
                                margin=dict(l=60, r=40, t=80, b=60),
                                showlegend=True,
                                legend=dict(x=1.02, y=1),
                                xaxis=dict(type='log' if max(sizes) > 10000 else 'linear'),
                                annotations=[
                                    dict(x=0.02, y=0.98, xref='paper', yref='paper',
                                         text=f"Files analyzed: {len(valid_assessments)}",
                                         showarrow=False, font=dict(size=10))
                                ]
                            )
                            charts['score_vs_size'] = json.dumps(fig, cls=PlotlyJSONEncoder)

        except Exception as e:
            logging.exception("GitHub chart generation failed")

        return charts

    def _generate_api_charts(self, test_results):
        charts = {}
        try:
            endpoints = test_results.get('endpoint_results', [])
            if not endpoints:
                return charts
            
            valid_endpoints = [ep for ep in endpoints if ep.get('response_time', 0) > 0]
            
            if valid_endpoints:
                # Enhanced Response Time Chart with improved visualization
                if len(valid_endpoints) > 0:
                    # Prepare data with better formatting
                    endpoint_data = []
                    for ep in valid_endpoints:
                        method = ep.get('method', 'GET')
                        endpoint = ep.get('endpoint', '')[:30]
                        time_ms = max(0, ep.get('response_time', 0))
                        status = ep.get('status_code', 0)
                        success = ep.get('success', False)
                        
                        # Performance category
                        if time_ms < 200:
                            perf_category = 'Excellent (<200ms)'
                            color = '#2ca02c'
                        elif time_ms < 500:
                            perf_category = 'Good (200-500ms)'
                            color = '#17becf'
                        elif time_ms < 1000:
                            perf_category = 'Fair (500ms-1s)'
                            color = '#ff7f0e'
                        elif time_ms < 2000:
                            perf_category = 'Slow (1-2s)'
                            color = '#fd7e14'
                        else:
                            perf_category = 'Very Slow (>2s)'
                            color = '#d62728'
                        
                        endpoint_data.append({
                            'name': f"{method} {endpoint}",
                            'time': time_ms,
                            'method': method,
                            'endpoint': endpoint,
                            'status': status,
                            'success': success,
                            'category': perf_category,
                            'color': color
                        })
                    
                    # Sort by response time for better visualization
                    endpoint_data.sort(key=lambda x: x['time'])
                    
                    names = [d['name'] for d in endpoint_data]
                    times = [d['time'] for d in endpoint_data]
                    colors = [d['color'] for d in endpoint_data]
                    categories = [d['category'] for d in endpoint_data]
                    
                    # Create hover text with detailed information
                    hover_text = [
                        f"<b>{d['method']} {d['endpoint']}</b><br>" +
                        f"Response Time: {d['time']:,.0f}ms<br>" +
                        f"Status Code: {d['status']}<br>" +
                        f"Performance: {d['category']}<br>" +
                        f"Success: {'✓' if d['success'] else '✗'}"
                        for d in endpoint_data
                    ]
                    
                    # Create the bar chart
                    fig = px.bar(
                        x=names, y=times,
                        title='API Response Time Analysis (Sorted by Performance)',
                        labels={'x': 'Endpoints', 'y': 'Response Time (ms)'},
                        color=categories,
                        color_discrete_map={
                            'Excellent (<200ms)': '#2ca02c',
                            'Good (200-500ms)': '#17becf', 
                            'Fair (500ms-1s)': '#ff7f0e',
                            'Slow (1-2s)': '#fd7e14',
                            'Very Slow (>2s)': '#d62728'
                        },
                        hover_name=hover_text
                    )
                    
                    # Add performance threshold zones
                    fig.add_hrect(y0=0, y1=200, fillcolor="rgba(44,160,44,0.1)", 
                                  annotation_text="Excellent Zone", annotation_position="top left",
                                  line_width=0)
                    fig.add_hrect(y0=200, y1=500, fillcolor="rgba(23,190,207,0.1)", 
                                  annotation_text="Good Zone", annotation_position="top left",
                                  line_width=0)
                    fig.add_hrect(y0=500, y1=1000, fillcolor="rgba(255,127,14,0.1)", 
                                  annotation_text="Fair Zone", annotation_position="top left",
                                  line_width=0)
                    fig.add_hrect(y0=1000, y1=max(times) * 1.1 if times else 2000, 
                                  fillcolor="rgba(214,39,40,0.1)", 
                                  annotation_text="Slow Zone", annotation_position="top left",
                                  line_width=0)
                    
                    # Add threshold lines
                    fig.add_hline(y=200, line_dash="dash", line_color="#2ca02c", line_width=2,
                                  annotation_text="200ms (Excellent)", annotation_position="right")
                    fig.add_hline(y=500, line_dash="dash", line_color="#17becf", line_width=2,
                                  annotation_text="500ms (Good)", annotation_position="right")
                    fig.add_hline(y=1000, line_dash="dash", line_color="#ff7f0e", line_width=2,
                                  annotation_text="1s (Fair)", annotation_position="right")
                    
                    # Calculate statistics for annotations
                    avg_time = sum(times) / len(times) if times else 0
                    median_time = sorted(times)[len(times)//2] if times else 0
                    
                    fig.update_xaxes(
                        tickangle=-45,
                        title="API Endpoints (sorted by response time)"
                    )
                    fig.update_yaxes(
                        title="Response Time (milliseconds)",
                        type="linear"
                    )
                    
                    fig.update_layout(
                        height=500, 
                        margin=dict(l=60, r=120, t=80, b=140), 
                        showlegend=True,
                        legend=dict(
                            orientation="v",
                            yanchor="top",
                            y=1,
                            xanchor="left",
                            x=1.02
                        ),
                        annotations=[
                            dict(
                                x=0.02, y=0.98, xref='paper', yref='paper',
                                text=f"Avg: {avg_time:.0f}ms | Median: {median_time:.0f}ms | Endpoints: {len(times)}",
                                showarrow=False, 
                                font=dict(size=11, color="#666"),
                                bgcolor="rgba(255,255,255,0.8)",
                                bordercolor="#ddd",
                                borderwidth=1
                            )
                        ],
                        hovermode='x unified'
                    )
                    
                    charts['response_times'] = json.dumps(fig, cls=PlotlyJSONEncoder)
                
                # Performance Grades Distribution
                grades = [ep.get('performance_grade', 'F') for ep in valid_endpoints if ep.get('performance_grade')]
                if grades:
                    grade_counts = {}
                    for grade in grades:
                        grade_counts[grade] = grade_counts.get(grade, 0) + 1
                    
                    # Sort grades in logical order
                    grade_order = ['A', 'B', 'C', 'D', 'F']
                    sorted_grades = {g: grade_counts.get(g, 0) for g in grade_order if g in grade_counts}
                    
                    grade_colors = {'A': '#2ca02c', 'B': '#17becf', 'C': '#ff7f0e', 'D': '#fd7e14', 'F': '#d62728'}
                    
                    fig = px.pie(
                        values=list(sorted_grades.values()),
                        names=list(sorted_grades.keys()),
                        title='Performance Grade Distribution',
                        color=list(sorted_grades.keys()),
                        color_discrete_map=grade_colors
                    )
                    fig.update_traces(
                        textposition='inside', 
                        textinfo='percent+label',
                        textfont_size=12
                    )
                    fig.update_layout(
                        height=350, 
                        margin=dict(l=20, r=20, t=50, b=20),
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
                    )
                    charts['performance_grades'] = json.dumps(fig, cls=PlotlyJSONEncoder)
                
                # Method Performance Comparison
                method_perf = test_results.get('method_performance', {})
                if method_perf and len(method_perf) > 0:
                    methods = list(method_perf.keys())
                    avg_times = [max(0, method_perf[m].get('avg_response_time', 0)) for m in methods]
                    success_rates = [max(0, min(100, method_perf[m].get('success_rate', 0))) for m in methods]
                    
                    # Only create chart if we have valid data
                    if any(t > 0 for t in avg_times) and any(r > 0 for r in success_rates):
                        fig = px.scatter(
                            x=avg_times, y=success_rates, 
                            text=methods,
                            title='HTTP Method Performance Analysis',
                            labels={'x': 'Average Response Time (ms)', 'y': 'Success Rate (%)'},
                            size=[20] * len(methods),  # Fixed size for all points
                            color=success_rates,
                            color_continuous_scale='RdYlGn'
                        )
                        
                        fig.update_traces(
                            textposition="top center", 
                            marker=dict(size=15, line=dict(width=2, color='white'))
                        )
                        
                        fig.update_layout(
                            height=400, 
                            margin=dict(l=60, r=40, t=60, b=50),
                            xaxis=dict(title="Average Response Time (ms)", range=[0, max(avg_times) * 1.1]),
                            yaxis=dict(title="Success Rate (%)", range=[0, 105])
                        )
                        charts['method_performance'] = json.dumps(fig, cls=PlotlyJSONEncoder)
            
            # Status Code Distribution
            status_codes = test_results.get('status_code_distribution', {})
            if status_codes:
                # Color code by status type
                status_colors = {}
                for code in status_codes.keys():
                    if str(code).startswith('2'):
                        status_colors[f"HTTP {code}"] = '#2ca02c'  # Green for success
                    elif str(code).startswith('3'):
                        status_colors[f"HTTP {code}"] = '#17becf'  # Blue for redirect
                    elif str(code).startswith('4'):
                        status_colors[f"HTTP {code}"] = '#ff7f0e'  # Orange for client error
                    elif str(code).startswith('5'):
                        status_colors[f"HTTP {code}"] = '#d62728'  # Red for server error
                    else:
                        status_colors[f"HTTP {code}"] = '#7f7f7f'  # Gray for others
                
                fig = px.pie(
                    values=list(status_codes.values()),
                    names=[f"HTTP {k}" for k in status_codes.keys()],
                    title='HTTP Status Code Distribution',
                    color_discrete_map=status_colors
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400, margin=dict(l=40, r=40, t=60, b=40))
                charts['status_codes'] = json.dumps(fig, cls=PlotlyJSONEncoder)
            
            # API Reliability Gauge
            reliability_score = max(0, min(100, test_results.get('reliability_score', 0)))
            if reliability_score > 0:
                remaining = 100 - reliability_score
                
                # Choose color based on score
                if reliability_score >= 80:
                    color = '#2ca02c'  # Green
                elif reliability_score >= 60:
                    color = '#ff7f0e'  # Orange
                else:
                    color = '#d62728'  # Red
                
                fig = px.pie(
                    values=[reliability_score, remaining],
                    names=['Reliable', 'Issues'],
                    title='API Reliability',
                    color_discrete_sequence=[color, '#e9ecef'],
                    hole=0.6
                )
                
                fig.update_traces(
                    textposition='inside', 
                    textinfo='none',
                    hovertemplate='%{label}: %{value}%<extra></extra>'
                )
                
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=50, b=20),
                    showlegend=False,
                    annotations=[
                        dict(
                            text=f'{reliability_score}%',
                            x=0.5, y=0.5,
                            font_size=28,
                            font_color=color,
                            showarrow=False
                        )
                    ]
                )
                charts['reliability_gauge'] = json.dumps(fig, cls=PlotlyJSONEncoder)

            # Performance Distribution Histogram
            if len(valid_endpoints) > 5:
                times = [ep.get('response_time', 0) for ep in valid_endpoints if ep.get('response_time', 0) > 0]
                if times:
                    fig_hist = px.histogram(
                        x=times,
                        nbins=min(10, len(times)//2),
                        title='Response Time Distribution',
                        labels={'x': 'Response Time (ms)', 'y': 'Number of Endpoints'},
                        color_discrete_sequence=['#17becf']
                    )
                    
                    # Add statistics annotations
                    avg_time = sum(times) / len(times)
                    median_time = sorted(times)[len(times)//2]
                    
                    fig_hist.add_vline(
                        x=avg_time, line_dash="dash", line_color="#ff7f0e",
                        annotation_text=f"Avg: {avg_time:.0f}ms"
                    )
                    fig_hist.add_vline(
                        x=median_time, line_dash="dot", line_color="#2ca02c",
                        annotation_text=f"Median: {median_time:.0f}ms"
                    )
                    
                    fig_hist.update_layout(
                        height=350,
                        margin=dict(l=50, r=40, t=60, b=50),
                        showlegend=False,
                        bargap=0.1
                    )
                    
                    charts['response_time_distribution'] = json.dumps(fig_hist, cls=PlotlyJSONEncoder)

        except Exception as e:
            logging.exception("API chart generation failed")

        return charts

    def _generate_simple_report_content(self, data, report_type):
        return f"""
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

    def _generate_simple_report(self, data, filename, report_type):
        html_content = self._generate_simple_report_content(data, report_type)
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
