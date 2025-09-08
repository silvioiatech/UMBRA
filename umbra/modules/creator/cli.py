#!/usr/bin/env python3
"""
Creator v1 (CRT4) - Command Line Interface
Administrative and management utilities for Creator v1 system
"""

import asyncio
import click
import json
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import yaml

# Import Creator v1 components
from umbra.core.config import UmbraConfig
from umbra.ai.agent import UmbraAIAgent
from umbra.modules.creator import create_creator_system, CreatorV1System
from umbra.modules.creator.errors import CreatorError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class CreatorCLI:
    """Creator v1 Command Line Interface"""
    
    def __init__(self):
        self.config = None
        self.creator_system = None
        self.config_file = None
    
    async def load_system(self, config_file: Optional[str] = None, debug: bool = False):
        """Load and initialize Creator v1 system"""
        try:
            if config_file:
                self.config_file = Path(config_file)
                if self.config_file.exists():
                    if self.config_file.suffix in ['.yaml', '.yml']:
                        with open(self.config_file, 'r') as f:
                            config_data = yaml.safe_load(f)
                    else:
                        with open(self.config_file, 'r') as f:
                            config_data = json.load(f)
                    
                    self.config = UmbraConfig(config_data)
                else:
                    click.echo(f"❌ Config file not found: {config_file}")
                    return False
            else:
                # Use default configuration
                self.config = UmbraConfig({
                    "CREATOR_V1_ENABLED": True,
                    "CREATOR_V1_DEBUG": debug,
                    "CREATOR_SECURITY_ENABLED": False,  # Disable for CLI
                    "CREATOR_RATE_LIMITING_ENABLED": False,
                })
            
            # Create AI agent
            ai_agent = UmbraAIAgent(self.config)
            
            # Initialize Creator system
            self.creator_system = await create_creator_system(self.config, ai_agent)
            
            return True
            
        except Exception as e:
            click.echo(f"❌ Failed to load Creator v1 system: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup system resources"""
        if self.creator_system:
            await self.creator_system.shutdown()

# CLI Context for async support
class AsyncContext:
    def __init__(self):
        self.cli = CreatorCLI()
    
    async def __aenter__(self):
        return self.cli
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cli.cleanup()

# Main CLI group
@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, config, debug):
    """Creator v1 (CRT4) Command Line Interface"""
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = config
    ctx.obj['debug'] = debug

# System management commands
@cli.group()
def system():
    """System management commands"""
    pass

@system.command()
@click.pass_context
def status(ctx):
    """Get system status"""
    async def _status():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                status_data = creator_cli.creator_system.get_system_status()
                
                click.echo("📊 Creator v1 System Status")
                click.echo(f"Version: {status_data['version']}")
                click.echo(f"Enabled: {status_data['enabled']}")
                click.echo(f"Health: {status_data['health_status']}")
                
                # Component status
                components = status_data.get('components_status', {})
                working = sum(1 for status in components.values() if status)
                total = len(components)
                
                click.echo(f"Components: {working}/{total} operational")
                
                if ctx.obj['debug']:
                    click.echo("\n📋 Component Details:")
                    for name, status in components.items():
                        status_icon = "✅" if status else "❌"
                        click.echo(f"  {status_icon} {name}")
                
                # Performance metrics
                performance = status_data.get('performance_metrics', {})
                if performance:
                    click.echo(f"\n⚡ Performance: {len(performance)} metrics available")
                
                # Security status
                security = status_data.get('security_status', {})
                if security:
                    click.echo(f"🔒 Security: {'Enabled' if security.get('enabled') else 'Disabled'}")
    
    asyncio.run(_status())

