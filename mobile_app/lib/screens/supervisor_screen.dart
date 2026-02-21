import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';

class SupervisorScreen extends StatefulWidget {
  const SupervisorScreen({super.key});

  @override
  State<SupervisorScreen> createState() => _SupervisorScreenState();
}

class _SupervisorScreenState extends State<SupervisorScreen> {
  Map<String, dynamic>? _report;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadStatus();
  }

  Future<void> _loadStatus() async {
    setState(() { _loading = true; _error = null; });
    try {
      final data = await ApiService.getSupervisorStatus();
      setState(() {
        _report = data;
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
            Text('🛡️ ', style: TextStyle(fontSize: 22)),
            Text('Supervisor Agent'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _loadStatus,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
          : _error != null
              ? _buildError()
              : RefreshIndicator(
                  onRefresh: _loadStatus,
                  color: AppTheme.primary,
                  child: _buildContent(),
                ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 50, color: AppTheme.error),
          const SizedBox(height: 16),
          Text('Cannot load supervisor status', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 16),
          FilledButton.icon(onPressed: _loadStatus, icon: const Icon(Icons.refresh), label: const Text('Retry')),
        ],
      ),
    );
  }

  Widget _buildContent() {
    final summary = _report?['summary'] ?? {};
    final platforms = _report?['platforms'] as Map<String, dynamic>? ?? {};

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Summary cards
        Row(
          children: [
            Expanded(child: _summaryCard('Active', '${summary['active_platforms'] ?? 0}', AppTheme.success)),
            const SizedBox(width: 12),
            Expanded(child: _summaryCard('Degraded', '${summary['degraded_platforms'] ?? 0}', AppTheme.warning)),
            const SizedBox(width: 12),
            Expanded(child: _summaryCard('Disabled', '${summary['disabled_platforms'] ?? 0}', AppTheme.error)),
          ],
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [AppTheme.primary.withAlpha(30), AppTheme.primary.withAlpha(10)],
            ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppTheme.primary.withAlpha(50)),
          ),
          child: Row(
            children: [
              const Icon(Icons.search_rounded, color: AppTheme.primary, size: 28),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Total Jobs Discovered', style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                  Text(
                    '${summary['total_jobs_found'] ?? 0}',
                    style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: AppTheme.primary),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),

        // Platform health cards
        Text('Platform Health', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 12),
        ...platforms.entries.map((entry) => _platformCard(entry.key, entry.value)),
      ],
    );
  }

  Widget _summaryCard(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withAlpha(15),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withAlpha(40)),
      ),
      child: Column(
        children: [
          Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
        ],
      ),
    );
  }

  Widget _platformCard(String name, Map<String, dynamic> health) {
    final status = health['status'] ?? 'unknown';
    final color = status == 'active' ? AppTheme.success
        : status == 'degraded' ? AppTheme.warning
        : AppTheme.error;
    final icon = status == 'active' ? Icons.check_circle_rounded
        : status == 'degraded' ? Icons.warning_rounded
        : Icons.cancel_rounded;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.surfaceLighter),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Text(AppTheme.platformIcon(name), style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name[0].toUpperCase() + name.substring(1),
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        Icon(icon, size: 14, color: color),
                        const SizedBox(width: 4),
                        Text(
                          status.toUpperCase(),
                          style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              if (status == 'disabled')
                FilledButton.tonal(
                  onPressed: () async {
                    try {
                      await ApiService.reEnablePlatform(name);
                      _loadStatus();
                    } catch (e) {
                      if (mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.error),
                        );
                      }
                    }
                  },
                  style: FilledButton.styleFrom(
                    backgroundColor: AppTheme.success.withAlpha(30),
                    foregroundColor: AppTheme.success,
                  ),
                  child: const Text('Re-enable', style: TextStyle(fontSize: 12)),
                ),
            ],
          ),
          const SizedBox(height: 12),
          // Stats row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _miniStat('Runs', '${health['total_runs'] ?? 0}'),
              _miniStat('Jobs Found', '${health['total_jobs_found'] ?? 0}'),
              _miniStat('Last Batch', '${health['last_job_count'] ?? 0}'),
              _miniStat('Duration', '${health['last_run_duration'] ?? 0}s'),
            ],
          ),
          if (health['last_error'] != null) ...[
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppTheme.error.withAlpha(10),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                'Error: ${health['last_error']}',
                style: const TextStyle(fontSize: 11, color: AppTheme.error),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _miniStat(String label, String value) {
    return Column(
      children: [
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.textPrimary)),
        Text(label, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
      ],
    );
  }
}
