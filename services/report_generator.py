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
try:
    import numpy as np
except ImportError:
    # Fallback for numpy functions if not available
    class NumpyFallback:
        @staticmethod
        def log10(x):
            import math
            return math.log10(x)
    np = NumpyFallback()
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
                # Enhanced Response Time Chart with improved visualization and accuracy
                if len(valid_endpoints) > 0:
                    # Prepare data with enhanced accuracy metrics
                    endpoint_data = []
                    for ep in valid_endpoints:
                        method = ep.get('method', 'GET')
                        endpoint = ep.get('endpoint', '')[:35]  # Increased length for better readability
                        time_ms = max(0, ep.get('response_time', 0))
                        status = ep.get('status_code', 0)
                        success = ep.get('success', False)
                        response_size = ep.get('response_size', 0)
                        
                        # Enhanced performance categorization with more granular thresholds
                        if time_ms < 100:
                            perf_category = 'Excellent (<100ms)'
                            color = '#00C851'  # Bright green
                            score = 100
                        elif time_ms < 200:
                            perf_category = 'Very Good (100-200ms)'
                            color = '#2ca02c'  # Green
                            score = 90
                        elif time_ms < 500:
                            perf_category = 'Good (200-500ms)'
                            color = '#17becf'  # Light blue
                            score = 75
                        elif time_ms < 1000:
                            perf_category = 'Fair (500ms-1s)'
                            color = '#ff7f0e'  # Orange
                            score = 60
                        elif time_ms < 2000:
                            perf_category = 'Slow (1-2s)'
                            color = '#fd7e14'  # Dark orange
                            score = 40
                        elif time_ms < 5000:
                            perf_category = 'Very Slow (2-5s)'
                            color = '#dc3545'  # Red
                            score = 20
                        else:
                            perf_category = 'Critical (>5s)'
                            color = '#8B0000'  # Dark red
                            score = 10
                        
                        # Calculate throughput estimate (requests per second)
                        throughput = 1000 / time_ms if time_ms > 0 else 0
                        
                        endpoint_data.append({
                            'name': f"{method} {endpoint}",
                            'time': time_ms,
                            'method': method,
                            'endpoint': endpoint,
                            'status': status,
                            'success': success,
                            'category': perf_category,
                            'color': color,
                            'score': score,
                            'response_size': response_size,
                            'throughput': throughput
                        })
                    
                    # Sort by response time for better visualization
                    endpoint_data.sort(key=lambda x: x['time'])
                    
                    names = [d['name'] for d in endpoint_data]
                    times = [d['time'] for d in endpoint_data]
                    categories = [d['category'] for d in endpoint_data]
                    
                    # Enhanced hover text with comprehensive metrics
                    hover_text = [
                        f"<b>{d['method']} {d['endpoint']}</b><br>" +
                        f"Response Time: {d['time']:,.1f}ms<br>" +
                        f"Performance Score: {d['score']}/100<br>" +
                        f"Throughput: {d['throughput']:.1f} req/s<br>" +
                        f"Status Code: {d['status']}<br>" +
                        f"Response Size: {d['response_size']:,} bytes<br>" +
                        f"Category: {d['category']}<br>" +
                        f"Success: {'✅ Yes' if d['success'] else '❌ No'}"
                        for d in endpoint_data
                    ]
                    
                    # Create enhanced bar chart with better color mapping
                    fig = px.bar(
                        x=names, y=times,
                        title='📊 API Response Time Analysis - Performance Breakdown',
                        labels={'x': 'API Endpoints', 'y': 'Response Time (milliseconds)'},
                        color=categories,
                        color_discrete_map={
                            'Excellent (<100ms)': '#00C851',
                            'Very Good (100-200ms)': '#2ca02c',
                            'Good (200-500ms)': '#17becf', 
                            'Fair (500ms-1s)': '#ff7f0e',
                            'Slow (1-2s)': '#fd7e14',
                            'Very Slow (2-5s)': '#dc3545',
                            'Critical (>5s)': '#8B0000'
                        },
                        hover_name=hover_text
                    )
                    
                    # Add enhanced performance threshold zones with better visibility
                    fig.add_hrect(y0=0, y1=100, fillcolor="rgba(0,200,81,0.15)", 
                                  annotation_text="🟢 Excellent Zone (<100ms)", annotation_position="top left",
                                  line_width=0)
                    fig.add_hrect(y0=100, y1=200, fillcolor="rgba(44,160,44,0.12)", 
                                  annotation_text="🟢 Very Good Zone (100-200ms)", annotation_position="top left",
                                  line_width=0)
                    fig.add_hrect(y0=200, y1=500, fillcolor="rgba(23,190,207,0.1)", 
                                  annotation_text="🔵 Good Zone (200-500ms)", annotation_position="top left",
                                  line_width=0)
                    fig.add_hrect(y0=500, y1=1000, fillcolor="rgba(255,127,14,0.1)", 
                                  annotation_text="🟡 Fair Zone (500ms-1s)", annotation_position="top left",
                                  line_width=0)
                    fig.add_hrect(y0=1000, y1=2000, fillcolor="rgba(253,126,20,0.1)", 
                                  annotation_text="🟠 Slow Zone (1-2s)", annotation_position="top left",
                                  line_width=0)
                    fig.add_hrect(y0=2000, y1=max(times) * 1.1 if times else 5000, 
                                  fillcolor="rgba(220,53,69,0.1)", 
                                  annotation_text="🔴 Critical Zone (>2s)", annotation_position="top left",
                                  line_width=0)
                    
                    # Add enhanced threshold lines with better annotations
                    fig.add_hline(y=100, line_dash="dot", line_color="#00C851", line_width=2,
                                  annotation_text="100ms (Excellent)", annotation_position="right")
                    fig.add_hline(y=200, line_dash="dash", line_color="#2ca02c", line_width=2,
                                  annotation_text="200ms (Very Good)", annotation_position="right")
                    fig.add_hline(y=500, line_dash="dash", line_color="#17becf", line_width=2,
                                  annotation_text="500ms (Good)", annotation_position="right")
                    fig.add_hline(y=1000, line_dash="dash", line_color="#ff7f0e", line_width=2,
                                  annotation_text="1s (Fair)", annotation_position="right")
                    fig.add_hline(y=2000, line_dash="dash", line_color="#fd7e14", line_width=2,
                                  annotation_text="2s (Slow)", annotation_position="right")
                    
                    # Calculate enhanced statistics
                    avg_time = sum(times) / len(times) if times else 0
                    median_time = sorted(times)[len(times)//2] if times else 0
                    p95_time = sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else (times[0] if times else 0)
                    p99_time = sorted(times)[int(len(times) * 0.99)] if len(times) > 1 else (times[0] if times else 0)
                    min_time = min(times) if times else 0
                    max_time = max(times) if times else 0
                    
                    # Calculate performance distribution
                    excellent_count = sum(1 for d in endpoint_data if d['score'] >= 90)
                    good_count = sum(1 for d in endpoint_data if 60 <= d['score'] < 90)
                    poor_count = sum(1 for d in endpoint_data if d['score'] < 60)
                    
                    fig.update_xaxes(
                        tickangle=-45,
                        title="API Endpoints (sorted by response time)",
                        tickfont=dict(size=10)
                    )
                    fig.update_yaxes(
                        title="Response Time (milliseconds)",
                        type="linear",
                        gridcolor="rgba(128,128,128,0.2)"
                    )
                    
                    fig.update_layout(
                        height=600,  # Increased height for better visibility
                        margin=dict(l=80, r=140, t=100, b=160), 
                        showlegend=True,
                        legend=dict(
                            orientation="v",
                            yanchor="top",
                            y=1,
                            xanchor="left",
                            x=1.02,
                            font=dict(size=10)
                        ),
                        annotations=[
                            # Main statistics box
                            dict(
                                x=0.02, y=0.98, xref='paper', yref='paper',
                                text=f"📈 <b>Performance Statistics</b><br>" +
                                     f"Average: {avg_time:.1f}ms | Median: {median_time:.1f}ms<br>" +
                                     f"P95: {p95_time:.1f}ms | P99: {p99_time:.1f}ms<br>" +
                                     f"Range: {min_time:.1f}ms - {max_time:.1f}ms",
                                showarrow=False, 
                                font=dict(size=11, color="#333"),
                                bgcolor="rgba(255,255,255,0.9)",
                                bordercolor="#ddd",
                                borderwidth=1,
                                align="left"
                            ),
                            # Performance distribution box
                            dict(
                                x=0.02, y=0.85, xref='paper', yref='paper',
                                text=f"🎯 <b>Performance Distribution</b><br>" +
                                     f"Excellent/Very Good: {excellent_count} ({excellent_count/len(endpoint_data)*100:.1f}%)<br>" +
                                     f"Good/Fair: {good_count} ({good_count/len(endpoint_data)*100:.1f}%)<br>" +
                                     f"Slow/Critical: {poor_count} ({poor_count/len(endpoint_data)*100:.1f}%)",
                                showarrow=False, 
                                font=dict(size=10, color="#333"),
                                bgcolor="rgba(248,249,250,0.9)",
                                bordercolor="#ddd",
                                borderwidth=1,
                                align="left"
                            )
                        ],
                        hovermode='closest',
                        plot_bgcolor='rgba(248,249,250,0.8)'
                    )
                    
                    charts['response_times'] = json.dumps(fig, cls=PlotlyJSONEncoder)
                
                # Enhanced Performance Grades Distribution with detailed metrics
                grades = [ep.get('performance_grade', 'F') for ep in valid_endpoints if ep.get('performance_grade')]
                if grades:
                    grade_counts = {}
                    grade_times = {}  # Track average times per grade
                    
                    for i, grade in enumerate(grades):
                        grade_counts[grade] = grade_counts.get(grade, 0) + 1
                        if grade not in grade_times:
                            grade_times[grade] = []
                        grade_times[grade].append(valid_endpoints[i].get('response_time', 0))
                    
                    # Sort grades in logical order with enhanced categories
                    grade_order = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
                    sorted_grades = {g: grade_counts.get(g, 0) for g in grade_order if g in grade_counts}
                    
                    # Enhanced color scheme with more granular grades
                    grade_colors = {
                        'A+': '#00C851', 'A': '#2ca02c', 'A-': '#4CAF50',
                        'B+': '#17becf', 'B': '#2196F3', 'B-': '#03A9F4',
                        'C+': '#ff7f0e', 'C': '#FF9800', 'C-': '#FFC107',
                        'D': '#fd7e14', 'F': '#d62728'
                    }
                    
                    # Calculate average response times for each grade
                    grade_avg_times = {}
                    for grade, times in grade_times.items():
                        grade_avg_times[grade] = sum(times) / len(times) if times else 0
                    
                    # Create enhanced pie chart
                    fig = px.pie(
                        values=list(sorted_grades.values()),
                        names=list(sorted_grades.keys()),
                        title='🏆 Performance Grade Distribution - Quality Analysis',
                        color=list(sorted_grades.keys()),
                        color_discrete_map=grade_colors,
                        hover_data={'values': list(sorted_grades.values())}
                    )
                    
                    # Enhanced hover template with detailed information
                    hover_template = [
                        f"<b>Grade {grade}</b><br>" +
                        f"Count: {count} endpoints<br>" +
                        f"Percentage: %{percent}<br>" +
                        f"Avg Response Time: {grade_avg_times.get(grade, 0):.1f}ms<br>" +
                        f"<extra></extra>"
                        for grade, count in sorted_grades.items()
                        for percent in [f"{count/sum(sorted_grades.values())*100:.1f}"]
                    ]
                    
                    fig.update_traces(
                        textposition='inside', 
                        textinfo='percent+label',
                        textfont_size=12,
                        textfont_color='white',
                        hovertemplate='<b>Grade %{label}</b><br>' +
                                     'Count: %{value} endpoints<br>' +
                                     'Percentage: %{percent}<br>' +
                                     '<extra></extra>',
                        marker=dict(line=dict(color='white', width=2))
                    )
                    
                    # Calculate performance insights
                    total_endpoints = sum(sorted_grades.values())
                    excellent_grades = sum(sorted_grades.get(g, 0) for g in ['A+', 'A', 'A-'])
                    good_grades = sum(sorted_grades.get(g, 0) for g in ['B+', 'B', 'B-'])
                    poor_grades = sum(sorted_grades.get(g, 0) for g in ['C+', 'C', 'C-', 'D', 'F'])
                    
                    fig.update_layout(
                        height=450, 
                        margin=dict(l=40, r=40, t=80, b=100),
                        showlegend=True,
                        legend=dict(
                            orientation="h", 
                            yanchor="bottom", 
                            y=-0.3,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=10)
                        ),
                        annotations=[
                            dict(
                                text=f"📊 <b>Performance Summary</b><br>" +
                                     f"🟢 Excellent (A grades): {excellent_grades} ({excellent_grades/total_endpoints*100:.1f}%)<br>" +
                                     f"🔵 Good (B grades): {good_grades} ({good_grades/total_endpoints*100:.1f}%)<br>" +
                                     f"🟡 Needs Improvement: {poor_grades} ({poor_grades/total_endpoints*100:.1f}%)",
                                x=0.5, y=-0.15, xref='paper', yref='paper',
                                showarrow=False,
                                font=dict(size=11, color="#333"),
                                bgcolor="rgba(248,249,250,0.9)",
                                bordercolor="#ddd",
                                borderwidth=1,
                                align="center"
                            )
                        ],
                        plot_bgcolor='rgba(248,249,250,0.8)'
                    )
                    charts['performance_grades'] = json.dumps(fig, cls=PlotlyJSONEncoder)
                
                # Enhanced Method Performance Comparison with comprehensive metrics
                method_perf = test_results.get('method_performance', {})
                if method_perf and len(method_perf) > 0:
                    methods = list(method_perf.keys())
                    avg_times = [max(0, method_perf[m].get('avg_response_time', 0)) for m in methods]
                    success_rates = [max(0, min(100, method_perf[m].get('success_rate', 0))) for m in methods]
                    total_requests = [method_perf[m].get('total', 0) for m in methods]
                    
                    # Only create chart if we have valid data
                    if any(t > 0 for t in avg_times) and any(r > 0 for r in success_rates):
                        # Calculate performance scores for each method
                        performance_scores = []
                        for i, method in enumerate(methods):
                            # Score based on response time and success rate
                            time_score = max(0, 100 - (avg_times[i] / 10))  # Penalty for slow responses
                            success_score = success_rates[i]
                            combined_score = (time_score * 0.4 + success_score * 0.6)  # Weight success rate more
                            performance_scores.append(combined_score)
                        
                        # Create enhanced scatter plot
                        fig = px.scatter(
                            x=avg_times, y=success_rates, 
                            text=methods,
                            title='🔍 HTTP Method Performance Analysis - Speed vs Reliability',
                            labels={'x': 'Average Response Time (ms)', 'y': 'Success Rate (%)'},
                            size=total_requests,  # Size based on number of requests
                            color=performance_scores,
                            color_continuous_scale='RdYlGn',
                            size_max=30,
                            hover_data={'x': avg_times, 'y': success_rates}
                        )
                        
                        # Enhanced hover template
                        hover_template = [
                            f"<b>{method} Method</b><br>" +
                            f"Avg Response Time: {avg_times[i]:.1f}ms<br>" +
                            f"Success Rate: {success_rates[i]:.1f}%<br>" +
                            f"Total Requests: {total_requests[i]}<br>" +
                            f"Performance Score: {performance_scores[i]:.1f}/100<br>" +
                            f"<extra></extra>"
                            for i, method in enumerate(methods)
                        ]
                        
                        fig.update_traces(
                            textposition="top center", 
                            marker=dict(
                                line=dict(width=2, color='white'),
                                opacity=0.8
                            ),
                            hovertemplate='<b>%{text} Method</b><br>' +
                                         'Response Time: %{x:.1f}ms<br>' +
                                         'Success Rate: %{y:.1f}%<br>' +
                                         '<extra></extra>'
                        )
                        
                        # Add performance quadrants
                        avg_response_time = sum(avg_times) / len(avg_times)
                        avg_success_rate = sum(success_rates) / len(success_rates)
                        
                        # Add quadrant lines
                        fig.add_hline(y=avg_success_rate, line_dash="dot", line_color="gray", opacity=0.5)
                        fig.add_vline(x=avg_response_time, line_dash="dot", line_color="gray", opacity=0.5)
                        
                        # Add performance zones
                        fig.add_shape(
                            type="rect",
                            x0=0, y0=avg_success_rate, x1=avg_response_time, y1=105,
                            fillcolor="rgba(40,167,69,0.1)",
                            line=dict(width=0),
                            layer="below"
                        )
                        
                        # Calculate method rankings
                        method_rankings = sorted(
                            [(methods[i], performance_scores[i], avg_times[i], success_rates[i]) 
                             for i in range(len(methods))], 
                            key=lambda x: x[1], reverse=True
                        )
                        
                        best_method = method_rankings[0] if method_rankings else None
                        worst_method = method_rankings[-1] if method_rankings else None
                        
                        fig.update_layout(
                            height=500, 
                            margin=dict(l=80, r=120, t=100, b=80),
                            xaxis=dict(
                                title="Average Response Time (milliseconds)", 
                                range=[0, max(avg_times) * 1.15],
                                gridcolor="rgba(128,128,128,0.2)"
                            ),
                            yaxis=dict(
                                title="Success Rate (%)", 
                                range=[min(0, min(success_rates) - 5), 105],
                                gridcolor="rgba(128,128,128,0.2)"
                            ),
                            coloraxis_colorbar=dict(
                                title="Performance<br>Score",
                                titleside="right"
                            ),
                            plot_bgcolor='rgba(248,249,250,0.8)',
                            annotations=[
                                # Performance insights box
                                dict(
                                    x=0.98, y=0.02, xref='paper', yref='paper',
                                    text=f"🏆 <b>Method Performance Ranking</b><br>" +
                                         (f"🥇 Best: {best_method[0]} (Score: {best_method[1]:.1f})<br>" +
                                          f"   {best_method[2]:.1f}ms, {best_method[3]:.1f}% success<br>" if best_method else "") +
                                         (f"🥉 Needs Improvement: {worst_method[0]}<br>" +
                                          f"   {worst_method[2]:.1f}ms, {worst_method[3]:.1f}% success" if worst_method else ""),
                                    showarrow=False,
                                    font=dict(size=10, color="#333"),
                                    bgcolor="rgba(255,255,255,0.95)",
                                    bordercolor="#ddd",
                                    borderwidth=1,
                                    align="left",
                                    xanchor="right",
                                    yanchor="bottom"
                                ),
                                # Quadrant labels
                                dict(
                                    x=avg_response_time/2, y=(avg_success_rate + 100)/2,
                                    text="🟢 Optimal Zone<br>(Fast & Reliable)",
                                    showarrow=False,
                                    font=dict(size=10, color="#28a745"),
                                    bgcolor="rgba(40,167,69,0.1)",
                                    bordercolor="#28a745",
                                    borderwidth=1
                                )
                            ]
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

            # Enhanced Performance Distribution Histogram with detailed analysis
            if len(valid_endpoints) > 3:  # Lowered threshold for better coverage
                times = [ep.get('response_time', 0) for ep in valid_endpoints if ep.get('response_time', 0) > 0]
                if times:
                    # Calculate optimal number of bins using Sturges' rule
                    optimal_bins = max(5, min(20, int(1 + 3.322 * np.log10(len(times)))))
                    
                    # Create histogram with enhanced styling
                    fig_hist = px.histogram(
                        x=times,
                        nbins=optimal_bins,
                        title='📈 Response Time Distribution - Performance Pattern Analysis',
                        labels={'x': 'Response Time (milliseconds)', 'y': 'Number of Endpoints'},
                        color_discrete_sequence=['#17becf'],
                        opacity=0.8
                    )
                    
                    # Calculate comprehensive statistics
                    avg_time = sum(times) / len(times)
                    median_time = sorted(times)[len(times)//2]
                    std_dev = (sum((x - avg_time) ** 2 for x in times) / len(times)) ** 0.5
                    min_time = min(times)
                    max_time = max(times)
                    
                    # Calculate percentiles
                    sorted_times = sorted(times)
                    p25 = sorted_times[int(len(times) * 0.25)] if len(times) > 3 else min_time
                    p75 = sorted_times[int(len(times) * 0.75)] if len(times) > 3 else max_time
                    p90 = sorted_times[int(len(times) * 0.90)] if len(times) > 9 else max_time
                    p95 = sorted_times[int(len(times) * 0.95)] if len(times) > 19 else max_time
                    p99 = sorted_times[int(len(times) * 0.99)] if len(times) > 99 else max_time
                    
                    # Add enhanced statistical lines
                    fig_hist.add_vline(
                        x=avg_time, line_dash="dash", line_color="#ff7f0e", line_width=3,
                        annotation_text=f"📊 Average: {avg_time:.1f}ms",
                        annotation_position="top"
                    )
                    fig_hist.add_vline(
                        x=median_time, line_dash="dot", line_color="#2ca02c", line_width=3,
                        annotation_text=f"📍 Median: {median_time:.1f}ms",
                        annotation_position="top"
                    )
                    fig_hist.add_vline(
                        x=p95, line_dash="dashdot", line_color="#d62728", line_width=2,
                        annotation_text=f"⚠️ P95: {p95:.1f}ms",
                        annotation_position="top"
                    )
                    
                    # Add performance zones as background rectangles
                    fig_hist.add_vrect(
                        x0=0, x1=200, fillcolor="rgba(44,160,44,0.1)",
                        annotation_text="Excellent Zone", annotation_position="top left",
                        line_width=0
                    )
                    fig_hist.add_vrect(
                        x0=200, x1=1000, fillcolor="rgba(255,193,7,0.1)",
                        annotation_text="Acceptable Zone", annotation_position="top left",
                        line_width=0
                    )
                    fig_hist.add_vrect(
                        x0=1000, x1=max(times) * 1.1, fillcolor="rgba(220,53,69,0.1)",
                        annotation_text="Critical Zone", annotation_position="top left",
                        line_width=0
                    )
                    
                    # Calculate distribution insights
                    fast_endpoints = sum(1 for t in times if t < 200)
                    medium_endpoints = sum(1 for t in times if 200 <= t < 1000)
                    slow_endpoints = sum(1 for t in times if t >= 1000)
                    
                    fig_hist.update_layout(
                        height=450,
                        margin=dict(l=60, r=60, t=100, b=120),
                        showlegend=False,
                        bargap=0.05,
                        plot_bgcolor='rgba(248,249,250,0.8)',
                        annotations=[
                            # Comprehensive statistics box
                            dict(
                                x=0.98, y=0.98, xref='paper', yref='paper',
                                text=f"📊 <b>Statistical Analysis</b><br>" +
                                     f"Mean: {avg_time:.1f}ms ± {std_dev:.1f}<br>" +
                                     f"Median: {median_time:.1f}ms<br>" +
                                     f"Range: {min_time:.1f} - {max_time:.1f}ms<br>" +
                                     f"P25: {p25:.1f}ms | P75: {p75:.1f}ms<br>" +
                                     f"P90: {p90:.1f}ms | P95: {p95:.1f}ms<br>" +
                                     f"P99: {p99:.1f}ms",
                                showarrow=False,
                                font=dict(size=10, color="#333"),
                                bgcolor="rgba(255,255,255,0.95)",
                                bordercolor="#ddd",
                                borderwidth=1,
                                align="left",
                                xanchor="right",
                                yanchor="top"
                            ),
                            # Performance distribution summary
                            dict(
                                x=0.02, y=0.98, xref='paper', yref='paper',
                                text=f"🎯 <b>Performance Distribution</b><br>" +
                                     f"🟢 Fast (<200ms): {fast_endpoints} ({fast_endpoints/len(times)*100:.1f}%)<br>" +
                                     f"🟡 Medium (200ms-1s): {medium_endpoints} ({medium_endpoints/len(times)*100:.1f}%)<br>" +
                                     f"🔴 Slow (>1s): {slow_endpoints} ({slow_endpoints/len(times)*100:.1f}%)<br>" +
                                     f"Total Endpoints: {len(times)}",
                                showarrow=False,
                                font=dict(size=10, color="#333"),
                                bgcolor="rgba(248,249,250,0.95)",
                                bordercolor="#ddd",
                                borderwidth=1,
                                align="left",
                                xanchor="left",
                                yanchor="top"
                            )
                        ]
                    )
                    
                    fig_hist.update_xaxes(
                        title="Response Time (milliseconds)",
                        gridcolor="rgba(128,128,128,0.2)"
                    )
                    fig_hist.update_yaxes(
                        title="Number of Endpoints",
                        gridcolor="rgba(128,128,128,0.2)"
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