@system.command()
@click.pass_context
def health(ctx):
    """Perform comprehensive health check"""
    async def _health():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                click.echo("🏥 Running health check...")
                
                health_report = await creator_cli.creator_system.health_check()
                
                overall_status = health_report.get('overall_health', {})
                click.echo(f"Overall Health: {overall_status.get('status', 'unknown')}")
                click.echo(f"Message: {overall_status.get('message', 'No message')}")
                
                # Critical issues
                critical_issues = overall_status.get('critical_issues', [])
                if critical_issues:
                    click.echo("\n🚨 Critical Issues:")
                    for issue in critical_issues:
                        click.echo(f"  - {issue['check']}: {issue['message']}")
                
                # Warnings
                warning_issues = overall_status.get('warning_issues', [])
                if warning_issues:
                    click.echo("\n⚠️  Warnings:")
                    for issue in warning_issues:
                        click.echo(f"  - {issue['check']}: {issue['message']}")
                
                # System summary
                system_summary = health_report.get('system_summary', {})
                if system_summary:
                    click.echo("\n💻 System Resources:")
                    click.echo(f"  CPU: {system_summary.get('cpu_percent', 0):.1f}%")
                    click.echo(f"  Memory: {system_summary.get('memory_percent', 0):.1f}%")
                    click.echo(f"  Disk: {system_summary.get('disk_percent', 0):.1f}%")
                    click.echo(f"  Uptime: {system_summary.get('uptime_hours', 0):.1f} hours")
    
    asyncio.run(_health())

@system.command()
@click.option('--format', '-f', type=click.Choice(['json', 'yaml', 'table']), default='table')
@click.pass_context
def metrics(ctx, format):
    """Display system metrics"""
    async def _metrics():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                # Get metrics from various components
                analytics = creator_cli.creator_system.get_component("analytics")
                advanced_metrics = creator_cli.creator_system.get_component("advanced_metrics")
                cache = creator_cli.creator_system.get_component("cache")
                
                metrics_data = {}
                
                if analytics:
                    metrics_data['analytics'] = {
                        'daily_stats': analytics.get_daily_stats(),
                        'action_stats': analytics.get_action_stats()
                    }
                
                if advanced_metrics:
                    metrics_data['advanced_metrics'] = advanced_metrics.get_metrics_summary()
                
                if cache:
                    metrics_data['cache'] = cache.get_stats()
                
                if format == 'json':
                    click.echo(json.dumps(metrics_data, indent=2, default=str))
                elif format == 'yaml':
                    click.echo(yaml.dump(metrics_data, default_flow_style=False))
                else:
                    # Table format
                    click.echo("📊 System Metrics")
                    for component, data in metrics_data.items():
                        click.echo(f"\n{component.upper()}:")
                        if isinstance(data, dict):
                            for key, value in data.items():
                                if isinstance(value, dict):
                                    click.echo(f"  {key}:")
                                    for subkey, subvalue in value.items():
                                        click.echo(f"    {subkey}: {subvalue}")
                                else:
                                    click.echo(f"  {key}: {value}")
    
    asyncio.run(_metrics())

# Content generation commands
@cli.group()
def content():
    """Content generation commands"""
    pass

@content.command()
@click.argument('topic')
@click.option('--platform', '-p', help='Target platform')
@click.option('--tone', '-t', help='Content tone')
@click.option('--output', '-o', help='Output file')
@click.pass_context
def generate(ctx, topic, platform, tone, output):
    """Generate content for a topic"""
    async def _generate():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                click.echo(f"🎯 Generating content for: {topic}")
                
                request = {
                    "action": "generate_post",
                    "topic": topic,
                    "platform": platform,
                    "tone": tone
                }
                
                try:
                    result = await creator_cli.creator_system.generate_content(
                        request, user_id="cli_user"
                    )
                    
                    content = result.get('content', 'No content generated')
                    
                    if output:
                        Path(output).write_text(content)
                        click.echo(f"✅ Content saved to: {output}")
                    else:
                        click.echo("📝 Generated Content:")
                        click.echo(content)
                    
                    # Show metadata
                    if ctx.obj['debug']:
                        click.echo(f"\n📊 Metadata:")
                        click.echo(f"  Provider: {result.get('provider_used', 'Unknown')}")
                        click.echo(f"  Model: {result.get('model_used', 'Unknown')}")
                        click.echo(f"  Words: {result.get('metadata', {}).get('word_count', 0)}")
                        click.echo(f"  Characters: {result.get('metadata', {}).get('char_count', 0)}")
                
                except CreatorError as e:
                    click.echo(f"❌ Content generation failed: {e}")
    
    asyncio.run(_generate())

