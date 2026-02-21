import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? _stats;
  List<dynamic>? _recentApps;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() { _loading = true; _error = null; });
    try {
      final stats = await ApiService.getStats();
      final apps = await ApiService.getAllApplications();
      setState(() {
        _stats = stats;
        _recentApps = apps.take(5).toList();
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Text('🤖 ', style: TextStyle(fontSize: 24)),
            Text('Job Agent'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _loadData,
          ),
          IconButton(
            icon: const Icon(Icons.rocket_launch_rounded, color: AppTheme.accent),
            onPressed: () async {
              try {
                await ApiService.triggerScan();
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('🚀 Job scan triggered!'),
                      backgroundColor: AppTheme.success,
                    ),
                  );
                }
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Error: $e'),
                      backgroundColor: AppTheme.error,
                    ),
                  );
                }
              }
            },
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
          : _error != null
              ? _buildError()
              : RefreshIndicator(
                  onRefresh: _loadData,
                  color: AppTheme.primary,
                  child: _buildContent(),
                ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.cloud_off_rounded, size: 64, color: AppTheme.textSecondary),
            const SizedBox(height: 16),
            Text(
              'Cannot connect to server',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              'Make sure your API URL is correct in Settings',
              style: Theme.of(context).textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: _loadData,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContent() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Greeting
        Text(
          'Hi Ajsal 👋',
          style: Theme.of(context).textTheme.headlineLarge,
        ),
        const SizedBox(height: 4),
        Text(
          'Your AI agent is working hard for you',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 24),

        // Stats Grid
        _buildStatsGrid(),
        const SizedBox(height: 24),

        // Pie Chart
        _buildPieChart(),
        const SizedBox(height: 24),

        // Recent Applications
        Text(
          'Recent Applications',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        if (_recentApps != null && _recentApps!.isNotEmpty)
          ..._recentApps!.map((app) => _buildRecentCard(app))
        else
          Container(
            padding: const EdgeInsets.all(32),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Center(
              child: Text(
                'No applications yet.\nTrigger a scan to find jobs! 🚀',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppTheme.textSecondary),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildStatsGrid() {
    final stats = _stats ?? {};
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.5,
      children: [
        _statCard('Applied', '${stats['total_applied'] ?? 0}', Icons.send_rounded, AppTheme.primary),
        _statCard('Interviews', '${stats['interviews'] ?? 0}', Icons.calendar_today_rounded, AppTheme.success),
        _statCard('Offers', '${stats['offers'] ?? 0}', Icons.star_rounded, AppTheme.warning),
        _statCard('Discovered', '${stats['total_discovered'] ?? 0}', Icons.search_rounded, AppTheme.secondary),
      ],
    );
  }

  Widget _statCard(String label, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            color.withAlpha(30),
            color.withAlpha(10),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withAlpha(50)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Icon(icon, color: color, size: 28),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                value,
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              Text(
                label,
                style: const TextStyle(
                  color: AppTheme.textSecondary,
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPieChart() {
    final stats = _stats ?? {};
    final applied = (stats['total_applied'] ?? 0).toDouble();
    final interviews = (stats['interviews'] ?? 0).toDouble();
    final offers = (stats['offers'] ?? 0).toDouble();
    final rejected = (stats['rejected'] ?? 0).toDouble();
    final noResponse = (stats['no_response'] ?? 0).toDouble();

    if (applied + interviews + offers + rejected + noResponse == 0) {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Application Status', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 16),
          SizedBox(
            height: 200,
            child: PieChart(
              PieChartData(
                sectionsSpace: 3,
                centerSpaceRadius: 40,
                sections: [
                  if (applied > 0) PieChartSectionData(value: applied, color: AppTheme.primary, title: '${applied.toInt()}', radius: 50, titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white)),
                  if (interviews > 0) PieChartSectionData(value: interviews, color: AppTheme.success, title: '${interviews.toInt()}', radius: 50, titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white)),
                  if (offers > 0) PieChartSectionData(value: offers, color: AppTheme.warning, title: '${offers.toInt()}', radius: 50, titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white)),
                  if (rejected > 0) PieChartSectionData(value: rejected, color: AppTheme.error, title: '${rejected.toInt()}', radius: 50, titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white)),
                  if (noResponse > 0) PieChartSectionData(value: noResponse, color: AppTheme.textSecondary, title: '${noResponse.toInt()}', radius: 50, titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 16,
            runSpacing: 8,
            children: [
              _legendItem('Applied', AppTheme.primary),
              _legendItem('Interviews', AppTheme.success),
              _legendItem('Offers', AppTheme.warning),
              _legendItem('Rejected', AppTheme.error),
              _legendItem('No Reply', AppTheme.textSecondary),
            ],
          ),
        ],
      ),
    );
  }

  Widget _legendItem(String label, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12, height: 12,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 6),
        Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
      ],
    );
  }

  Widget _buildRecentCard(dynamic app) {
    final statusColor = _statusColor(app['status'] ?? '');
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.surfaceLighter),
      ),
      child: Row(
        children: [
          Container(
            width: 48, height: 48,
            decoration: BoxDecoration(
              color: AppTheme.platformColor(app['platform'] ?? '').withAlpha(30),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: Text(
                AppTheme.platformIcon(app['platform'] ?? ''),
                style: const TextStyle(fontSize: 22),
              ),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  app['role'] ?? 'Unknown Role',
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 15,
                    color: AppTheme.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 3),
                Text(
                  '${app['company'] ?? ''} • ${app['location'] ?? ''}',
                  style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: statusColor.withAlpha(25),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: statusColor.withAlpha(60)),
            ),
            child: Text(
              app['status'] ?? '',
              style: TextStyle(fontSize: 11, color: statusColor, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }

  Color _statusColor(String status) {
    switch (status.toLowerCase()) {
      case 'applied':
        return AppTheme.primary;
      case 'interview':
        return AppTheme.success;
      case 'offer':
        return AppTheme.warning;
      case 'rejected':
        return AppTheme.error;
      default:
        return AppTheme.textSecondary;
    }
  }
}