@content.command()
@click.argument('topic')
@click.option('--platform', '-p', help='Target platform')
@click.option('--tone', '-t', help='Content tone')
@click.option('--output-dir', '-o', help='Output directory', default='.')
@click.pass_context
def pack(ctx, topic, platform, tone, output_dir):
    """Generate complete content pack"""
    async def _pack():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                click.echo(f"📦 Generating content pack for: {topic}")
                
                request = {
                    "action": "generate_content_pack",
                    "topic": topic,
                    "platform": platform,
                    "tone": tone
                }
                
                try:
                    result = await creator_cli.creator_system.generate_content(
                        request, user_id="cli_user"
                    )
                    
                    pack = result.get('pack', {})
                    
                    # Create output directory
                    output_path = Path(output_dir)
                    output_path.mkdir(exist_ok=True)
                    
                    # Save pack components
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pack_dir = output_path / f"content_pack_{timestamp}"
                    pack_dir.mkdir(exist_ok=True)
                    
                    # Save each component
                    if pack.get('caption'):
                        (pack_dir / "caption.txt").write_text(pack['caption'])
                    
                    if pack.get('cta'):
                        (pack_dir / "cta.txt").write_text(pack['cta'])
                    
                    if pack.get('titles'):
                        (pack_dir / "titles.json").write_text(
                            json.dumps(pack['titles'], indent=2)
                        )
                    
                    if pack.get('hashtags'):
                        (pack_dir / "hashtags.txt").write_text('\n'.join(pack['hashtags']))
                    
                    if pack.get('alt_text'):
                        (pack_dir / "alt_text.txt").write_text(pack['alt_text'])
                    
                    # Save complete pack as JSON
                    (pack_dir / "complete_pack.json").write_text(
                        json.dumps(result, indent=2, default=str)
                    )
                    
                    click.echo(f"✅ Content pack saved to: {pack_dir}")
                    click.echo(f"📊 Generated {len([f for f in pack_dir.iterdir() if f.is_file()])} files")
                
                except CreatorError as e:
                    click.echo(f"❌ Content pack generation failed: {e}")
    
    asyncio.run(_pack())

# Analytics commands
@cli.group()
def analytics():
    """Analytics and reporting commands"""
    pass

@analytics.command()
@click.option('--days', '-d', default=7, help='Number of days to analyze')
@click.option('--format', '-f', type=click.Choice(['json', 'table']), default='table')
@click.pass_context
def usage(ctx, days, format):
    """Show usage analytics"""
    async def _usage():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                analytics_component = creator_cli.creator_system.get_component("analytics")
                
                if analytics_component:
                    daily_stats = analytics_component.get_daily_stats()
                    action_stats = analytics_component.get_action_stats()
                    
                    if format == 'json':
                        click.echo(json.dumps({
                            'daily_stats': daily_stats,
                            'action_stats': action_stats
                        }, indent=2, default=str))
                    else:
                        click.echo(f"📈 Usage Analytics (Last {days} days)")
                        click.echo(f"Total Requests: {daily_stats.get('total_requests', 0)}")
                        click.echo(f"Successful: {daily_stats.get('successful_requests', 0)}")
                        click.echo(f"Failed: {daily_stats.get('failed_requests', 0)}")
                        click.echo(f"Average Response Time: {daily_stats.get('avg_response_time_ms', 0):.0f}ms")
                        
                        if action_stats:
                            click.echo("\n📊 Top Actions:")
                            for action, stats in list(action_stats.items())[:5]:
                                click.echo(f"  {action}: {stats.total_requests} requests")
                else:
                    click.echo("❌ Analytics component not available")
    
    asyncio.run(_usage())

@analytics.command()
@click.option('--metric', '-m', help='Specific metric to export')
@click.option('--format', '-f', type=click.Choice(['json', 'csv']), default='json')
@click.option('--output', '-o', help='Output file')
@click.pass_context
def export(ctx, metric, format, output):
    """Export analytics data"""
    async def _export():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                advanced_metrics = creator_cli.creator_system.get_component("advanced_metrics")
                
                if advanced_metrics:
                    if metric:
                        # Export specific metric
                        values = advanced_metrics.get_metric_values(metric)
                        export_data = [
                            {
                                'timestamp': dp.timestamp,
                                'value': dp.value,
                                'labels': dp.labels
                            } for dp in values
                        ]
                    else:
                        # Export summary
                        export_data = advanced_metrics.get_metrics_summary()
                    
                    if format == 'json':
                        content = json.dumps(export_data, indent=2, default=str)
                    else:  # CSV
                        import csv
                        import io
                        
                        output_io = io.StringIO()
                        if isinstance(export_data, list) and export_data:
                            fieldnames = export_data[0].keys()
                            writer = csv.DictWriter(output_io, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(export_data)
                        content = output_io.getvalue()
                    
                    if output:
                        Path(output).write_text(content)
                        click.echo(f"✅ Data exported to: {output}")
                    else:
                        click.echo(content)
                else:
                    click.echo("❌ Advanced metrics component not available")
    
    asyncio.run(_export())

# Configuration commands
@cli.group()
def config():
    """Configuration management commands"""
    pass

@config.command()
@click.option('--output', '-o', help='Output file')
@click.pass_context
def show(ctx, output):
    """Show current configuration"""
    async def _show():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                dynamic_config = creator_cli.creator_system.get_component("dynamic_config")
                
                if dynamic_config:
                    config_data = dynamic_config.export_config(include_sensitive=False)
                    
                    if output:
                        with open(output, 'w') as f:
                            if output.endswith('.yaml') or output.endswith('.yml'):
                                yaml.dump(config_data, f, default_flow_style=False)
                            else:
                                json.dump(config_data, f, indent=2, default=str)
                        click.echo(f"✅ Configuration exported to: {output}")
                    else:
                        click.echo("⚙️  Current Configuration:")
                        for key, value in sorted(config_data.items()):
                            click.echo(f"  {key}: {value}")
                else:
                    click.echo("❌ Dynamic config component not available")
    
    asyncio.run(_show())

@config.command()
@click.argument('key')
@click.argument('value')
@click.pass_context
def set(ctx, key, value):
    """Set configuration value"""
    async def _set():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                dynamic_config = creator_cli.creator_system.get_component("dynamic_config")
                
                if dynamic_config:
                    # Try to parse value as JSON, fallback to string
                    try:
                        parsed_value = json.loads(value)
                    except json.JSONDecodeError:
                        parsed_value = value
                    
                    success = dynamic_config.set(
                        key, parsed_value, 
                        changed_by="cli", 
                        reason=f"Set via CLI at {datetime.now()}"
                    )
                    
                    if success:
                        click.echo(f"✅ Set {key} = {parsed_value}")
                    else:
                        click.echo(f"❌ Failed to set {key}")
                else:
                    click.echo("❌ Dynamic config component not available")
    
    asyncio.run(_set())

@config.command()
@click.argument('key')
@click.pass_context
def get(ctx, key):
    """Get configuration value"""
    async def _get():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                dynamic_config = creator_cli.creator_system.get_component("dynamic_config")
                
                if dynamic_config:
                    value = dynamic_config.get(key)
                    if value is not None:
                        click.echo(f"{key}: {value}")
                    else:
                        click.echo(f"❌ Configuration key not found: {key}")
                else:
                    click.echo("❌ Dynamic config component not available")
    
    asyncio.run(_get())

# Plugin commands
@cli.group()
def plugins():
    """Plugin management commands"""
    pass

@plugins.command()
@click.pass_context
def list(ctx):
    """List installed plugins"""
    async def _list():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                plugin_manager = creator_cli.creator_system.get_component("plugin_manager")
                
                if plugin_manager:
                    all_plugins = plugin_manager.get_all_plugins_info()
                    active_plugins = plugin_manager.get_active_plugins()
                    
                    click.echo(f"🔌 Installed Plugins ({len(all_plugins)})")
                    
                    for name, info in all_plugins.items():
                        status_icon = "🟢" if name in active_plugins else "🔴"
                        metadata = info.get('metadata', {})
                        
                        click.echo(f"  {status_icon} {name}")
                        click.echo(f"    Version: {metadata.get('version', 'unknown')}")
                        click.echo(f"    Type: {metadata.get('plugin_type', 'unknown')}")
                        click.echo(f"    Status: {info.get('status', 'unknown')}")
                        
                        if info.get('error_message'):
                            click.echo(f"    ❌ Error: {info['error_message']}")
                else:
                    click.echo("❌ Plugin manager not available")
    
    asyncio.run(_list())

@plugins.command()
@click.argument('plugin_name')
@click.pass_context
def activate(ctx, plugin_name):
    """Activate a plugin"""
    async def _activate():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                plugin_manager = creator_cli.creator_system.get_component("plugin_manager")
                
                if plugin_manager:
                    success = await plugin_manager.activate_plugin(plugin_name)
                    if success:
                        click.echo(f"✅ Activated plugin: {plugin_name}")
                    else:
                        click.echo(f"❌ Failed to activate plugin: {plugin_name}")
                else:
                    click.echo("❌ Plugin manager not available")
    
    asyncio.run(_activate())

@plugins.command()
@click.argument('plugin_name')
@click.pass_context
def deactivate(ctx, plugin_name):
    """Deactivate a plugin"""
    async def _deactivate():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                plugin_manager = creator_cli.creator_system.get_component("plugin_manager")
                
                if plugin_manager:
                    success = await plugin_manager.deactivate_plugin(plugin_name)
                    if success:
                        click.echo(f"✅ Deactivated plugin: {plugin_name}")
                    else:
                        click.echo(f"❌ Failed to deactivate plugin: {plugin_name}")
                else:
                    click.echo("❌ Plugin manager not available")
    
    asyncio.run(_deactivate())

# Workflow commands
@cli.group()
def workflow():
    """Workflow management commands"""
    pass

@workflow.command()
@click.pass_context
def list(ctx):
    """List workflows"""
    async def _list():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                workflow_manager = creator_cli.creator_system.get_component("workflow_manager")
                
                if workflow_manager:
                    workflows = workflow_manager.list_workflows()
                    
                    click.echo(f"🔄 Workflows ({len(workflows)})")
                    
                    for workflow in workflows:
                        status_icon = {
                            'created': '⭕',
                            'running': '🔵', 
                            'completed': '✅',
                            'failed': '❌',
                            'cancelled': '⭕'
                        }.get(workflow['status'], '❓')
                        
                        click.echo(f"  {status_icon} {workflow['name']}")
                        click.echo(f"    ID: {workflow['id']}")
                        click.echo(f"    Status: {workflow['status']}")
                        click.echo(f"    Progress: {workflow['progress_percentage']:.1f}%")
                        click.echo(f"    Steps: {workflow['step_count']}")
                        
                        if workflow.get('duration_seconds'):
                            click.echo(f"    Duration: {workflow['duration_seconds']:.1f}s")
                else:
                    click.echo("❌ Workflow manager not available")
    
    asyncio.run(_list())

@workflow.command()
@click.argument('workflow_file')
@click.pass_context
def create(ctx, workflow_file):
    """Create workflow from file"""
    async def _create():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                workflow_manager = creator_cli.creator_system.get_component("workflow_manager")
                
                if workflow_manager:
                    workflow_path = Path(workflow_file)
                    if not workflow_path.exists():
                        click.echo(f"❌ Workflow file not found: {workflow_file}")
                        return
                    
                    with open(workflow_path, 'r') as f:
                        if workflow_path.suffix in ['.yaml', '.yml']:
                            workflow_definition = yaml.safe_load(f)
                        else:
                            workflow_definition = json.load(f)
                    
                    workflow_id = await workflow_manager.create_custom_workflow(
                        name=workflow_definition.get('name', 'CLI Workflow'),
                        steps=workflow_definition.get('steps', []),
                        description=workflow_definition.get('description', ''),
                        user_id="cli_user"
                    )
                    
                    click.echo(f"✅ Created workflow: {workflow_id}")
                else:
                    click.echo("❌ Workflow manager not available")
    
    asyncio.run(_create())

# Utility commands
@cli.group()
def utils():
    """Utility commands"""
    pass

@utils.command()
@click.option('--requests', '-r', default=10, help='Number of requests to send')
@click.option('--concurrency', '-c', default=1, help='Concurrent requests')
@click.pass_context
def benchmark(ctx, requests, concurrency):
    """Benchmark system performance"""
    async def _benchmark():
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                click.echo(f"⚡ Running benchmark: {requests} requests, {concurrency} concurrent")
                
                start_time = time.time()
                successful = 0
                failed = 0
                
                async def make_request(i):
                    try:
                        request = {
                            "action": "generate_post",
                            "topic": f"Benchmark topic {i+1}",
                            "platform": "twitter"
                        }
                        
                        result = await creator_cli.creator_system.generate_content(
                            request, user_id=f"benchmark_user_{i}"
                        )
                        
                        if result.get('content'):
                            return True
                    except Exception:
                        pass
                    return False
                
                # Run benchmark
                import asyncio
                semaphore = asyncio.Semaphore(concurrency)
                
                async def bounded_request(i):
                    async with semaphore:
                        return await make_request(i)
                
                tasks = [bounded_request(i) for i in range(requests)]
                results = await asyncio.gather(*tasks)
                
                successful = sum(1 for r in results if r)
                failed = requests - successful
                
                end_time = time.time()
                total_time = end_time - start_time
                
                click.echo(f"\n📊 Benchmark Results:")
                click.echo(f"  Total Requests: {requests}")
                click.echo(f"  Successful: {successful}")
                click.echo(f"  Failed: {failed}")
                click.echo(f"  Success Rate: {(successful/requests)*100:.1f}%")
                click.echo(f"  Total Time: {total_time:.2f}s")
                click.echo(f"  Requests/Second: {requests/total_time:.2f}")
                click.echo(f"  Average Time/Request: {total_time/requests:.3f}s")
    
    asyncio.run(_benchmark())

@utils.command()
@click.option('--format', '-f', type=click.Choice(['json', 'yaml']), default='yaml')
@click.option('--output', '-o', help='Output file')
def init_config(format, output):
    """Generate initial configuration file"""
    from umbra.modules.creator.config_defaults import *
    
    # Get all configuration variables
    config_vars = {}
    current_module = sys.modules['umbra.modules.creator.config_defaults']
    
    for name in dir(current_module):
        if name.startswith('CREATOR_') and not name.startswith('_'):
            value = getattr(current_module, name)
            config_vars[name] = value
    
    if format == 'json':
        content = json.dumps(config_vars, indent=2, default=str)
        default_filename = 'creator_config.json'
    else:
        content = yaml.dump(config_vars, default_flow_style=False)
        default_filename = 'creator_config.yaml'
    
    output_file = output or default_filename
    
    with open(output_file, 'w') as f:
        f.write(content)
    
    click.echo(f"✅ Configuration template created: {output_file}")

@utils.command()
@click.pass_context
def doctor(ctx):
    """Diagnose system issues"""
    async def _doctor():
        click.echo("🩺 Running Creator v1 diagnostics...")
        
        # Check basic imports
        try:
            from umbra.modules.creator import CreatorV1System
            click.echo("✅ Creator v1 imports working")
        except ImportError as e:
            click.echo(f"❌ Import error: {e}")
            return
        
        # Try to load system
        async with AsyncContext() as creator_cli:
            if await creator_cli.load_system(ctx.obj['config_file'], ctx.obj['debug']):
                click.echo("✅ System initialization successful")
                
                # Check components
                components_to_check = [
                    'analytics', 'cache', 'security', 'health_monitor',
                    'plugin_manager', 'workflow_manager', 'creator_service'
                ]
                
                for component_name in components_to_check:
                    component = creator_cli.creator_system.get_component(component_name)
                    if component:
                        click.echo(f"✅ {component_name} component loaded")
                    else:
                        click.echo(f"❌ {component_name} component missing")
                
                # Test basic functionality
                try:
                    test_request = {
                        "action": "generate_post",
                        "topic": "System test",
                        "platform": "twitter"
                    }
                    
                    result = await creator_cli.creator_system.generate_content(
                        test_request, user_id="doctor_test"
                    )
                    
                    if result.get('content'):
                        click.echo("✅ Content generation test passed")
                    else:
                        click.echo("❌ Content generation test failed")
                
                except Exception as e:
                    click.echo(f"❌ Content generation test error: {e}")
                
                # System health
                try:
                    health = await creator_cli.creator_system.health_check()
                    overall_status = health.get('overall_health', {}).get('status', 'unknown')
                    click.echo(f"✅ System health: {overall_status}")
                except Exception as e:
                    click.echo(f"❌ Health check error: {e}")
            else:
                click.echo("❌ System initialization failed")
        
        click.echo("\n🩺 Diagnosis complete")
    
    asyncio.run(_doctor())

if __name__ == '__main__':
    cli()
